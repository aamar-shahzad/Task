import React from 'react';

function Sidebar({ onNewChat, onLoadChat, currentSessionId, chatHistory }) {
  // Generate a title based on the first message of a chat
  const getChatTitle = (chat) => {
    if (chat.messages && chat.messages.length > 0) {
      // Use the first user message as the title, limited to 30 characters
      const firstUserMessage = chat.messages.find(msg => msg.sender === 'user');
      console.log(firstUserMessage, "firstUserMessage");
      if (firstUserMessage) {
        return firstUserMessage.text.length > 30 
          ? firstUserMessage.text.substring(0, 30) + '...' 
          : firstUserMessage.text;
      }
    }
    return `Chat ${new Date(chat.createdAt).toLocaleDateString()}`;
  };
  console.log(chatHistory, "chatHistory");

  return (
    <div className="flex flex-col h-full bg-gray-50 border-r border-gray-200">
      <div className="p-4 border-b border-gray-200">
        <button 
          className="flex items-center justify-center w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors duration-200 font-medium"
          onClick={onNewChat}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="mr-2">
            <path d="M12 5V19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M5 12H19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          New chat
        </button>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4">
        <h3 className="text-sm font-semibold text-gray-500 uppercase mb-3">Recent Conversations</h3>
        
        {chatHistory && chatHistory.length > 0 ? (
          <ul className="space-y-2">
            {chatHistory.map(chat => {
              const title = getChatTitle(chat);
              
              return (
                <li 
                  key={chat.sessionId} 
                  className={`p-3 rounded-md cursor-pointer transition-colors duration-200 ${
                    chat.sessionId === currentSessionId 
                      ? 'bg-blue-100 text-blue-800' 
                      : 'hover:bg-gray-200'
                  }`}
                  onClick={() => onLoadChat(chat.sessionId)}
                >
                  <div className="text-sm font-medium truncate">{title}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {new Date(chat.createdAt).toLocaleDateString()}
                  </div>
                </li>
              );
            })}
          </ul>
        ) : (
          <div className="text-sm text-gray-500 text-center py-6">No previous chats</div>
        )}
      </div>
      
      <div className="p-4 border-t border-gray-200 text-xs text-gray-500">
        <div className="font-medium">RAG-Enhanced Q&A System</div>
        <div className="mt-1">Powered by Employee Data</div>
      </div>
    </div>
  );
}

export default Sidebar;