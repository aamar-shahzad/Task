import React from 'react';
import ReactMarkdown from 'react-markdown';

function ChatMessage({ message }) {
  const { text, sender, timestamp, source, isError } = message;
  
  const formattedTime = new Date(timestamp).toLocaleTimeString([], { 
    hour: '2-digit', 
    minute: '2-digit' 
  });
  
  return (
    <div className={`flex mb-6 ${sender === 'user' ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex max-w-3xl ${sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
        <div className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center mr-2 ${
          sender === 'user' ? 'bg-blue-600 ml-2' : 'bg-gray-700'
        }`}>
          {sender === 'user' ? (
            <svg className="h-5 w-5 text-white" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 11C14.2091 11 16 9.20914 16 7C16 4.79086 14.2091 3 12 3C9.79086 3 8 4.79086 8 7C8 9.20914 9.79086 11 12 11Z" fill="currentColor" />
              <path d="M12 13C7.03 13 3 17.03 3 22H21C21 17.03 16.97 13 12 13Z" fill="currentColor" />
            </svg>
          ) : (
            <svg className="h-5 w-5 text-white" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M20 11C20 15.4183 16.4183 19 12 19C7.58172 19 4 15.4183 4 11C4 6.58172 7.58172 3 12 3C16.4183 3 20 6.58172 20 11Z" fill="currentColor" />
              <path d="M15 9C15 10.6569 13.6569 12 12 12C10.3431 12 9 10.6569 9 9C9 7.34315 10.3431 6 12 6C13.6569 6 15 7.34315 15 9Z" fill="white" />
            </svg>
          )}
        </div>
        
        <div className={`rounded-lg ${
          isError ? 'bg-red-50 border border-red-200' : 
          sender === 'user' ? 'bg-blue-50 border border-blue-200' : 'bg-white border border-gray-200'
        } overflow-hidden shadow-sm`}>
          <div className="px-4 py-2 border-b border-gray-100 flex justify-between items-center">
            <div className={`font-medium text-sm ${
              isError ? 'text-red-700' : sender === 'user' ? 'text-blue-700' : 'text-gray-700'
            }`}>
              {sender === 'user' ? 'You' : 'Assistant'}
            </div>
            <div className="text-xs text-gray-500">{formattedTime}</div>
          </div>
          
          <div className="px-4 py-3">
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown>{text}</ReactMarkdown>
              {source && source !== 'unknown' && (
                <div className="mt-2 text-xs text-gray-500 italic">
                  Source: {source}
                </div>
              )}
            </div>
          </div>
       
        </div>
      </div>
    </div>
  );
}

export default ChatMessage;