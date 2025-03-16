from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks,Request
from fastapi.responses import JSONResponse
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import uuid

from app.models.schema import QueryRequest, QueryResponse, SessionResponse, SessionHistoryResponse, SessionInit
from app.services.conversation_service import ConversationManager, get_conversation_manager, conversation_store
from app.services.ai_service import classify_query_type, handle_general_conversation
from app.services.data_service import process_dataframe_query, get_dataframe
from app.config import CONVERSATION_TIMEOUT_HOURS

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Background task to clean up old conversations
async def cleanup_old_conversations():
    """Remove conversations that haven't been accessed for more than CONVERSATION_TIMEOUT_HOURS"""
    cutoff_time = datetime.now() - timedelta(hours=CONVERSATION_TIMEOUT_HOURS)
    removed = 0
    
    for session_id in list(conversation_store.keys()):
        if conversation_store[session_id]["last_access"] < cutoff_time:
            conversation_store.pop(session_id)
            removed += 1
    
    logger.info(f"Cleaned up {removed} old conversations")

# Root route (for health check)
@router.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Excel Query API (with Gemini) is running!",
        "timestamp": datetime.now().isoformat()
    }
@router.options("/")
async def options(request: Request):
    return JSONResponse(content="",status_code=200)

# Initialize a session
@router.post("/sessions/init", response_model=SessionInit)
async def init_session():
    """Initialize a new session or return an existing one"""
    session_id = str(uuid.uuid4())
    
    # Create new conversation manager for this session
    conversation_manager = ConversationManager(session_id)
    
    return SessionInit(
        sessionId=session_id
    )

# Create a new session explicitly
@router.post("/sessions/create", response_model=SessionInit)
async def create_session():
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    
    # Create new conversation manager for this session
    conversation_manager = ConversationManager(session_id)
    
    return SessionInit(
        sessionId=session_id
    )

# Get chat history
@router.get("/sessions/history", response_model=SessionHistoryResponse)
async def get_session_history():
    """Get list of recent chat sessions"""
    # Use the list_conversations function from conversation_service
    from app.services.conversation_service import list_conversations
    
    # Get paginated conversations (default 20)
    conversations, total_count = list_conversations(limit=20, offset=0)
    
    # Format for response
    history = []
    for conv in conversations:
        history.append({
            "sessionId": conv["session_id"],
            "createdAt": conv.get("created_at", datetime.now().isoformat()),
            "updatedAt": conv.get("last_access", conv.get("created_at", datetime.now().isoformat())),
            "title": conv.get("title", f"Conversation {conv['session_id'][:8]}"),
            "messageCount": conv.get("message_count", 0)
        })
    
    return SessionHistoryResponse(
        history=history
    )

