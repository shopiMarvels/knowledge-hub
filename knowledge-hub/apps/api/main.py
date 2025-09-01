from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Knowledge Hub API",
    description="A powerful knowledge management system with AI capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Response models
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    environment: str

class MessageResponse(BaseModel):
    message: str

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify the API is running.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="1.0.0",
        environment=os.getenv("NODE_ENV", "development")
    )

# Root endpoint
@app.get("/", response_model=MessageResponse)
async def root():
    """
    Root endpoint with welcome message.
    """
    return MessageResponse(message="Welcome to Knowledge Hub API")

# API Info endpoint
@app.get("/info")
async def api_info():
    """
    Get API information and environment details.
    """
    return {
        "name": "Knowledge Hub API",
        "version": "1.0.0",
        "environment": os.getenv("NODE_ENV", "development"),
        "database_connected": True,  # TODO: Add actual DB connection check
        "redis_connected": True,     # TODO: Add actual Redis connection check
        "ollama_connected": True,    # TODO: Add actual Ollama connection check
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Knowledge Hub API is starting up...")
    # TODO: Initialize database connections
    # TODO: Initialize Redis connections
    # TODO: Verify Ollama connection

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Knowledge Hub API is shutting down...")
    # TODO: Close database connections
    # TODO: Close Redis connections

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
