import React from 'react';
import { render, screen } from '@testing-library/react';
import ChatMessage from './ChatMessage'; 


describe('ChatMessage', () => {
  it('renders the message with the correct sender and content', () => {
    const message = {
      text: 'Hello, how can I help you?',
      sender: 'assistant',
      timestamp: '2025-03-14T12:00:00Z',
      source: 'Chatbot',
      isError: false,
    };

    render(<ChatMessage message={message} />);

    // Check sender name
    expect(screen.getByText('Assistant')).toBeInTheDocument();

    // Check message text
    expect(screen.getByText('Hello, how can I help you?')).toBeInTheDocument();

    // Check the source
    expect(screen.getByText('Source: Chatbot')).toBeInTheDocument();

    // Check the time format
    expect(screen.getByText('08:00 AM')).toBeInTheDocument();
  });

 


  it('does not show the source when it is "unknown"', () => {
    const message = {
      text: 'No source available',
      sender: 'assistant',
      timestamp: '2025-03-14T16:45:00Z',
      source: 'unknown',
      isError: false,
    };

    render(<ChatMessage message={message} />);

    // Check if source is not displayed
    expect(screen.queryByText('Source: unknown')).not.toBeInTheDocument();
  });

  it('renders the message without source information when source is undefined', () => {
    const message = {
      text: 'Just a regular message',
      sender: 'user',
      timestamp: '2025-03-14T18:00:00Z',
      source: undefined,
      isError: false,
    };

    render(<ChatMessage message={message} />);

    // Check that source is not displayed
    expect(screen.queryByText('Source:')).not.toBeInTheDocument();
  });
  
});
