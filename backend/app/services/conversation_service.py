from datetime import datetime, timedelta
from typing import Any, List, Dict, Optional, Tuple
import logging
import json
import os
import shutil
from app.models.schema import Message
from app.config import MAX_HISTORY_ENTRIES

logger = logging.getLogger(__name__)

# Configuration for persistence
STORAGE_DIR = os.getenv("STORAGE_DIR", "data/conversations")
os.makedirs(STORAGE_DIR, exist_ok=True)

# Keep this for backward compatibility
conversation_store = {}

class ConversationManager:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.max_history = MAX_HISTORY_ENTRIES
        self.storage_path = os.path.join(STORAGE_DIR, f"{session_id}.json")
        
        # Load existing conversation or initialize new one
        self.conversation_data = self._load_conversation()
        
        # Update access time
        self.conversation_data["last_access"] = datetime.now().isoformat()
        
        # For backward compatibility, keep the conversation store updated
        conversation_store[session_id] = {
            "messages": self.conversation_data["messages"],
            "last_access": datetime.now(),
            "context": self.conversation_data["context"],
        }
        
        self._save_conversation()
    
    def _load_conversation(self) -> Dict[str, Any]:
        """Load conversation from disk or initialize new one if not exists"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    
                # Convert string timestamps back to Message objects
                if "messages" in data:
                    messages = []
                    for msg_dict in data["messages"]:
                        messages.append(Message(**msg_dict))
                    data["messages"] = messages
                    
                return data
            except Exception as e:
                logger.error(f"Error loading conversation {self.session_id}: {e}")
        
        # Return new conversation data if file doesn't exist or there was an error
        return {
            "messages": [],
            "last_access": datetime.now().isoformat(),
            "context": {},
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "title": f"Conversation {self.session_id[:8]}",
                "tags": []
            }
        }
    
    def _save_conversation(self):
        """Save conversation to disk"""
        try:
            # Convert Message objects to dicts for JSON serialization
            data_to_save = self.conversation_data.copy()
            data_to_save["messages"] = [msg.dict() for msg in self.conversation_data["messages"]]
            
            # Ensure metadata exists
            if "metadata" not in data_to_save:
                data_to_save["metadata"] = {
                    "created_at": datetime.now().isoformat(),
                    "title": f"Conversation {self.session_id[:8]}",
                    "tags": []
                }
            
            # Serialize context data that might not be JSON serializable
            if "last_result" in data_to_save["context"]:
                # You might need a custom serialization approach depending on what's in last_result
                try:
                    json.dumps(data_to_save["context"]["last_result"])
                except (TypeError, OverflowError):
                    # If not serializable, store a placeholder or string representation
                    data_to_save["context"]["last_result"] = str(data_to_save["context"]["last_result"])
            
            with open(self.storage_path, 'w') as f:
                json.dump(data_to_save, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving conversation {self.session_id}: {e}")
    
    def add_message(self, user_message: str, system_response: str, result_data: Any = None):
        # Create user message
        user_msg = Message(
            text=user_message,
            sender="user",
            timestamp=datetime.now().isoformat()
        )
        
        # Create system message
        system_msg = Message(
            text=system_response,
            sender="assistant",
            timestamp=datetime.now().isoformat(),
            source="dataframe" if result_data is not None else "conversation",
            isError=False
        )
        
        # Add messages to store
        self.conversation_data["messages"].append(user_msg)
        self.conversation_data["messages"].append(system_msg)
        
        # Auto-generate title from first user message if no title exists
        if len(self.conversation_data["messages"]) == 2:  # First message pair
            if "metadata" not in self.conversation_data:
                self.conversation_data["metadata"] = {}
            
            # Generate a title from the first user message (max 50 chars)
            first_msg = user_message[:50] + "..." if len(user_message) > 50 else user_message
            self.conversation_data["metadata"]["title"] = first_msg
        
        # Trim history if too long (accounting for pairs of messages)
        if len(self.conversation_data["messages"]) > self.max_history * 2:
            # Remove two messages at a time (user + system)
            self.conversation_data["messages"] = self.conversation_data["messages"][2:]
        
        # Update last access time
        self.conversation_data["last_access"] = datetime.now().isoformat()
        
        # Store last result for follow-up questions
        if result_data is not None:
            self.conversation_data["context"]["last_result"] = result_data
        
        # Keep in-memory store in sync (for backward compatibility)
        conversation_store[self.session_id] = {
            "messages": self.conversation_data["messages"],
            "last_access": datetime.now(),
            "context": self.conversation_data["context"],
        }
        
        # Save to disk
        self._save_conversation()
    
    def get_messages(self) -> List[Message]:
        """Get all messages in the conversation"""
        return self.conversation_data["messages"]
    
    def get_context(self) -> Dict[str, Any]:
        """Get the context data for this conversation"""
        return self.conversation_data["context"]
    
    def get_conversation_text(self, limit: int = 5) -> str:
        """Get conversation history as a formatted text for context, limited to the most recent message pairs"""
        messages = self.get_messages()
        if not messages:
            return ""
        
        # Calculate how many message pairs to include (each pair is user + assistant)
        pair_limit = min(limit, len(messages) // 2)
        start_idx = max(0, len(messages) - (pair_limit * 2))
        
        # Get the recent messages
        recent_messages = messages[start_idx:]
        
        formatted = "Previous conversation:\n"
        for i in range(0, len(recent_messages), 2):
            if i + 1 < len(recent_messages):  # Make sure we have both user and assistant messages
                user_msg = recent_messages[i]
                assistant_msg = recent_messages[i + 1]
                formatted += f"User: {user_msg.text}\n"
                formatted += f"System: {assistant_msg.text}\n"
        
        return formatted
    
    def update_metadata(self, title: Optional[str] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Update conversation metadata"""
        if "metadata" not in self.conversation_data:
            self.conversation_data["metadata"] = {
                "created_at": datetime.now().isoformat(),
                "title": f"Conversation {self.session_id[:8]}",
                "tags": []
            }
        
        if title is not None:
            self.conversation_data["metadata"]["title"] = title
        
        if tags is not None:
            self.conversation_data["metadata"]["tags"] = tags
        
        self._save_conversation()
        return self.conversation_data["metadata"]
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get conversation metadata"""
        if "metadata" not in self.conversation_data:
            self.conversation_data["metadata"] = {
                "created_at": datetime.now().isoformat(),
                "title": f"Conversation {self.session_id[:8]}",
                "tags": []
            }
            self._save_conversation()
        
        return self.conversation_data["metadata"]
    
    def clear_history(self) -> None:
        """Clear all messages in the conversation but keep the session"""
        self.conversation_data["messages"] = []
        self.conversation_data["context"] = {}
        self._save_conversation()
        
        # Update in-memory store
        conversation_store[self.session_id]["messages"] = []
        conversation_store[self.session_id]["context"] = {}
    
    def delete_conversation(self) -> bool:
        """Delete the conversation completely"""
        try:
            if os.path.exists(self.storage_path):
                os.remove(self.storage_path)
            
            # Remove from in-memory store
            if self.session_id in conversation_store:
                del conversation_store[self.session_id]
            
            return True
        except Exception as e:
            logger.error(f"Error deleting conversation {self.session_id}: {e}")
            return False

# Chat history management functions

def list_conversations(limit: int = 10, offset: int = 0, 
                       filter_tag: Optional[str] = None,
                       search_query: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
    """
    List all conversations with pagination, filtering and search
    Returns: (conversations list, total count)
    """
    conversations = []
    
    # Get all conversation files
    files = [f for f in os.listdir(STORAGE_DIR) if f.endswith('.json')]
    
    # Process each file to extract metadata
    for filename in files:
        file_path = os.path.join(STORAGE_DIR, filename)
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            session_id = filename.replace('.json', '')
            
            # Extract basic metadata
            metadata = data.get("metadata", {
                "title": f"Conversation {session_id[:8]}",
                "created_at": data.get("last_access", datetime.now().isoformat()),
                "tags": []
            })
            
            # Add session_id to metadata
            metadata["session_id"] = session_id
            
            # Count messages
            message_count = len(data.get("messages", []))
            metadata["message_count"] = message_count
            
            # Apply tag filter if provided
            if filter_tag and filter_tag not in metadata.get("tags", []):
                continue
            
            # Apply search query if provided
            if search_query:
                search_query = search_query.lower()
                title = metadata.get("title", "").lower()
                
                # Search in title
                if search_query not in title:
                    # If not in title, check first few messages
                    found = False
                    for msg in data.get("messages", [])[:6]:  # Check first 3 exchanges
                        if isinstance(msg, dict) and search_query in msg.get("text", "").lower():
                            found = True
                            break
                    
                    if not found:
                        continue
            
            conversations.append(metadata)
        except Exception as e:
            logger.error(f"Error reading conversation file {filename}: {e}")
    
    # Sort by last access time (most recent first)
    conversations.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    # Get total count before pagination
    total_count = len(conversations)
    
    # Apply pagination
    paginated = conversations[offset:offset+limit] if offset < len(conversations) else []
    
    return paginated, total_count

def export_conversation(session_id: str, format: str = "json") -> Tuple[bool, str, Any]:
    """
    Export a conversation in the specified format
    Returns: (success, filename, data)
    """
    file_path = os.path.join(STORAGE_DIR, f"{session_id}.json")
    
    if not os.path.exists(file_path):
        return False, "", None
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if format.lower() == "json":
            return True, f"{session_id}.json", data
        
        elif format.lower() == "txt":
            # Convert to plain text format
            text_content = f"Conversation: {data.get('metadata', {}).get('title', session_id)}\n"
            text_content += f"Created: {data.get('metadata', {}).get('created_at', '')}\n\n"
            
            # Add each message
            for msg in data.get("messages", []):
                sender = msg.get("sender", "unknown")
                text = msg.get("text", "")
                text_content += f"{sender.capitalize()}: {text}\n\n"
            
            return True, f"{session_id}.txt", text_content
        
        elif format.lower() == "html":
            # Create HTML representation
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Conversation Export - {data.get('metadata', {}).get('title', session_id)}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .message {{ margin-bottom: 15px; padding: 10px; border-radius: 5px; }}
        .user {{ background-color: #f0f0f0; }}
        .assistant {{ background-color: #e1f5fe; }}
        .metadata {{ margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="metadata">
        <h1>{data.get('metadata', {}).get('title', 'Conversation')}</h1>
        <p>Created: {data.get('metadata', {}).get('created_at', '')}</p>
    </div>
    <div class="conversation">
"""
            
            # Add each message
            for msg in data.get("messages", []):
                sender = msg.get("sender", "unknown")
                text = msg.get("text", "").replace("\n", "<br>")
                html_content += f"""    <div class="message {sender}">
        <strong>{sender.capitalize()}:</strong><br>
        {text}
    </div>
"""
            
            html_content += """    </div>
</body>
</html>"""
            
            return True, f"{session_id}.html", html_content
        
        else:
            return False, "", None
            
    except Exception as e:
        logger.error(f"Error exporting conversation {session_id}: {e}")
        return False, "", None

