import re
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def clean_code_string(code_string):
    """Remove markdown formatting and other artifacts from code strings"""
    code = re.sub(r'```python\s*', '', code_string)
    code = re.sub(r'```\s*', '', code_string)
    return code.strip()

def format_result(result):
    """Format a pandas result object for API response"""
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
    
    return result_data, result_note