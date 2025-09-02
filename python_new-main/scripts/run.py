"""
Startup script for LangGraph AI Agent System
"""
import uvicorn
import os
import sys

# Try to import decouple, fallback to os.getenv
try:
    from decouple import config
except ImportError:
    def config(key, default=None, cast=None):
        value = os.getenv(key, default)
        if cast and value is not None:
            return cast(value)
        return value

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(__file__))

if __name__ == "__main__":
    # Configuration
    host = config('APP_HOST', default='localhost')
    port = config('APP_PORT', default=8000, cast=int)
    debug = config('DEBUG', default=True, cast=bool)
    
    print(f"""
    🚀 Starting LangGraph AI Agent System
    
    📍 Server: http://{host}:{port}
    🔧 Debug Mode: {debug}
    
    🤖 Features:
    ✅ User Authentication & Registration
    ✅ Vector-based Similarity Search Agent
    ✅ Dynamic LangGraph Nodes & Edges
    ✅ Intelligent Query Orchestration
    ✅ Local Ollama Integration
    ✅ Agent-based LTM Storage
    ✅ Interactive Web UI
    
    🛠️  Prerequisites:
    - MySQL server running (for user data & LTM)
    - Redis server running (for STM)
    - Ollama server running (for AI responses)
    
    📊 Database: {config('MYSQL_DATABASE', default='langgraph_ai_system')}
    🔄 Redis: {config('REDIS_HOST', default='localhost')}:{config('REDIS_PORT', default=6379)}
    🦙 Ollama: {config('OLLAMA_BASE_URL', default='http://localhost:11434')}
    """)
    
    try:
        uvicorn.run(
            "api.main:app",
            host=host,
            port=port,
            reload=debug,
            log_level="info" if debug else "warning"
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down LangGraph AI Agent System...")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)
