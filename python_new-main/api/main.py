# main.py

import sys
import os
# Add the parent directory to Python path to enable imports from core, auth, database modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, HTTPException, Body, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict
import json, os
import logging
from datetime import datetime

# Import required modules for vector search
try:
    from langchain.schema import Document
    from langchain_community.embeddings import HuggingFaceEmbeddings
except ImportError:
    # Fallback if langchain modules are not available
    Document = None
    HuggingFaceEmbeddings = None

from core.memory import MemoryManager
from core.orchestrator import run_dynamic_graph
from core.ollama_client import ollama_client

# Optional imports with fallbacks
try:
    from core.dynamic_agents import dynamic_agent_manager
except ImportError:
    dynamic_agent_manager = None

try:
    from auth.auth_endpoints import router as auth_router, get_current_user
except ImportError:
    auth_router = None
    get_current_user = None

try:
    from database.connection import get_mysql_conn
except ImportError:
    get_mysql_conn = None

# Import travel endpoints
try:
    from api.travel_endpoints import router as travel_router
except ImportError:
    travel_router = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ FastAPI Setup
app = FastAPI(
    title="Travel Assistant - LangGraph Multi-Agent System",
    description="Intelligent travel planning assistant with specialized agents",
    version="1.0.0"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Include authentication router (if available)
if auth_router:
    app.include_router(auth_router)

# Include travel router (if available)
if travel_router:
    app.include_router(travel_router)

# ✅ Globalsh
memory_manager = MemoryManager()
AGENT_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../core/agents.json"))

# ✅ Schemas
class GraphInput(BaseModel):
    user: str
    question: str

class STMRequest(BaseModel):
    user_id: str
    agent_id: str
    value: str
    expiry_hours: int = 1

# ✅ Health
@app.get("/ping")
def ping():
    return {"pong": True}

@app.get("/health")
def health():
    return {"status": "Server is running ✅"}

# ✅ Agent API
@app.get("/agents")
def get_agents():
    try:
        return {
            "agents": dynamic_agent_manager.get_all_agents(),
            "edges": dynamic_agent_manager.get_graph_edges()
        }
    except Exception as e:
        return {"agents": {}, "edges": {}}

@app.post("/register_agents")
def register_agents(payload: dict = Body(...)):
    try:
        data = {"agents": [], "edges": {}, "entry_point": ""}
        if os.path.exists(AGENT_FILE):
            with open(AGENT_FILE, "r") as f:
                data = json.load(f)

        existing_agents = {a["id"]: a for a in data.get("agents", [])}
        existing_edges = data.get("edges", {})
        entry_point = payload.get("entry_point", data.get("entry_point", ""))

        for agent in payload.get("agents", []):
            if agent["id"] not in existing_agents:
                existing_agents[agent["id"]] = agent

        for src, targets in payload.get("edges", {}).items():
            existing_edges[src] = list(set(existing_edges.get(src, []) + targets))

        updated = {
            "agents": list(existing_agents.values()),
            "edges": existing_edges,
            "entry_point": entry_point
        }

        with open(AGENT_FILE, "w") as f:
            json.dump(updated, f, indent=2)

        return {"message": "Updated", "data": updated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ STM & LTM APIs
@app.post("/set_stm")
def set_stm(req: STMRequest):
    memory_manager.set_stm(req.user_id, req.agent_id, req.value, req.expiry_hours * 3600)
    return {"message": "STM saved"}

@app.get("/get_stm/{user_id}/{agent_id}")
def get_stm(user_id: str, agent_id: str):
    return {"value": memory_manager.get_stm(user_id, agent_id)}

@app.post("/memory/ltm/{user_id}/{agent_id}")
def set_ltm(user_id: str, agent_id: str, value: str = Body(...)):
    memory_manager.set_ltm(user_id, agent_id, value)
    return {"message": "LTM saved"}

@app.get("/memory/ltm/{user_id}/{agent_id}")
def get_ltm(user_id: str, agent_id: str):
    return memory_manager.get_ltm_by_agent(user_id, agent_id)

# ✅ Vector Search (Semantic)
@app.get("/search_vector")
def search_vector(query: str, user_id: str, agent_id: str = None, hours: int = 1, days: int = 1):
    try:
        stm_texts = memory_manager.get_recent_stm(user_id, agent_id, hours)
        ltm_entries = memory_manager.get_recent_ltm(user_id, agent_id, days)
        ltm_texts = [e["value"] for e in ltm_entries if "value" in e]
        all_texts = stm_texts + ltm_texts

        result_texts = []
        
        # Check if langchain dependencies are available
        if Document and HuggingFaceEmbeddings:
            try:
                docs = [Document(page_content=text) for text in all_texts if isinstance(text, str)]
                
                if docs:
                    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
                    from langchain_community.vectorstores import FAISS
                    vector_db = FAISS.from_documents(docs, embedding=embeddings)
                    results = vector_db.similarity_search(query, k=5)
                    result_texts = [doc.page_content for doc in results]
            except Exception as vector_error:
                logger.warning(f"Vector search failed, using text matching fallback: {vector_error}")
                # Simple text matching fallback
                query_lower = query.lower()
                result_texts = [text for text in all_texts if query_lower in text.lower()][:5]
        else:
            # Simple text matching fallback when langchain is not available
            query_lower = query.lower()
            result_texts = [text for text in all_texts if query_lower in text.lower()][:5]

        return {
            "stm": stm_texts,
            "ltm": ltm_texts,
            "results": result_texts
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ New Chat Input Schema
class ChatInput(BaseModel):
    user: str
    user_id: int
    question: str

# ✅ Main UI Route
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # Serve the new travel interface
    return templates.TemplateResponse("travel_interface.html", {"request": request})

# ✅ Simple Interface Route
@app.get("/simple", response_class=HTMLResponse)
async def simple_interface(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ✅ Legacy Interface Route
@app.get("/legacy", response_class=HTMLResponse)
async def legacy_interface(request: Request):
    return templates.TemplateResponse("auth_interface.html", {"request": request})

# ✅ Updated run_graph endpoint with LangGraph Multiagent System
@app.post("/run_graph")
async def run_graph_authenticated(payload: GraphInput, current_user: dict = Depends(get_current_user) if get_current_user else None):
    """Run Travel Assistant with specialized travel agents"""
    try:
        # Import the travel-enhanced multiagent system
        from core.langgraph_multiagent_system import langgraph_multiagent_system
        
        # Use authenticated user ID if available, otherwise generate temporary ID
        if current_user:
            user_id = current_user['id']
            username = current_user['username']
        else:
            user_id = int(datetime.now().timestamp())
            username = payload.user
        
        start_time = datetime.now()
        
        # Process request through Travel Assistant System
        result = langgraph_multiagent_system.process_request(
            user=username,
            user_id=user_id,
            question=payload.question
        )
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Log query for authenticated users
        if current_user:
            try:
                from auth.auth_service import auth_service
                logger.info(f"🔄 Processing query for user {current_user['id']} ({current_user['username']}): {payload.question[:50]}...")
                auth_service.log_user_query(
                    user_id=current_user['id'],
                    session_id="web_session",  # In real app, track session properly
                    question=payload.question,
                    agent_used=result.get('agent', 'Unknown'),
                    response_text=result.get('response', ''),
                    edges_traversed=result.get('edges_traversed', []),
                    processing_time=processing_time
                )
                logger.info(f"✅ Query logged for user {current_user['id']}")
            except Exception as log_error:
                logger.warning(f"Failed to log query: {log_error}")
        
        return result
        
    except Exception as e:
        logger.error(f"Travel assistant execution error: {e}")
        raise HTTPException(status_code=500, detail=f"Travel assistant execution failed: {str(e)}")

# ✅ Legacy run_graph endpoint without authentication (for backward compatibility)
@app.post("/run_graph_legacy")
async def run_graph_legacy(payload: GraphInput):
    """Legacy run_graph endpoint using travel assistant system"""
    try:
        from core.langgraph_multiagent_system import langgraph_multiagent_system
        
        result = langgraph_multiagent_system.process_request(
            user=payload.user,
            user_id=int(datetime.now().timestamp()),
            question=payload.question
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Travel assistant execution error: {e}")
        raise HTTPException(status_code=500, detail=f"Travel assistant execution failed: {str(e)}")

# async def ai_chat(
#     input_data: ChatInput,
#     current_user: dict = Depends(get_current_user)
# ):
#     """Main chat endpoint with intelligent agent orchestration"""
#     try:
#         logger.info(f"Processing chat request from user {input_data.user}: {input_data.question}")
#         
#         # Run dynamic graph with orchestration
#         result = run_dynamic_graph(
#             user=input_data.user,
#             user_id=input_data.user_id,
#             question=input_data.question
#         )
#         
#         return result
#         
#     except Exception as e:
#         logger.error(f"Chat error: {e}")
#         raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

# ✅ Ollama Status Check
@app.get("/api/ollama/status")
async def ollama_status():
    """Check Ollama server status"""
    try:
        available = ollama_client.is_available()
        models = ollama_client.list_models() if available else []
        
        return {
            "available": available,
            "models": models,
            "base_url": ollama_client.base_url
        }
    except Exception as e:
        logger.error(f"Ollama status check failed: {e}")
        return {
            "available": False,
            "error": str(e),
            "base_url": ollama_client.base_url
        }

# ✅ Dynamic Agent Management APIs (temporarily disabled due to auth dependency)
# @app.get("/api/agents")
# async def get_dynamic_agents(
#     current_user: dict = Depends(get_current_user)
# ):
#     """Get all active agents"""
#     return {
#         "agents": dynamic_agent_manager.get_all_agents(),
#         "edges": dynamic_agent_manager.get_graph_edges()
#     }

# @app.post("/api/agents")
# async def add_agent(
#     agent_data: dict = Body(...),
#     current_user: dict = Depends(get_current_user)
# ):
#     """Add new agent configuration"""
#     try:
#         success = dynamic_agent_manager.add_agent(
#             agent_name=agent_data["name"],
#             module_path=agent_data["module_path"],
#             description=agent_data.get("description", ""),
#             capabilities=agent_data.get("capabilities", []),
#             dependencies=agent_data.get("dependencies", [])
#         )
#         
#         if success:
#             return {"message": "Agent added successfully"}
#         else:
#             raise HTTPException(status_code=400, detail="Failed to add agent")
#             
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/api/edges")
# async def add_edge(
#     edge_data: dict = Body(...),
#     current_user: dict = Depends(get_current_user)
# ):
#     """Add new graph edge"""
#     try:
#         success = dynamic_agent_manager.add_edge(
#             source_agent=edge_data["source"],
#             target_agent=edge_data["target"],
#             condition=edge_data.get("condition"),
#             weight=edge_data.get("weight", 1)
#         )
#         
#         if success:
#             return {"message": "Edge added successfully"}
#         else:
#             raise HTTPException(status_code=400, detail="Failed to add edge")
#             
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# ✅ Vector Search API (temporarily disabled due to auth dependency)
# @app.post("/api/search")
# async def vector_search(
#     search_data: dict = Body(...),
#     current_user: dict = Depends(get_current_user)
# ):
#     """Perform vector similarity search"""
#     try:
#         query = search_data["query"]
#         user_id = current_user["id"]
#         agent_name = search_data.get("agent_name")
#         
#         results = memory_manager.get_search_history_json(
#             query=query,
#             user_id=user_id,
#             agent_name=agent_name
#         )
#         
#         return results
#         
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# Note: run_graph endpoint already implemented above with authentication support

# ✅ Server startup
if __name__ == "__main__":
    import uvicorn
    import logging
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Starting LangGraph AI Agent System...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🎯 Main Interface: http://localhost:8000")
    print("\n" + "="*50)
    
    try:
        uvicorn.run(
            "api.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
