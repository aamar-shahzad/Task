from fastapi import FastAPI
from fastapi import FastAPI, HTTPException, Request, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from dotenv import load_dotenv

from app.api.endpoints import router
from app.services.data_service import get_dataframe

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

# Include API routes
app.include_router(router)

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