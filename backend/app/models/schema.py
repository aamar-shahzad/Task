from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union, Literal

# Input schema to match frontend
class QueryRequest(BaseModel):
    query: str = Field(..., description="The natural language query to process")
    session_id: Optional[str] = Field("default", description="Session identifier for conversation tracking")


class QueryResponse(BaseModel):
    answer: str
    source: Literal["conversation", "dataframe", "error"]
    session_id: str
    debug: Optional[Dict[str, Any]] = None


# New models for session management

class Message(BaseModel):
    text: str
    sender: Literal["user", "assistant"]
    timestamp: str
    source: Optional[str] = None
    isError: Optional[bool] = None


class SessionInit(BaseModel):
    sessionId: str


class SessionHistoryItem(BaseModel):
    sessionId: str
    title: str
    createdAt: str
    updatedAt: str


class SessionHistoryResponse(BaseModel):
    history: List[SessionHistoryItem]


class SessionResponse(BaseModel):
    id: str
    messages: List[Message]
    createdAt: str
    updatedAt: str