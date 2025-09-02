#!/usr/bin/env python3
"""
Debug test to identify and fix system issues
"""
import sys
import os
import traceback
import logging

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test all critical imports"""
    print("🔍 Testing imports...")
    
    # Core imports
    try:
        from core.memory import MemoryManager
        print("✅ MemoryManager import successful")
    except Exception as e:
        print(f"❌ MemoryManager import failed: {e}")
        traceback.print_exc()
    
    try:
        from core.langgraph_multiagent_system import LangGraphMultiAgentSystem
        print("✅ LangGraphMultiAgentSystem import successful")
    except Exception as e:
        print(f"❌ LangGraphMultiAgentSystem import failed: {e}")
        traceback.print_exc()
    
    try:
        from api.main import app
        print("✅ FastAPI app import successful")
    except Exception as e:
        print(f"❌ FastAPI app import failed: {e}")
        traceback.print_exc()
    
    try:
        from auth.auth_service import auth_service
        print("✅ Auth service import successful")
    except Exception as e:
        print(f"❌ Auth service import failed: {e}")
        traceback.print_exc()

def test_database_connections():
    """Test database connections"""
    print("\n🔍 Testing database connections...")
    
    try:
        from core.memory import MemoryManager
        memory_manager = MemoryManager()
        print("✅ MemoryManager initialization successful")
    except Exception as e:
        print(f"❌ MemoryManager initialization failed: {e}")
        traceback.print_exc()

def test_langgraph_system():
    """Test LangGraph multiagent system"""
    print("\n🔍 Testing LangGraph system...")
    
    try:
        from core.langgraph_multiagent_system import LangGraphMultiAgentSystem
        system = LangGraphMultiAgentSystem()
        print("✅ LangGraph system initialization successful")
        
        # Test basic functionality
        test_query = "What's the weather like?"
        result = system.process_request("test_user", 123, test_query)
        print(f"✅ Basic query processing successful: {result}")
        
    except Exception as e:
        print(f"❌ LangGraph system failed: {e}")
        traceback.print_exc()

def test_vector_embeddings():
    """Test vector embedding system"""
    print("\n🔍 Testing vector embeddings...")
    
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        embedding = model.encode("test sentence")
        print(f"✅ Vector embeddings working: shape {embedding.shape}")
    except Exception as e:
        print(f"❌ Vector embeddings failed: {e}")
        traceback.print_exc()

def main():
    """Run all tests"""
    print("🚀 Running comprehensive debug test...\n")
    
    test_imports()
    test_database_connections()
    test_langgraph_system()
    test_vector_embeddings()
    
    print("\n🏁 Debug test completed!")

if __name__ == "__main__":
    main()
