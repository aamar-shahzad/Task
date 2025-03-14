import React, { useState, useRef, useEffect } from 'react';
import './ChatInput.css';

function ChatInput({ onSendMessage, disabled }) {
  const [inputText, setInputText] = useState('');
  const textareaRef = useRef(null);
  
  useEffect(() => {
    if (textareaRef.current) {
      // Auto-resize the textarea
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [inputText]);
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputText.trim() && !disabled) {
      onSendMessage(inputText);
      setInputText('');
    }
  };
  
  const handleKeyDown = (e) => {
    // Submit on Enter (but not with Shift+Enter)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };
  
  return (
    <form className="chat-input-container" onSubmit={handleSubmit}>
      <div className="chat-input-box">
        <textarea
          ref={textareaRef}
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your question here..."
          disabled={disabled}
          className="chat-input"
          rows="1"
        />
        <div className="input-buttons">
          <button 
            type="submit" 
            disabled={disabled || !inputText.trim()} 
            className="send-button"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M22 2L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
      </div>
    </form>
  );
}
    
export default ChatInput;