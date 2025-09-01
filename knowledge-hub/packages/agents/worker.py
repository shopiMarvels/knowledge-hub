#!/usr/bin/env python3
"""
Knowledge Hub Worker Service

This worker service handles background tasks, AI processing, and MCP tool execution.
Currently implements a simple infinite loop for basic functionality.
"""

import asyncio
import logging
import os
import signal
import sys
import time
from datetime import datetime
from typing import Optional

import redis
from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/worker.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/knowledge_hub")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# Global variables for graceful shutdown
shutdown_event = asyncio.Event()
running = True

class WorkerService:
    """Main worker service class"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.db_engine = None
        self.db_session = None
        self.celery_app = None
        self.task_count = 0
        
    async def initialize(self):
        """Initialize all connections and services"""
        logger.info("Initializing Worker Service...")
        
        try:
            # Initialize Redis connection
            self.redis_client = redis.from_url(REDIS_URL)
            await self._test_redis_connection()
            
            # Initialize Database connection
            self.db_engine = create_engine(DATABASE_URL)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.db_engine)
            self.db_session = SessionLocal()
            
            # Initialize Celery for task queue
            self.celery_app = Celery(
                'knowledge_hub_worker',
                broker=REDIS_URL,
                backend=REDIS_URL
            )
            
            logger.info("Worker Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Worker Service: {e}")
            raise
    
    async def _test_redis_connection(self):
        """Test Redis connection"""
        try:
            self.redis_client.ping()
            logger.info("Redis connection successful")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise
    
    async def run_worker_loop(self):
        """Main worker loop - processes tasks and maintains services"""
        logger.info("Starting worker loop...")
        
        while not shutdown_event.is_set():
            try:
                # Heartbeat - update worker status
                await self._update_worker_status()
                
                # Process any pending tasks
                await self._process_pending_tasks()
                
                # Check system health
                await self._health_check()
                
                # Sleep for a short interval
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                await asyncio.sleep(10)  # Longer sleep on error
    
    async def _update_worker_status(self):
        """Update worker status in Redis"""
        try:
            status = {
                'worker_id': 'knowledge_hub_worker_1',
                'status': 'running',
                'last_heartbeat': datetime.now().isoformat(),
                'tasks_processed': self.task_count,
                'uptime': time.time()
            }
            
            self.redis_client.hset('worker:status', mapping=status)
            
        except Exception as e:
            logger.error(f"Failed to update worker status: {e}")
    
    async def _process_pending_tasks(self):
        """Process any pending tasks from the queue"""
        try:
            # Check for tasks in Redis queue
            task = self.redis_client.lpop('tasks:pending')
            
            if task:
                logger.info(f"Processing task: {task}")
                # TODO: Implement actual task processing
                # This is where MCP tools would be invoked
                
                self.task_count += 1
                logger.info(f"Task completed. Total tasks processed: {self.task_count}")
                
        except Exception as e:
            logger.error(f"Error processing tasks: {e}")
    
    async def _health_check(self):
        """Perform health checks on all services"""
        try:
            # Check Redis
            self.redis_client.ping()
            
            # Check Database
            self.db_session.execute("SELECT 1")
            
            # TODO: Check Ollama connection
            # TODO: Check other external services
            
            # Update health status
            health_status = {
                'timestamp': datetime.now().isoformat(),
                'redis': 'healthy',
                'database': 'healthy',
                'ollama': 'unknown',  # TODO: implement check
                'overall': 'healthy'
            }
            
            self.redis_client.hset('worker:health', mapping=health_status)
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            
            # Update health status with error
            health_status = {
                'timestamp': datetime.now().isoformat(),
                'overall': 'unhealthy',
                'error': str(e)
            }
            
            try:
                self.redis_client.hset('worker:health', mapping=health_status)
            except:
                pass  # If Redis is down, we can't update status
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down Worker Service...")
        
        try:
            if self.db_session:
                self.db_session.close()
                
            if self.redis_client:
                self.redis_client.close()
                
            logger.info("Worker Service shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

# Global worker instance
worker_service = WorkerService()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    global running
    running = False
    shutdown_event.set()

async def main():
    """Main entry point"""
    logger.info("Starting Knowledge Hub Worker Service")
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize the worker service
        await worker_service.initialize()
        
        # Start the main worker loop
        await worker_service.run_worker_loop()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        # Perform graceful shutdown
        await worker_service.shutdown()
        logger.info("Worker Service stopped")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
