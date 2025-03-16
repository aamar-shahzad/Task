import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ChatInput from './ChatInput';

describe('ChatInput', () => {
  it('renders the ChatInput component', () => {
    render(<ChatInput onSendMessage={() => {}} disabled={false} />);
    expect(screen.getByPlaceholderText('Type your question here...')).toBeInTheDocument();
  });

  it('should resize textarea based on input text', () => {
    const { getByPlaceholderText } = render(<ChatInput onSendMessage={() => {}} disabled={false} />);
    const textarea = getByPlaceholderText('Type your question here...');

    // Set the scrollHeight property to simulate the textarea growing
    Object.defineProperty(textarea, 'scrollHeight', {
      value: 250, // Simulate the height you want
      writable: true,
    });

    // Trigger input change to resize the textarea
    fireEvent.change(textarea, { target: { value: 'Some text' } });

    // Ensure that the height gets resized
    expect(textarea.style.height).toBe('200px'); // Should match the max height of 200px
  });

  it('should call onSendMessage when Enter is pressed (without Shift)', () => {
    const mockOnSendMessage = jest.fn();
    const { getByPlaceholderText } = render(
      <ChatInput onSendMessage={mockOnSendMessage} disabled={false} />
    );
    const textarea = getByPlaceholderText('Type your question here...');
    
    fireEvent.change(textarea, { target: { value: 'Hello' } });
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false });
    
    expect(mockOnSendMessage).toHaveBeenCalledWith('Hello');
  });

  it('should not call onSendMessage when Enter is pressed with Shift key', () => {
    const mockOnSendMessage = jest.fn();
    const { getByPlaceholderText } = render(
      <ChatInput onSendMessage={mockOnSendMessage} disabled={false} />
    );
    const textarea = getByPlaceholderText('Type your question here...');
    
    fireEvent.change(textarea, { target: { value: 'Hello' } });
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true });
    
    expect(mockOnSendMessage).not.toHaveBeenCalled();
  });

  it('should disable the Send button when input is empty', () => {
    const { getByRole } = render(<ChatInput onSendMessage={() => {}} disabled={false} />);
    const sendButton = getByRole('button'); // Finds the button by role
    expect(sendButton).toBeDisabled();
  });
  
  it('should disable the Send button when disabled prop is true', () => {
    const { getByRole } = render(<ChatInput onSendMessage={() => {}} disabled={true} />);
    const sendButton = getByRole('button'); // Finds the button by role
    expect(sendButton).toBeDisabled();
  });
  
  it('should clear input after sending a message', () => {
    const mockOnSendMessage = jest.fn();
    const { getByPlaceholderText } = render(
      <ChatInput onSendMessage={mockOnSendMessage} disabled={false} />
    );
    const textarea = getByPlaceholderText('Type your question here...');
    
    fireEvent.change(textarea, { target: { value: 'Hello' } });
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false });
    
    expect(mockOnSendMessage).toHaveBeenCalledWith('Hello');
    expect(textarea.value).toBe(''); // Input should be cleared after sending
  });
});
