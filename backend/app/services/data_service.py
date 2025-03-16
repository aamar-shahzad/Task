# app/services/data_service.py
import pandas as pd
import logging
from functools import lru_cache
import os
import re

logger = logging.getLogger(__name__)
UNSAFE_CODE_PATTERNS = ['import', 'exec', 'eval', 'os.', 'system', '__', 'open', 'file', 'write']

# Cache for dataframe to avoid reloading
@lru_cache(maxsize=1)
def get_dataframe():
    """Load or create the employee dataframe with caching"""
    try:

        filepath="./app/data/Fake_Employee_Data.xlsx"
        if os.path.exists(filepath):
            print("file exists")
        else:
            print("file not exists")
        df = pd.read_excel(filepath, engine='openpyxl')
        print("df",df)

        return df
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
        # os.makedirs('data', exist_ok=True)
        # df.to_excel(os.path.join('data', 'employee_data.xlsx'), index=False)
        return df

async def process_dataframe_query(question: str, conversation_manager=None):
    """Process a question against the dataframe with conversation context"""
    try:
        df = get_dataframe()
        
        # Delayed import of AiModelService to avoid circular imports
        from app.services.ai_service import AiModelService
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
        
        # First, let's add a step to help the AI understand potential variations
        mapping_prompt = f"""
        User question: "{question}"
        
        DataFrame columns: {list(df.columns)}
        
        Task: Identify all potential column references in the user's question and map them to the EXACT column names in the DataFrame.
        
        Consider these variations:
        1. Singular vs plural forms (e.g., "sale" → "Sales")
        2. Case differences (e.g., "department" → "Department")
        3. Synonyms or related terms (e.g., "workers" → "EmployeeID")
        4. Misspellings or typos (e.g., "performence" → "Performance")
        
        Return a JSON object with mappings from user terms to actual column names.
        Example: {{"sale": "Sales", "workers": "EmployeeID"}}
        
        Return only the JSON object, nothing else.
        """
        
        column_mapping_response = await ai_service.generate_content(mapping_prompt)
        
        # Now generate the code with this mapping knowledge
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
        
        User question: "{question}"
        
        Column mapping analysis:
        {column_mapping_response}
        
        Instructions:
        1. Return EXACTLY ONE pandas operation/statement using only the 'df' DataFrame
        2. Use only pandas built-in functions and methods
        4. Focus on answering the current question directly
        5. Handle potential NULL/NaN values appropriately
        6. If aggregating, use appropriate grouping
        7. IMPORTANT: Make sure to use the EXACT column names from the DataFrame, not the user's variations
        8. If the user refers to a column in singular form but the actual column is plural (or vice versa), use the correct column name
        9. If the user refers to a column using a synonym or related term, map it to the correct actual column name
        
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
        
        # Rest of the function remains the same...
        
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