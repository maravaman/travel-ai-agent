#!/usr/bin/env python3
"""
FastAPI Server Startup Script
Starts the LangGraph AI Agent System server
"""

import os
import sys
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Start the FastAPI server"""
    
    print("Starting LangGraph AI Agent System...")
    print("Server will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("Main Interface: http://localhost:8000")
    print("\n" + "="*50)
    
    try:
        # Start the server
        uvicorn.run(
            "api.main:app",
            host="127.0.0.1",  # Use localhost instead of 0.0.0.0 for development
            port=8000,
            reload=True,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        logger.error(f"❌ Server failed to start: {e}")
        print(f"Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
