import google.generativeai as genai
import asyncio
import logging
import re
from app.config import UNSAFE_CODE_PATTERNS
from app.services.data_service import get_dataframe

logger = logging.getLogger(__name__)

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
        
        # Determine appropriate response length first
        length_analysis_prompt = f"""
        Analyze this conversational query: "{question}"
        
        Determine if this query requires:
        1. A brief, direct response (1-2 sentences)
        2. A medium-length response (3-5 sentences)
        3. A detailed, comprehensive response (multiple paragraphs)
        
        Return ONLY one of these options without explanation: "BRIEF", "MEDIUM", or "DETAILED"
        """
        
        response_length = await ai_service.generate_content(length_analysis_prompt)
        response_length = response_length.strip().upper()
        
        # Default to BRIEF for conversation if the response isn't one of the expected values
        if response_length not in ["BRIEF", "MEDIUM", "DETAILED"]:
            response_length = "BRIEF"
            
        logger.info(f"Determined conversation response length: {response_length}")
        
        # Set length parameters based on analysis
        if response_length == "BRIEF":
            length_instruction = "Provide a brief, concise response of 1-2 sentences only. Maximum 50 words."
            max_tokens = 75
        elif response_length == "MEDIUM":
            length_instruction = "Provide a moderately detailed response of 3-5 sentences only. Maximum 100 words."
            max_tokens = 150
        else:  # DETAILED
            length_instruction = "Provide a comprehensive, detailed response with thorough information. Maximum 250 words."
            max_tokens = 300
        
        # Create a more structured prompt that enforces a single response
        prompt = f"""
        You are an AI assistant for a data analysis application responding to a general query.
        
        Previous conversation context:
        {context_text}
        
        User query: "{question}"
        
        IMPORTANT INSTRUCTIONS:
        1. Response length: {length_instruction}
        2. Format: Provide ONLY ONE natural conversational response with no labels or prefixes
        3. DO NOT output multiple versions of your response
        4. DO NOT prefix your response with "BRIEF:", "MEDIUM:", or "DETAILED:"
        5. DO NOT mention anything about response length or formatting in your answer
        6. Answer conversationally as if you're having a normal discussion
        7. Only mention the data if specifically asked about it

        Guidelines:
        - Keep responses concise and to the point
        - Avoid overly technical language or jargon
        - Provide a human-like, engaging response
        
        
        Your response:
        """
        
        # Use Gemini's generation config to enforce token limits
        model = genai.GenerativeModel(
            model_name=ai_service.model_name,
            generation_config={
                "max_output_tokens": max_tokens,
                "temperature": 0.7,  
                "top_p": 0.95,
                "top_k": 40
            }
        )
        
        # Run in a thread pool to not block the event loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: model.generate_content(prompt)
        )
        
        response_text = response.text.strip()
        
        # Additional post-processing to ensure no labels remain
        response_text = re.sub(r'^\s*(BRIEF|MEDIUM|DETAILED):\s*', '', response_text, flags=re.IGNORECASE)
        
        # Check if the response still contains multiple sections and take only the appropriate one
        if "BRIEF:" in response_text or "MEDIUM:" in response_text or "DETAILED:" in response_text:
            # If model still generated multiple sections, extract only the appropriate one
            pattern = rf"({response_length}:.*?)(?:BRIEF:|MEDIUM:|DETAILED:|$)"
            match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
            if match:
                section = match.group(1)
                # Remove the label
                response_text = re.sub(r'^\s*(BRIEF|MEDIUM|DETAILED):\s*', '', section, flags=re.IGNORECASE).strip()
            else:
                # If we can't find the right section, take the first paragraph as a fallback
                response_text = response_text.split('\n\n')[0]
        
        return response_text
        
    except Exception as e:
        logger.error(f"Error in conversation handling: {str(e)}")
        return "I'm sorry, I couldn't process your question properly. Please try again."