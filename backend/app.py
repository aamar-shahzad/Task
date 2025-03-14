from fastapi import FastAPI, HTTPException, Request, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union, Literal
import pandas as pd
import google.generativeai as genai
import os
from dotenv import load_dotenv
import re
from datetime import datetime, timedelta
import logging
from functools import lru_cache
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Data Analysis API",
    description="API for analyzing employee data using natural language queries",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Configure Google Gemini API
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    logger.error("GEMINI_API_KEY not found in environment variables!")
else:
    genai.configure(api_key=API_KEY)

# Cache for dataframe to avoid reloading
@lru_cache(maxsize=1)
def get_dataframe():
    """Load or create the employee dataframe with caching"""
    try:
        return pd.read_excel('employee_data.xlsx')
    except Exception as e:
        logger.warning(f"Could not load employee_data.xlsx: {e}. Creating sample data instead.")
        # Create sample data if file isn't found
        data = {
            'EmployeeID': [f'Employee_{i}' for i in range(1, 11)],
            'Department': ['IT', 'Marketing', 'Sales', 'HR', 'Finance', 'IT', 'Marketing', 'Sales', 'HR', 'Finance'],
            'Salary': [85000, 70000, 65000, 60000, 75000, 90000, 72000, 68000, 62000, 78000],
            'Experience': [5, 3, 4, 2, 6, 7, 4, 5, 3, 8],
            'Performance': [4.2, 3.8, 3.5, 4.0, 4.5, 4.8, 3.9, 3.7, 4.1, 4.3]
        }
        df = pd.DataFrame(data)
        df.to_excel('employee_data.xlsx', index=False)
        return df

# In-memory storage for conversations - in production, use Redis or a database
conversation_store = {}

# Constants
MAX_HISTORY_ENTRIES = 10
CONVERSATION_TIMEOUT_HOURS = 24
UNSAFE_CODE_PATTERNS = ['import', 'exec', 'eval', 'os.', 'system', '__', 'open', 'file', 'write']


class ConversationManager:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.max_history = MAX_HISTORY_ENTRIES
        
        # Initialize if not exists
        if session_id not in conversation_store:
            conversation_store[session_id] = {
                "history": [],
                "last_access": datetime.now(),
                "context": {},
            }
        else:
            # Update access time
            conversation_store[session_id]["last_access"] = datetime.now()
    
    def add_message(self, user_message: str, system_response: str, result_data: Any = None):
        conversation_store[self.session_id]["history"].append({
            "user": user_message,
            "system": system_response,
            "timestamp": datetime.now().isoformat(),
            "result_type": type(result_data).__name__ if result_data is not None else None
        })
        
        # Trim history if too long
        if len(conversation_store[self.session_id]["history"]) > self.max_history:
            conversation_store[self.session_id]["history"].pop(0)
        
        # Update last access time
        conversation_store[self.session_id]["last_access"] = datetime.now()
        
        # Store last result for follow-up questions
        if result_data is not None:
            conversation_store[self.session_id]["context"]["last_result"] = result_data
    
    def get_history(self):
        return conversation_store[self.session_id]["history"]
    
    def get_context(self):
        return conversation_store[self.session_id]["context"]
    
    def get_conversation_text(self, limit=5):
        """Get conversation history as a formatted text for context, limited to the most recent messages"""
        history = self.get_history()
        if not history:
            return ""
        
        # Take only the most recent conversations for context
        recent_history = history[-limit:]
        
        formatted = "Previous conversation:\n"
        for msg in recent_history:
            formatted += f"User: {msg['user']}\n"
            formatted += f"System: {msg['system']}\n"
        
        return formatted


