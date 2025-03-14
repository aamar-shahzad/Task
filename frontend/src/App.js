import React, { useState, useRef, useEffect } from 'react';
import ChatMessage from './components/ChatMessage';
import ChatInput from './components/ChatInput';
import Sidebar from './components/Sidebar';
import { v4 as uuidv4 } from 'uuid';

function App() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [sessionId, setSessionId] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const messagesEndRef = useRef(null);
  const [isToggling, setIsToggling] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [isFirstVisit, setIsFirstVisit] = useState(false);

  useEffect(() => {
    initializeSession();
  }, []);

  useEffect(() => {
    if (messages.length > 0 && sessionId) {
      localStorage.setItem(`chat_${sessionId}`, JSON.stringify(messages));
    }
    scrollToBottom();
  }, [messages, sessionId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const initializeSession = async () => {
    setIsLoadingHistory(true);
    try {
      const savedSessionId = localStorage.getItem('currentSessionId');
      const savedMessages = savedSessionId ? JSON.parse(localStorage.getItem(`chat_${savedSessionId}`) || '[]') : [];

      if (savedSessionId) {
        setSessionId(savedSessionId);
        setMessages(savedMessages);
        setIsFirstVisit(false);
      } else {
        setIsFirstVisit(true);
        const response = await fetch('http://localhost:3001/sessions/init', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          }
        });

        if (!response.ok) {
          throw new Error('Failed to initialize session');
        }

        const data = await response.json();
        setSessionId(data.sessionId);
        localStorage.setItem('currentSessionId', data.sessionId);
      }

      await loadChatHistory();
    } catch (error) {
      console.error('Error initializing session:', error);
      const newSessionId = uuidv4();
      setSessionId(newSessionId);
      localStorage.setItem('currentSessionId', newSessionId);
    } finally {
      setIsLoadingHistory(false);
    }
  };


  const loadChatHistory = async () => {
    try {
      const response = await fetch('http://localhost:3001/sessions/history', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load chat history');
      }

      const data = await response.json();
      const mergedHistory = [...(data.history || [])];
      setChatHistory(mergedHistory);

      if (sessionId && !mergedHistory.some(chat => chat.sessionId === sessionId)) {
        const localMessages = JSON.parse(localStorage.getItem(`chat_${sessionId}`) || '[]');
        if (localMessages.length > 0) {
          const localSession = {
            sessionId,
            messages: localMessages,
            createdAt: localMessages[0]?.timestamp || new Date().toISOString()
          };
          setChatHistory(prev => [...prev, localSession]);
        }
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
      const localSessions = Object.keys(localStorage)
        .filter(key => key.startsWith('chat_'))
        .map(key => {
          const sessionId = key.replace('chat_', '');
          const messages = JSON.parse(localStorage.getItem(key) || '[]');
          return {
            sessionId,
            messages,
            createdAt: messages[0]?.timestamp || new Date().toISOString()
          };
        });
      setChatHistory(localSessions);
    }
  };

  const handleSendMessage = async (text) => {
    if (!text.trim()) return;
    
    // Add user message to chat
    const userMessage = {
      text,
      sender: 'user',
      timestamp: new Date().toISOString()
    };
    
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setLoading(true);
    
    try {
      // Send message to backend - the backend will save this to history
      const response = await fetch('http://localhost:3001/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          query: text, 
          session_id: sessionId 
        }),
      });
      
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      
      const data = await response.json();
      
      // Add assistant response to chat
      const assistantMessage = {
        text: data.answer,
        sender: 'assistant',
        timestamp: new Date().toISOString(),
        source: data.source || 'unknown'
      };
      
      const updatedMessages = [...messages, userMessage, assistantMessage];
      setMessages(updatedMessages);
      
      // Save to local storage
      localStorage.setItem(`chat_${sessionId}`, JSON.stringify(updatedMessages));
      
      // If this is a new session that wasn't previously in history, refresh history
      if (isFirstVisit && messages.length <= 1) {
        setIsFirstVisit(false);
        await loadChatHistory();
      }
    } catch (error) {
      console.error('Error:', error);
      
      // Add error message
      const errorMessage = {
        text: 'Sorry, there was an error processing your request. Please try again.',
        sender: 'assistant',
        timestamp: new Date().toISOString(),
        isError: true
      };
      
      setMessages(prevMessages => [...prevMessages, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = async () => {
    try {
      // Create a new session on the backend
      const response = await fetch('http://localhost:3001/sessions/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to create new session');
      }
      
      const data = await response.json();
      
      // Update local storage with new session ID
      localStorage.setItem('currentSessionId', data.sessionId);
      localStorage.removeItem(`chat_${sessionId}`); // Clean up old session data
      
      setSessionId(data.sessionId);
      setMessages([]);
      setIsFirstVisit(true);
      
      // Refresh history
      await loadChatHistory();
    } catch (error) {
      console.error('Error creating new chat:', error);
      // Fallback to just clearing messages
      const newSessionId = uuidv4();
      localStorage.setItem('currentSessionId', newSessionId);
      localStorage.removeItem(`chat_${sessionId}`); // Clean up old session data
      
      setSessionId(newSessionId);
      setMessages([]);
    }
  };

  const loadChat = async (id) => {
    try {
      // First check if we have this chat in local storage
      const localMessages = JSON.parse(localStorage.getItem(`chat_${id}`) || '[]');
      
      if (localMessages.length > 0) {
        setSessionId(id);
        setMessages(localMessages);
        localStorage.setItem('currentSessionId', id);
        return;
      }
      
      // If not in local storage, try loading from the backend
      const response = await fetch(`http://localhost:3001/sessions/${id}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to load chat');
      }
      
      const data = await response.json();
      setSessionId(id);
      setMessages(data.messages || []);
      
      // Save to local storage
      localStorage.setItem('currentSessionId', id);
      localStorage.setItem(`chat_${id}`, JSON.stringify(data.messages || []));
    } catch (error) {
      console.error('Error loading chat:', error);
      // Try to find it in local history as fallback
      const chat = chatHistory.find(chat => chat.sessionId === id);
      if (chat && chat.messages) {
        setSessionId(id);
        setMessages(chat.messages);
        localStorage.setItem('currentSessionId', id);
        localStorage.setItem(`chat_${id}`, JSON.stringify(chat.messages));
      }
    }
  };

  const handleQuickQuestion = (question) => {
    handleSendMessage(question);
  };

  const toggleSidebar = () => {
    setIsToggling(true);
    setShowSidebar(!showSidebar);
    
    // Reset the toggling state after animation completes
    setTimeout(() => {
      setIsToggling(false);
    }, 300);
  };

  const getChatTitle = (chat) => {
    if (chat.messages && chat.messages.length > 0) {
      const firstUserMessage = chat.messages.find(msg => msg.sender === 'user');
      if (firstUserMessage) {
        return firstUserMessage.text.length > 30 
          ? firstUserMessage.text.substring(0, 30) + '...' 
          : firstUserMessage.text;
      }
    }
    return `Chat ${new Date(chat.createdAt).toLocaleDateString()}`;
  };

  return (
    <div className="flex h-screen bg-gray-100">
      <div className="flex flex-1 overflow-hidden">
        {showSidebar && (
          <div className={`w-64 bg-white shadow-md transition-all duration-300 ${isToggling ? 'animate-slide' : ''}`}>
            <Sidebar 
              onNewChat={clearChat} 
              onLoadChat={loadChat}
              currentSessionId={sessionId}
              chatHistory={chatHistory}
              isLoading={isLoadingHistory}
              getChatTitle={getChatTitle}
            />
          </div>
        )}
        
        <div className="flex flex-col flex-1 overflow-hidden">
          <button 
            className={`absolute top-4 ${showSidebar ? 'left-64' : 'left-4'} z-10 p-2 bg-white rounded-full shadow-md transition-all duration-300 hover:bg-gray-100`}
            onClick={toggleSidebar}
            aria-label={showSidebar ? "Hide sidebar" : "Show sidebar"}
          >
            {showSidebar ? (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M15 6L9 12L15 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            ) : (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M9 6L15 12L9 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            )}
          </button>
          
          <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
            {isLoadingHistory ? (
              <div className="flex items-center justify-center h-full text-gray-500">Loading chats...</div>
            ) : messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center px-4">
                <h2 className="text-2xl font-bold mb-4 text-gray-800">Employee Data Assistant</h2>
                <p className="text-gray-600 mb-6">Ask questions about employee data or any general topic</p>
                <ul className="space-y-3 w-full max-w-md">
                  {[
                    "What is the median salary in the IT department?",
                    "Which department has the highest-paid employee?",
                    "How many employees are in the Finance department?",
                    "What is RAG in the context of AI?"
                  ].map((question, idx) => (
                    <li 
                      key={idx} 
                      onClick={() => handleQuickQuestion(question)}
                      className="p-3 bg-white rounded-lg shadow-sm border border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      {question}
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((message, index) => (
                  <ChatMessage key={index} message={message} />
                ))}
                {loading && (
                  <div className="flex space-x-2 p-4 items-center">
                    <div className="w-3 h-3 bg-gray-300 rounded-full animate-bounce"></div>
                    <div className="w-3 h-3 bg-gray-300 rounded-full animate-bounce delay-100"></div>
                    <div className="w-3 h-3 bg-gray-300 rounded-full animate-bounce delay-200"></div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
          
          <div className="border-t border-gray-200 bg-white p-4">
            <ChatInput onSendMessage={handleSendMessage} disabled={loading} />
            <div className="text-xs text-gray-500 mt-2 text-center">
              Our AI assistant provides information based on employee data. Use responsibly.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;