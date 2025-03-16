import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Sidebar from './Sidebar';


describe('Sidebar', () => {
  const mockOnNewChat = jest.fn();
  const mockOnLoadChat = jest.fn();
  const currentSessionId = 'session-123';
  
  const sampleChatHistory = [
    {
      sessionId: 'session-123',
      title: 'First Conversation',
      createdAt: '2025-03-14T10:00:00Z'
    },
    {
      sessionId: 'session-456',
      title: 'Second Conversation',
      createdAt: '2025-03-14T11:30:00Z'
    }
  ];

  it('renders the new chat button', () => {
    render(<Sidebar onNewChat={mockOnNewChat} onLoadChat={mockOnLoadChat} />);
    
    const newChatButton = screen.getByText('New chat');
    expect(newChatButton).toBeInTheDocument();
  });

  it('calls onNewChat when the new chat button is clicked', () => {
    render(<Sidebar onNewChat={mockOnNewChat} onLoadChat={mockOnLoadChat} />);
    
    const newChatButton = screen.getByText('New chat');
    fireEvent.click(newChatButton);
    
    expect(mockOnNewChat).toHaveBeenCalledTimes(1);
  });

  it('displays "No previous chats" when chat history is empty', () => {
    render(
      <Sidebar 
        onNewChat={mockOnNewChat} 
        onLoadChat={mockOnLoadChat}
        chatHistory={[]} 
      />
    );
    
    expect(screen.getByText('No previous chats')).toBeInTheDocument();
  });

  it('renders chat history items when provided', () => {
    render(
      <Sidebar 
        onNewChat={mockOnNewChat} 
        onLoadChat={mockOnLoadChat}
        currentSessionId={currentSessionId}
        chatHistory={sampleChatHistory} 
      />
    );
    
    expect(screen.getByText('First Conversation')).toBeInTheDocument();
    expect(screen.getByText('Second Conversation')).toBeInTheDocument();
    
    // Check for date formatting
    const dateElements = screen.getAllByText('Mar 14, 2025');
    expect(dateElements.length).toBe(2);
  });

  it('calls onLoadChat with the correct sessionId when a chat history item is clicked', () => {
    render(
      <Sidebar 
        onNewChat={mockOnNewChat} 
        onLoadChat={mockOnLoadChat}
        currentSessionId={currentSessionId}
        chatHistory={sampleChatHistory} 
      />
    );
    
    const secondChat = screen.getByText('Second Conversation');
    fireEvent.click(secondChat);
    
    expect(mockOnLoadChat).toHaveBeenCalledWith('session-456');
  });

  it('highlights the current session in the chat history', () => {
    const { container } = render(
      <Sidebar 
        onNewChat={mockOnNewChat} 
        onLoadChat={mockOnLoadChat}
        currentSessionId={currentSessionId}
        chatHistory={sampleChatHistory} 
      />
    );
    
    // Find the first chat list item (which should be highlighted)
    const firstChatItem = screen.getByText('First Conversation').closest('li');
    const secondChatItem = screen.getByText('Second Conversation').closest('li');
    
    expect(firstChatItem).toHaveClass('bg-blue-100');
    expect(firstChatItem).toHaveClass('text-blue-800');
    expect(secondChatItem).not.toHaveClass('bg-blue-100');
  });

  it('renders the footer text correctly', () => {
    render(<Sidebar onNewChat={mockOnNewChat} onLoadChat={mockOnLoadChat} />);
    
    expect(screen.getByText('RAG-Enhanced Q&A System')).toBeInTheDocument();
    expect(screen.getByText('Powered by Employee Data')).toBeInTheDocument();
  });
});