class AiModelService:
    """Service for interacting with the Gemini AI model"""
    
    def __init__(self, model_name='gemini-1.5-flash'):
        self.model_name = model_name
        
    async def generate_content(self, prompt):
        """Async wrapper around the synchronous Gemini API"""
        loop = asyncio.get_event_loop()
        model = genai.GenerativeModel(self.model_name)
        
        try:
            # Run in a thread pool to not block the event loop
            response = await loop.run_in_executor(
                None, lambda: model.generate_content(prompt)
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error generating content with {self.model_name}: {str(e)}")
            raise


async def classify_query_type(question: str, conversation_manager=None):
    """Determine if the query is a data analysis question or a general conversation question"""
    try:
        df = get_dataframe()
        ai_service = AiModelService()
        
        context_text = ""
        if conversation_manager:
            context_text = conversation_manager.get_conversation_text(limit=3)  # Limited context for efficiency
        
        # DataFrame info
        df_columns = list(df.columns)
        
        prompt = f"""
        Task: Classify the user's query as either DATA_ANALYSIS or GENERAL_CONVERSATION.
        
        Available data in the system:
        - DataFrame with columns: {df_columns}
        - Sample data (first 2 rows):
        {df.head(2).to_string()}
        
        Previous conversation context:
        {context_text}
        
        User query: "{question}"
        
        Classification instructions:
        1. DATA_ANALYSIS: Only classify as this if the query explicitly requests information from the DataFrame or is clearly a follow-up to a previous data-related question
        2. GENERAL_CONVERSATION: Classify as this if:
           - The query is a general knowledge question (e.g., "What is RAG in AI?")
           - The query is a greeting or casual conversation
           - The query is asking about something unrelated to the specific DataFrame contents
        3. When in doubt or if the query is ambiguous, classify as GENERAL_CONVERSATION
        
        Examples:
        - "What is machine learning?" → GENERAL_CONVERSATION
        - "What's the average salary?" → DATA_ANALYSIS
        - "Tell me about natural language processing" → GENERAL_CONVERSATION
        - "How many employees are in the IT department?" → DATA_ANALYSIS
        
        Respond with ONLY one of these exact strings: "DATA_ANALYSIS" or "GENERAL_CONVERSATION"
        """
        
        query_type = await ai_service.generate_content(prompt)
        
        # Make sure we get one of the expected responses
        if query_type not in ["DATA_ANALYSIS", "GENERAL_CONVERSATION"]:
            logger.warning(f"Unexpected query type classification: {query_type}")
            # Default to GENERAL_CONVERSATION if unclear
            return "GENERAL_CONVERSATION"
            
        return query_type
        
    except Exception as e:
        logger.error(f"Error in query classification: {str(e)}")
        # Default to GENERAL_CONVERSATION on error
        return "GENERAL_CONVERSATION"

async def handle_general_conversation(question: str, conversation_manager=None):
    """Handle general conversation queries with direct answers"""
    try:
        ai_service = AiModelService()
        
        context_text = ""
        if conversation_manager:
            context_text = conversation_manager.get_conversation_text(limit=3)
        
        # Determine appropriate response length
        length_analysis_prompt = f"""
        Analyze this conversational query: "{question}"
        
        Determine if this query requires:
        1. A brief, direct response (1-2 sentences)
        2. A medium-length response (3-5 sentences)
        3. A detailed, comprehensive response (multiple paragraphs)
        
        Consider the nature of the question - is it a simple greeting, a complex question,
        or something that requires elaboration?
        
        Return ONLY one of these options: "BRIEF", "MEDIUM", or "DETAILED"
        """
        
        response_length = await ai_service.generate_content(length_analysis_prompt)
        response_length = response_length.strip().upper()
        
        # Default to BRIEF for conversation if the response isn't one of the expected values
        if response_length not in ["BRIEF", "MEDIUM", "DETAILED"]:
            response_length = "BRIEF"
            
        logger.info(f"Determined conversation response length: {response_length}")
        
        prompt = f"""
        You are an AI assistant for a data analysis application, but you should directly answer general knowledge questions without redirecting users to data-related queries.
        
        Previous conversation context:
        {context_text}
        
        User query: "{question}"
        
        Instructions for responding:
        1. If this is a general knowledge question, answer it directly and completely without mentioning the available data or suggesting data-related questions
        2. Only refer to the employee data if the question is ambiguous and might be related to data analysis
        3. Do not end general knowledge responses with statements like "This isn't related to the available data" or "If you'd like to ask about the data instead..."
        4. Provide a {response_length.lower()} response that is helpful and conversational
        
        Response length guidelines:
        - BRIEF: A concise, direct response (1-2 sentences)
        - MEDIUM: A well-rounded response with some details (3-5 sentences)
        - DETAILED: A comprehensive response with thorough information (multiple paragraphs)
        
        Your current response should be {response_length.lower()} in length.
        """
        
        response_text = await ai_service.generate_content(prompt)
        return response_text
        
    except Exception as e:
        logger.error(f"Error in conversation handling: {str(e)}")
        return f"I'm sorry, I couldn't process your question properly. Please try again."

async def process_dataframe_query(question: str, conversation_manager=None):
    """Process a question against the dataframe with conversation context"""
    try:
        df = get_dataframe()
        ai_service = AiModelService()
        
        # Get conversation context for better understanding
        context_text = ""
        last_result = None
        
        if conversation_manager:
            context_text = conversation_manager.get_conversation_text(limit=3)
            context_dict = conversation_manager.get_context()
            last_result = context_dict.get("last_result")
        
        # Get the shape of the DataFrame
        df_shape = df.shape  # (rows, columns)
        
        # First generate the code
        prompt = f"""
        DataFrame Analysis Task:
        
        DataFrame 'df' specifications:
        - Dimensions: {df_shape[0]} rows × {df_shape[1]} columns
        - Available columns: {list(df.columns)}
        - Data types: {df.dtypes.to_dict()}
        - Sample data (first 3 rows):
        {df.head(3).to_string()}
        
        Previous context:
        {context_text}
        
        Question to analyze: "{question}"
        
        Instructions:
        1. Return EXACTLY ONE pandas operation/statement using only the 'df' DataFrame
        2. Use only pandas built-in functions and methods
        3. Do not reference any previous results or context variables
        4. Focus on answering the current question directly
        5. Handle potential NULL/NaN values appropriately
        6. If aggregating, use appropriate grouping
        
        Generate ONLY executable pandas code without any explanations or comments.
        """
        
        code = await ai_service.generate_content(prompt)
        
        # Clean up code (remove markdown formatting, etc.)
        code = re.sub(r'```python\s*', '', code)
        code = re.sub(r'```\s*', '', code)
        code = code.strip()
        
        # For debugging
        logger.info(f"Generated code: {code}")
        
        # Enhanced security check
        if any(unsafe_term in code.lower() for unsafe_term in UNSAFE_CODE_PATTERNS):
            logger.warning(f"Unsafe code detected: {code}")
            return None, "I cannot process this query as it might involve unsafe operations.", None
        
        # Execute the code with limited globals
        safe_globals = {
            "df": df, 
            "pd": pd,
        }
        
        # Execute in try block to catch any runtime errors
        try:
            result = eval(code, safe_globals)
        except Exception as exec_error:
            logger.error(f"Error executing generated code: {str(exec_error)}")
            return None, f"I couldn't process that query correctly. The specific error was: {str(exec_error)}", None
        
        # Convert result to appropriate format
        if isinstance(result, pd.DataFrame):
            # Limit large result sets
            if len(result) > 100:
                result = result.head(100)
                limited_result = True
            else:
                limited_result = False
                
            result_data = result.to_dict(orient="records")
            if limited_result:
                result_note = f"(Showing first 100 of {len(result)} results)"
            else:
                result_note = f"(Found {len(result)} results)"
                
        elif isinstance(result, pd.Series):
            result_data = result.to_dict()
            result_note = ""
        else:
            result_data = result
            result_note = ""
        
        logger.info(f"Result type: {type(result).__name__}")
        
        # Analyze the question to determine appropriate response length
        length_analysis_prompt = f"""
        Analyze this question: "{question}"
        
        Determine if this query requires:
        1. A brief, direct answer (1-2 sentences)
        2. A medium-length explanation (3-5 sentences)
        3. A detailed, comprehensive response (multiple paragraphs)
        
        Return ONLY one of these options: "BRIEF", "MEDIUM", or "DETAILED"
        """
        
        response_length = await ai_service.generate_content(length_analysis_prompt)
        response_length = response_length.strip().upper()
        
        # Default to BRIEF if the response isn't one of the expected values
        if response_length not in ["BRIEF", "MEDIUM", "DETAILED"]:
            response_length = "BRIEF"
            
        logger.info(f"Determined response length for query: {response_length}")
        
        # Generate a human-friendly explanation based on determined length
        explanation_prompt = f"""
        Question: {question}
        Data result: {result_data}
        
        Create a natural, conversational response that directly answers the question.
        
        Response requirements:
        1. Be concise and to the point - prefer 1-2 sentences when possible
        2. Include the specific answer/number from the data result
        3. Sound like a human answering a question, not an AI analyzing data
        4. DO NOT reveal how the analysis was performed or refer to dataframes/columns
        5. DO NOT explain the methodology or details about how you arrived at the answer
        6. DO NOT add unnecessary context, explanations, or interpretations
        7. DO NOT mention limitations of the analysis or suggest further analysis
        
        Make your response length {response_length.lower()}:
        - BRIEF: Just 1-2 direct sentences with the answer
        - MEDIUM: 3-4 sentences with minimal context
        - DETAILED: 5-6 sentences including relevant context
        
        Examples of good responses:
        - "The average salary in the Sales department is $66,500."
        - "Marketing has the highest average performance rating at 4.2, followed by IT at 4.0."
        - "Based on the data, John has the most experience with 8 years, while the company average is 4.5 years."
        """
        
        explanation = await ai_service.generate_content(explanation_prompt)
        
        return result_data, explanation, code
        
    except Exception as e:
        logger.error(f"Error processing dataframe query: {str(e)}", exc_info=True)
        return None, f"Error processing query: {str(e)}", None
# Input schema to match frontend
class QueryRequest(BaseModel):
    query: str = Field(..., description="The natural language query to process")
    session_id: Optional[str] = Field("default", description="Session identifier for conversation tracking")


class QueryResponse(BaseModel):
    answer: str
    source: Literal["conversation", "dataframe", "error"]
    session_id: str
    debug: Optional[Dict[str, Any]] = None


# Dependency for getting a conversation manager
def get_conversation_manager(session_id: str = "default"):
    return ConversationManager(session_id)


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
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Excel Query API (with Gemini) is running!",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest, 
    background_tasks: BackgroundTasks,
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    """Process a natural language query against the employee data"""
    question = request.query
    session_id = request.session_id or "default"
    
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


@app.get("/debug")
async def debug():
    """Debug endpoint providing system information"""
    if os.getenv("ENV") != "development":
        raise HTTPException(status_code=403, detail="Debug endpoint only available in development mode")
    
    df = get_dataframe()
    
    return {
        "system_info": {
            "active_sessions": len(conversation_store),
            "dataframe_shape": df.shape,
            "dataframe_columns": list(df.columns),
            "memory_usage": {col: df[col].memory_usage(deep=True) for col in df.columns}
        }
    }


@app.get("/cleanup")
async def cleanup_old_sessions():
    """Manually trigger cleanup of old sessions"""
    # Provide admin access control in production
    await cleanup_old_conversations()
    return {"message": f"Cleanup completed", "active_sessions": len(conversation_store)}


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the app on startup"""
    logger.info("Starting Data Analysis API")
    # Load dataframe on startup to verify it works
    try:
        df = get_dataframe()
        logger.info(f"Loaded dataframe with shape {df.shape}")
    except Exception as e:
        logger.error(f"Error loading dataframe: {str(e)}")