def import_conversation(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    Import a conversation from a JSON file
    Returns: (success, session_id if successful)
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Generate a new session ID
        session_id = f"imported_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Ensure the data has the required structure
        if "messages" not in data:
            data["messages"] = []
        
        if "context" not in data:
            data["context"] = {}
        
        if "metadata" not in data:
            data["metadata"] = {
                "title": f"Imported conversation",
                "created_at": datetime.now().isoformat(),
                "tags": ["imported"]
            }
        
        # Add import timestamp
        data["metadata"]["imported_at"] = datetime.now().isoformat()
        
        # Save to the conversations directory
        dest_path = os.path.join(STORAGE_DIR, f"{session_id}.json")
        with open(dest_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return True, session_id
        
    except Exception as e:
        logger.error(f"Error importing conversation: {e}")
        return False, None

def backup_all_conversations(backup_dir: Optional[str] = None) -> Tuple[bool, str]:
    """
    Create a backup of all conversations
    Returns: (success, backup_path)
    """
    if backup_dir is None:
        backup_dir = os.path.join(os.path.dirname(STORAGE_DIR), "backups")
    
    os.makedirs(backup_dir, exist_ok=True)
    
    # Create a timestamped backup folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"conversations_backup_{timestamp}")
    os.makedirs(backup_path, exist_ok=True)
    
    try:
        # Copy all conversation files to the backup folder
        files_copied = 0
        for filename in os.listdir(STORAGE_DIR):
            if filename.endswith('.json'):
                src_path = os.path.join(STORAGE_DIR, filename)
                dst_path = os.path.join(backup_path, filename)
                shutil.copy2(src_path, dst_path)
                files_copied += 1
        
        logger.info(f"Backed up {files_copied} conversation files to {backup_path}")
        return True, backup_path
        
    except Exception as e:
        logger.error(f"Error backing up conversations: {e}")
        return False, ""

def cleanup_old_conversations(max_age_days: int = 30):
    """Remove conversation files older than max_age_days"""
    now = datetime.now()
    deleted_count = 0
    
    for filename in os.listdir(STORAGE_DIR):
        if not filename.endswith('.json'):
            continue
            
        file_path = os.path.join(STORAGE_DIR, filename)
        try:
            # Get the last modified time of the file
            file_mtime = os.path.getmtime(file_path)
            last_modified = datetime.fromtimestamp(file_mtime)
            age_days = (now - last_modified).days
            
            # Also check last_access inside the file for more accuracy
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    
                if "last_access" in data:
                    last_access = datetime.fromisoformat(data["last_access"].replace('Z', '+00:00'))
                    file_age_days = (now - last_access).days
                    # Use the most recent of file modification time and last_access
                    age_days = min(age_days, file_age_days)
            except:
                # If we can't read the file, fall back to file system date
                pass
                
            if age_days > max_age_days:
                os.remove(file_path)
                deleted_count += 1
                logger.info(f"Removed old conversation file: {filename}")
        except Exception as e:
            logger.error(f"Error cleaning up file {filename}: {e}")
    
    return deleted_count

def get_conversation_manager(session_id: str = "default"):
    """Dependency for FastAPI to inject a ConversationManager instance"""
    return ConversationManager(session_id)