# Get a specific session
@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get details for a specific chat session"""
    try:
        # Load the conversation using ConversationManager
        conversation_manager = ConversationManager(session_id)
        
        # Get all messages
        messages_obj = conversation_manager.get_messages()
        
        # Get metadata
        metadata = conversation_manager.get_metadata()
        
        # Format messages for frontend
        messages = []
        for msg in messages_obj:
            messages.append({
                "text": msg.text,
                "sender": msg.sender,
                "timestamp": msg.timestamp,
                "source": getattr(msg, "source", "conversation"),
                "isError": getattr(msg, "isError", False)
            })
        
        return SessionResponse(
            id=session_id,
            messages=messages,
            createdAt=metadata.get("created_at", datetime.now().isoformat()),
            updatedAt=metadata.get("last_access", datetime.now().isoformat()),
            title=metadata.get("title", f"Conversation {session_id[:8]}")
        )
    
    except Exception as e:
        logger.error(f"Error retrieving session {session_id}: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Session not found or error occurred: {str(e)}")

# Load a specific chat session
@router.post("/sessions/load/{session_id}", response_model=SessionResponse)
async def load_session(session_id: str):
    """Load a specific chat session with all its messages"""
    try:
        # Load the conversation using ConversationManager
        conversation_manager = ConversationManager(session_id)
        
        # Get all messages
        messages_obj = conversation_manager.get_messages()
        
        # Get metadata
        metadata = conversation_manager.get_metadata()
        
        # Format messages for frontend
        messages = []
        for msg in messages_obj:
            messages.append({
                "text": msg.text,
                "sender": msg.sender,
                "timestamp": msg.timestamp,
                "source": getattr(msg, "source", "conversation"),
                "isError": getattr(msg, "isError", False)
            })
        
        # Update the last access time
        conversation_manager.conversation_data["last_access"] = datetime.now().isoformat()
        conversation_manager._save_conversation()
        
        return SessionResponse(
            id=session_id,
            messages=messages,
            createdAt=metadata.get("created_at", datetime.now().isoformat()),
            updatedAt=datetime.now().isoformat(),
            title=metadata.get("title", f"Conversation {session_id[:8]}")
        )
    
    except Exception as e:
        logger.error(f"Error loading session {session_id}: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Session not found or error occurred: {str(e)}")

@router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest, 
    background_tasks: BackgroundTasks,
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    """Process a natural language query against the employee data"""
    question = request.query
    session_id = request.session_id or str(uuid.uuid4())
    
    # Schedule cleanup in background
    background_tasks.add_task(cleanup_old_conversations)
    
    if not question or question.strip() == "":
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    # Initialize conversation manager with provided session ID
    conversation_manager = ConversationManager(session_id)
    
    try:
        # First determine if this is a data analysis question or general conversation
        query_type = await classify_query_type(question, conversation_manager)
        logger.info(f"Query type for '{question[:50]}...': {query_type}")
        
        if query_type == "GENERAL_CONVERSATION":
            # Handle as general conversation
            answer = await handle_general_conversation(question, conversation_manager)
            conversation_manager.add_message(question, answer)
            
            return QueryResponse(
                answer=answer,
                source="conversation",
                session_id=session_id
            )
        else:
            # Process as a data analysis query
            result_data, answer, code = await process_dataframe_query(question, conversation_manager)
            
            # Store the interaction in conversation history
            conversation_manager.add_message(question, answer, result_data)
            
            response = QueryResponse(
                answer=answer, 
                source="dataframe",
                session_id=session_id
            )
            
            # Include debug info if in development
            if os.getenv("ENV") == "development":
                response.debug = {
                    "code": code,
                    "raw_result": result_data
                }
                
            return response
            
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        return QueryResponse(
            answer=f"I'm sorry, but I encountered an error while processing your question. Please try rephrasing or ask something else.",
            source="error", 
            session_id=session_id
        )

# Delete a specific session
@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a specific chat session"""
    try:
        conversation_manager = ConversationManager(session_id)
        success = conversation_manager.delete_conversation()
        
        if success:
            return {"status": "success", "message": f"Session {session_id} deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to delete session {session_id}")
    
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Session not found or error occurred: {str(e)}")

# Clear conversation history for a session
@router.post("/sessions/{session_id}/clear")
async def clear_session_history(session_id: str):
    """Clear all messages in a specific chat session but keep the session"""
    try:
        conversation_manager = ConversationManager(session_id)
        conversation_manager.clear_history()
        
        return {"status": "success", "message": f"Conversation history for session {session_id} cleared"}
    
    except Exception as e:
        logger.error(f"Error clearing history for session {session_id}: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Session not found or error occurred: {str(e)}")

@router.get("/debug")
async def debug():
    """Debug endpoint providing system information"""
    # Count files in storage directory
    from app.services.conversation_service import STORAGE_DIR
    file_count = len([f for f in os.listdir(STORAGE_DIR) if f.endswith('.json')])
    
    return {
        "sessions_count": len(conversation_store),
        "session_ids": list(conversation_store.keys()),
        "persisted_sessions_count": file_count,
        "system_time": datetime.now().isoformat()
    }

@router.get("/cleanup")
async def cleanup_old_sessions(background_tasks: BackgroundTasks):
    """Manually trigger cleanup of old sessions"""
    background_tasks.add_task(cleanup_old_conversations)
    
    # Also clean up old conversation files
    from app.services.conversation_service import cleanup_old_conversations as cleanup_files
    deleted_count = cleanup_files(max_age_days=CONVERSATION_TIMEOUT_HOURS//24)
    
    return {
        "status": "cleanup scheduled", 
        "files_deleted": deleted_count
    }