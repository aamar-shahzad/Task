from fastapi.testclient import TestClient
from app.main import app
from app.services.conversation_service import ConversationManager, conversation_store
import uuid

# Initialize TestClient
client = TestClient(app)

def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "message": "Excel Query API (with Gemini) is running!",
        "timestamp": response.json()["timestamp"]
    }

def test_create_session():
    """Test the session creation endpoint."""
    response = client.post("/sessions/init")
    assert response.status_code == 200
    session_data = response.json()
    assert "sessionId" in session_data

    # Check if session is properly created in conversation store
    session_id = session_data["sessionId"]
    assert session_id in conversation_store

def test_get_session_history():
    """Test retrieving session history."""
    # Manually create a session for testing
    session_id = str(uuid.uuid4())
    conversation_manager = ConversationManager(session_id)
    conversation_manager.add_message("Test message", "Test response")

    # Ensure session is in conversation store
    conversation_store[session_id] = conversation_manager.get_metadata()

    response = client.get("/sessions/history")
    assert response.status_code == 200
    history = response.json()["history"]
    
    # Ensure the created session is in the history
    assert len(history) > 0
    assert history[0]["sessionId"] == session_id

def test_delete_session():
    """Test deleting a session."""
    # Manually create a session for testing
    session_id = str(uuid.uuid4())
    conversation_manager = ConversationManager(session_id)
    conversation_manager.add_message("Test message", "Test response")

    # Add the session to conversation store
    conversation_store[session_id] = conversation_manager.get_metadata()

    # Send request to delete the session
    response = client.delete(f"/sessions/{session_id}")
    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": f"Session {session_id} deleted successfully"}

    # Check if session is removed from store
    assert session_id not in conversation_store
