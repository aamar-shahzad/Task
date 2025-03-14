import React, { useState, useRef, useEffect } from 'react';
import './App.css';
import ChatMessage from './components/ChatMessage';
import ChatInput from './components/ChatInput';
import Sidebar from './components/Sidebar';
import { v4 as uuidv4 } from 'uuid'; // Import UUID library

function App() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [sessionId, setSessionId] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const messagesEndRef = useRef(null);
  const [isToggling, setIsToggling] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);

  // Initialize session and load chat history on component mount
  useEffect(() => {
    initializeSession();
  }, []);

  // Save messages to history when they change
  useEffect(() => {
    if (messages.length > 0 && sessionId) {
      // No need to explicitly save - backend will handle this with each message
      // We just need to update our local state
    }
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const initializeSession = async () => {
    setIsLoadingHistory(true);
    try {
      // Get a session ID from the backend or create a new one
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
      
      // Now load chat history
      await loadChatHistory();
    } catch (error) {
      console.error('Error initializing session:', error);
      // Fallback to local UUID if server fails
      setSessionId(uuidv4());
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
      setChatHistory(data.history || []);
    } catch (error) {
      console.error('Error loading chat history:', error);
      setChatHistory([]);
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
      
      setMessages(prevMessages => [...prevMessages, assistantMessage]);
      
      // Optionally refresh history if this is a new chat
      if (messages.length <= 1) {
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
      setSessionId(data.sessionId);
      setMessages([]);
      
      // Refresh history
      await loadChatHistory();
    } catch (error) {
      console.error('Error creating new chat:', error);
      // Fallback to just clearing messages
      setMessages([]);
      setSessionId(uuidv4());
    }
  };

  const loadChat = async (id) => {
    try {
      // Load a specific chat from the backend
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
    } catch (error) {
      console.error('Error loading chat:', error);
      // Try to find it in local state as fallback
      const chat = chatHistory.find(chat => chat.sessionId === id);
      if (chat && chat.messages) {
        setSessionId(id);
        setMessages(chat.messages);
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

  return (
    <div className="app-container">
      <div className="main-content">
        {showSidebar && (
          <Sidebar 
            onNewChat={clearChat} 
            onLoadChat={loadChat}
            currentSessionId={sessionId}
            chatHistory={chatHistory}
            isLoading={isLoadingHistory}
          />
        )}
        
        <div className="chat-container">
        <button 
          className={`toggle-sidebar-btn ${isToggling ? 'toggling' : ''}`} 
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
          
          <div className="messages-container">
            {isLoadingHistory ? (
              <div className="loading-history">Loading chats...</div>
            ) : messages.length === 0 ? (
              <div className="welcome-message">
                <h2>Employee Data Assistant</h2>
                <p>Ask questions about employee data or any general topic</p>
                <ul>
                  <li onClick={() => handleQuickQuestion("What is the median salary in the IT department?")}>
                    What is the median salary in the IT department?
                  </li>
                  <li onClick={() => handleQuickQuestion("Which department has the highest-paid employee?")}>
                    Which department has the highest-paid employee?
                  </li>
                  <li onClick={() => handleQuickQuestion("How many employees are in the Finance department?")}>
                    How many employees are in the Finance department?
                  </li>
                  <li onClick={() => handleQuickQuestion("What is RAG in the context of AI?")}>
                    What is RAG in the context of AI?
                  </li>
                </ul>
              </div>
            ) : (
              <div className="messages-list">
                {messages.map((message, index) => (
                  <ChatMessage key={index} message={message} />
                ))}
                {loading && (
                  <div className="loading-indicator">
                    <div className="loading-bubble"></div>
                    <div className="loading-bubble"></div>
                    <div className="loading-bubble"></div>
                  </div>
                )}
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          
          <div className="input-footer">
            <ChatInput onSendMessage={handleSendMessage} disabled={loading} />
            <div className="input-footer-text">
              Our AI assistant provides information based on employee data. Use responsibly.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;