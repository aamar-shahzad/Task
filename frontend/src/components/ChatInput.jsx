import React, { useState, useRef, useEffect } from 'react';

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
    <form className="w-full" onSubmit={handleSubmit}>
      <div className="relative flex items-center bg-white rounded-lg border border-gray-300 focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500">
        <textarea
          ref={textareaRef}
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your question here..."
          disabled={disabled}
          className="w-full py-3 px-4 bg-transparent outline-none resize-none max-h-40"
          rows="1"
        />
        <div className="flex-shrink-0 pr-2">
          <button 
            type="submit" 
            aria-label="Send"
            disabled={disabled || !inputText.trim()} 
            className={`p-2 rounded-full ${
              disabled || !inputText.trim() 
                ? 'text-gray-400 bg-gray-100 cursor-not-allowed' 
                : 'text-white bg-blue-600 hover:bg-blue-700 transition-colors duration-200'
            }`}
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