#!/usr/bin/env python3
"""
Knowledge Hub Worker Service

This worker service handles background tasks, AI processing, and MCP tool execution.
Currently implements a simple infinite loop for basic functionality.
"""

import os
from redis import Redis
from rq import Worker, Queue, Connection

listen = ['default']
redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
conn = Redis.from_url(redis_url)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work(with_scheduler=True)
