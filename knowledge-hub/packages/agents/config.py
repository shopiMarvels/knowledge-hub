"""
Worker Configuration

Configuration settings for the Knowledge Hub worker service and MCP tools.
"""

import os
from typing import Dict, Any

class WorkerConfig:
    """Configuration class for worker service"""
    
    # Database settings
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/knowledge_hub")
    
    # Redis settings
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Ollama settings
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    
    # Worker settings
    WORKER_ID = os.getenv("WORKER_ID", "knowledge_hub_worker_1")
    HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "5"))  # seconds
    TASK_TIMEOUT = int(os.getenv("TASK_TIMEOUT", "300"))  # seconds
    
    # Logging settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "/app/logs/worker.log")
    
    # MCP Tools settings
    MCP_TOOLS_BASE_PATH = os.getenv("MCP_TOOLS_BASE_PATH", "/app/data")
    
    # OpenAI settings (for AI tasks)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            attr: getattr(cls, attr) 
            for attr in dir(cls) 
            if not attr.startswith('_') and not callable(getattr(cls, attr))
        }
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration settings"""
        required_settings = [
            'DATABASE_URL',
            'REDIS_URL',
            'OLLAMA_URL'
        ]
        
        for setting in required_settings:
            if not getattr(cls, setting):
                raise ValueError(f"Required setting {setting} is not configured")
        
        return True
