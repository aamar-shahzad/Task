import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from './App';
import { v4 as uuidv4 } from 'uuid';

// Mock uuid
jest.mock('uuid', () => ({
  v4: jest.fn()
}));

// Mock fetch
global.fetch = jest.fn();

// Mock localStorage
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: jest.fn(key => store[key] || null),
    setItem: jest.fn((key, value) => {
      store[key] = value.toString();
    }),
    removeItem: jest.fn(key => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
    getAllKeys: jest.fn(() => Object.keys(store))
  };
})();

Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('App Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.clear();
    uuidv4.mockReturnValue('test-uuid-1234');
    window.HTMLElement.prototype.scrollIntoView = jest.fn();
    
    global.fetch = jest.fn().mockImplementation((url) => {
      console.log(`Mocking fetch for URL: ${url}`);
      
      // Session initialization
      if (url === 'http://localhost:3001/sessions/init') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ sessionId: 'server-session-id' })
        });
      } 
      // Get session history
      else if (url === 'http://localhost:3001/sessions/history') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            history: [
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
            ]
          })
        });
      } 
      // Create new session
      else if (url === 'http://localhost:3001/sessions/create') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ sessionId: 'new-session-id' })
        });
      } 
      // Query endpoint
      else if (url === 'http://localhost:3001/query') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ answer: 'Assistant response', source: 'system' })
        });
      } 
      // Specific session endpoints
      else if (url === 'http://localhost:3001/sessions/previous-session-id') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            messages: [
              { text: 'Loaded message', sender: 'user', timestamp: '2023-01-01T00:00:00.000Z' },
              { text: 'Loaded response', sender: 'assistant', timestamp: '2023-01-01T00:00:01.000Z' }
            ]
          })
        });
      } 
      else if (url === 'http://localhost:3001/sessions/saved-session-id') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            messages: [
              { text: 'Saved message', sender: 'user', timestamp: '2023-01-01T00:00:00.000Z' },
              { text: 'Saved response', sender: 'assistant', timestamp: '2023-01-01T00:00:01.000Z' }
            ]
          })
        });
      }
      else if (url === 'http://localhost:3001/sessions/existing-session-id') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            messages: [
              { text: 'Existing message', sender: 'user', timestamp: '2023-01-01T00:00:00.000Z' },
              { text: 'Existing response', sender: 'assistant', timestamp: '2023-01-01T00:00:01.000Z' }
            ]
          })
        });
      }
      else if (url === 'http://localhost:3001/sessions/session-123') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            messages: [
              { text: 'First conversation message', sender: 'user', timestamp: '2023-01-01T00:00:00.000Z' },
              { text: 'First conversation response', sender: 'assistant', timestamp: '2023-01-01T00:00:01.000Z' }
            ]
          })
        });
      } 
      else if (url === 'http://localhost:3001/sessions/session-456') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            messages: [
              { text: 'Second conversation message', sender: 'user', timestamp: '2023-01-01T00:00:00.000Z' },
              { text: 'Second conversation response', sender: 'assistant', timestamp: '2023-01-01T00:00:01.000Z' }
            ]
          })
        });
      }
      else if (url === 'http://localhost:3001/sessions/server-session-id') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            messages: []
          })
        });
      }
      else if (url === 'http://localhost:3001/sessions/new-session-id') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            messages: []
          })
        });
      }
      // Generic catch-all for session URLs that aren't explicitly handled
      else if (url.includes('http://localhost:3001/sessions/')) {
        const sessionId = url.split('/').pop();
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            messages: [
              { text: `${sessionId} message`, sender: 'user', timestamp: '2023-01-01T00:00:00.000Z' },
              { text: `${sessionId} response`, sender: 'assistant', timestamp: '2023-01-01T00:00:01.000Z' }
            ]
          })
        });
      }
      
      // Return a default response for any unhandled URLs
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({})
      });
    });
  });
  test('renders welcome screen on initial load', async () => {
    await act(async () => {
      render(<App />);
    });
    
    expect(screen.getByText('Employee Data Assistant')).toBeInTheDocument();
    expect(screen.getByText('Ask questions about employee data or any general topic')).toBeInTheDocument();
    
    // Check if quick questions are displayed
    expect(screen.getByText('What is the median salary in the IT department?')).toBeInTheDocument();
  });

  test('initializes new session when no saved session exists', async () => {
    await act(async () => {
      render(<App />);
    });

    expect(fetch).toHaveBeenCalledWith('http://localhost:3001/sessions/init', expect.any(Object));
    expect(fetch).toHaveBeenCalledWith('http://localhost:3001/sessions/history', expect.any(Object));
    expect(localStorageMock.setItem).toHaveBeenCalledWith('currentSessionId', 'server-session-id');
  });

  test('loads saved session when one exists', async () => {
    localStorageMock.getItem.mockImplementation((key) => {
      if (key === 'currentSessionId') return 'saved-session-id';
      if (key === 'chat_saved-session-id') {
        return JSON.stringify([
          { text: 'Saved message', sender: 'user', timestamp: '2023-01-01T00:00:00.000Z' },
          { text: 'Saved response', sender: 'assistant', timestamp: '2023-01-01T00:00:01.000Z' }
        ]);
      }
      return null;
    });

    await act(async () => {
      render(<App />);
    });

    expect(localStorageMock.getItem).toHaveBeenCalledWith('currentSessionId');
    expect(localStorageMock.getItem).toHaveBeenCalledWith('chat_saved-session-id');
    
    // Messages should be loaded from localStorage
    await waitFor(() => {
      expect(screen.getByText('Saved message')).toBeInTheDocument();
      expect(screen.getByText('Saved response')).toBeInTheDocument();
    });
  });
  test('handles error when initializing session', async () => {
    // Set up a new fetch mock just for this test
    global.fetch = jest.fn()
      .mockImplementationOnce(() => {
        // First call fails (sessions/init)
        return Promise.resolve({
          ok: false,
          status: 500,
          statusText: 'Internal Server Error'
        });
      })
      .mockImplementation((url) => {
        // All subsequent calls succeed with empty responses
        console.log(`Fallback mock for URL: ${url}`);
        if (url.includes('/sessions/history')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ history: [] })
          });
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({})
        });
      });
  
    await act(async () => {
      render(<App />);
    });
  
    // Check that a new UUID is generated as fallback
    expect(uuidv4).toHaveBeenCalled();
    expect(localStorageMock.setItem).toHaveBeenCalledWith('currentSessionId', 'test-uuid-1234');
  });
  test('handles sending and receiving messages', async () => {
    await act(async () => {
      render(<App />);
    });

    // Get the input field and send button
    const inputField = screen.getByRole('textbox');
    const sendButton = screen.getByRole('button', { name: /send/i });

    // Type a message and send it
    await act(async () => {
      fireEvent.change(inputField, { target: { value: 'Hello assistant' } });
      fireEvent.click(sendButton);
    });

    // Check that the message was sent and the response received
    await waitFor(() => {
      expect(screen.getByText('Hello assistant')).toBeInTheDocument();
      expect(screen.getByText('Assistant response')).toBeInTheDocument();
    });

    // Check that the message was saved to localStorage
    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      expect.stringContaining('chat_'),
      expect.stringContaining('Hello assistant')
    );
  });

  test('handles quick question selection', async () => {
    await act(async () => {
      render(<App />);
    });

    const quickQuestion = screen.getByText('What is RAG in the context of AI?');
    
    await act(async () => {
      fireEvent.click(quickQuestion);
    });

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('http://localhost:3001/query', expect.objectContaining({
        method: 'POST',
        body: expect.stringContaining('What is RAG in the context of AI?')
      }));
      expect(screen.getByText('What is RAG in the context of AI?')).toBeInTheDocument();
      expect(screen.getByText('Assistant response')).toBeInTheDocument();
    });
  });

  test('handles sidebar toggle', async () => {
    await act(async () => {
      render(<App />);
    });

    // The sidebar should be visible initially
    expect(screen.getByText(/new chat/i)).toBeInTheDocument();
    
    // Find and click the toggle button
    const toggleButton = screen.getByLabelText('Hide sidebar');
    
    await act(async () => {
      fireEvent.click(toggleButton);
    });
    
    // After a short delay to simulate animation, the sidebar should be hidden
    await waitFor(() => {
      expect(screen.queryByText(/new chat/i)).not.toBeInTheDocument();
    });
  });

  test('handles clearing chat and creating new session', async () => {
    // Setup with existing messages
    localStorageMock.getItem.mockImplementation((key) => {
      if (key === 'currentSessionId') return 'existing-session-id';
      if (key === 'chat_existing-session-id') {
        return JSON.stringify([
          { text: 'Existing message', sender: 'user', timestamp: '2023-01-01T00:00:00.000Z' },
          { text: 'Existing response', sender: 'assistant', timestamp: '2023-01-01T00:00:01.000Z' }
        ]);
      }
      return null;
    });

    await act(async () => {
      render(<App />);
    });

    // Verify messages are loaded
    expect(screen.getByText('Existing message')).toBeInTheDocument();
    
    // Find and click the "New Chat" button
    
    const newChatButton = screen.getByText(/new chat/i); // Case insensitive match

    
    await act(async () => {
      fireEvent.click(newChatButton);
    });
    
    // Verify that a new session is created and messages are cleared
    expect(fetch).toHaveBeenCalledWith('http://localhost:3001/sessions/create', expect.any(Object));
    
    await waitFor(() => {
      expect(screen.queryByText('Existing message')).not.toBeInTheDocument();
      expect(screen.getByText('Employee Data Assistant')).toBeInTheDocument();
    });
    
    // Verify localStorage is updated
    expect(localStorageMock.setItem).toHaveBeenCalledWith('currentSessionId', 'new-session-id');
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('chat_existing-session-id');
  });
  test('handles loading a chat session', async () => {
    await act(async () => {
      render(<App />);
    });
    
    // Mock the chat history item in the sidebar
    const chatHistoryItem = screen.getByText('First Conversation');
    
    await act(async () => {
      fireEvent.click(chatHistoryItem);
    });
    
    // Update this to match the actual session ID that's being used
    expect(fetch).toHaveBeenCalledWith('http://localhost:3001/sessions/session-123', expect.any(Object));
    
    await waitFor(() => {
      expect(localStorageMock.setItem).toHaveBeenCalledWith('currentSessionId', 'session-123');
    });
  });

  test('handles error when sending message', async () => {
    // Mock a failed response
    global.fetch.mockImplementationOnce((url) => {
      if (url === 'http://localhost:3001/sessions/init') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ sessionId: 'server-session-id' })
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ history: [] })
      });
    }).mockImplementationOnce((url) => {
      if (url === 'http://localhost:3001/query') {
        return Promise.resolve({
          ok: false,
          status: 500,
          statusText: 'Internal Server Error'
        });
      }
      return Promise.reject(new Error('Not mocked'));
    });

    await act(async () => {
      render(<App />);
    });

    const inputField = screen.getByRole('textbox');
    const sendButton = screen.getByLabelText('Send');

    // Type a message and send it
    await act(async () => {
      fireEvent.change(inputField, { target: { value: 'This will cause an error' } });
      fireEvent.click(sendButton);
    });

   
  });


});