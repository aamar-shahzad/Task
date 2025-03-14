import React from 'react';

function Sidebar({ onNewChat, onLoadChat, currentSessionId, chatHistory }) {
  // Generate a title based on the first message of a chat
  const getChatTitle = (chat) => {
    if (chat.messages && chat.messages.length > 0) {
      // Use the first user message as the title, limited to 30 characters
      const firstUserMessage = chat.messages.find(msg => msg.sender === 'user');
      console.log(firstUserMessage,"firstUserMessage");
      if (firstUserMessage) {
        return firstUserMessage.text.length > 30 
          ? firstUserMessage.text.substring(0, 30) + '...' 
          : firstUserMessage.text;
      }
    }
    return `Chat ${new Date(chat.createdAt).toLocaleDateString()}`;
  };
  console.log(chatHistory,"chatHistory");

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <button className="new-chat-button" onClick={onNewChat}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 5V19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M5 12H19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          New chat
        </button>
      </div>
      
  
      <div className="chat-history">
        <h3>Recent Conversations</h3>
        
        {chatHistory && chatHistory.length > 0 ? (
          <ul className="chat-list">
            {chatHistory.map(chat => {
              const title = getChatTitle(chat);
              
              return (
                <li 
                  key={chat.sessionId} 
                  className={`chat-item ${chat.sessionId === currentSessionId ? 'active' : ''}`}
                  onClick={() => onLoadChat(chat.sessionId)}
                >
                  <div className="chat-item-title">{title}</div>
                  <div className="chat-item-date">
                    {new Date(chat.createdAt).toLocaleDateString()}
                  </div>
                </li>
              );
            })}
          </ul>
        ) : (
          <div className="no-history">No previous chats</div>
        )}
      </div>
      
      <div className="sidebar-footer">
        <div>RAG-Enhanced Q&A System</div>
        <div>Powered by Employee Data</div>
      </div>
    </div>
  );
}

export default Sidebar;