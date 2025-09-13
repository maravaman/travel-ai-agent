"""
Dynamic Agent Management API Endpoints
Provides REST API for managing dynamically loaded agents
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from core.dynamic_agent_loader import get_dynamic_agent_loader
from core.memory import MemoryManager

logger = logging.getLogger(__name__)

# Request/Response models
class AgentExecutionRequest(BaseModel):
    agent_name: str
    query: str
    user_id: int = 0

class MultiAgentExecutionRequest(BaseModel):
    agent_names: List[str]
    query: str
    user_id: int = 0

class CapabilityExecutionRequest(BaseModel):
    capability: str
    query: str
    user_id: int = 0

class KeywordExecutionRequest(BaseModel):
    query: str
    user_id: int = 0
    max_agents: int = 3

class AgentConfigRequest(BaseModel):
    name: str
    file_path: str
    class_name: str
    enabled: bool = True
    priority: int = 2
    entry_point: str = "main"
    description: str = ""
    capabilities: List[str] = []
    keywords: List[str] = []
    execution_settings: Dict[str, Any] = {}

class AgentExecutionResponse(BaseModel):
    success: bool
    agent: str
    response: str
    processing_time: float
    error: Optional[str] = None

class MultiAgentExecutionResponse(BaseModel):
    query: str
    user_id: int
    agents_executed: List[str]
    successful_executions: int
    total_processing_time: float
    individual_results: List[Dict[str, Any]]
    timestamp: str

class AgentInfoResponse(BaseModel):
    name: str
    class_name: str
    description: str
    capabilities: List[str]
    keywords: List[str]
    file_path: Optional[str]
    execution_count: int
    success_rate: float
    avg_processing_time: float
    enabled: bool
    priority: int

class LoaderStatsResponse(BaseModel):
    total_agents_loaded: int
    total_executions: int
    successful_executions: int
    success_rate: float
    agent_execution_counts: Dict[str, int]
    loaded_agents: List[str]
    config_file: str

# Router
router = APIRouter(prefix="/dynamic", tags=["dynamic_agents"])

def get_loader():
    """Dependency to get dynamic agent loader"""
    memory_manager = MemoryManager()
    return get_dynamic_agent_loader(memory_manager)

@router.post("/execute", response_model=AgentExecutionResponse)
async def execute_agent(
    request: AgentExecutionRequest,
    loader = Depends(get_loader)
):
    """Execute specific agent with query"""
    try:
        result = loader.execute_agent(
            agent_name=request.agent_name,
            query=request.query,
            user_id=request.user_id
        )
        
        return AgentExecutionResponse(
            success=result["success"],
            agent=result["agent"],
            response=result.get("response", ""),
            processing_time=result.get("processing_time", 0),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Agent execution error: {e}")
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")

@router.post("/execute/multiple", response_model=MultiAgentExecutionResponse)
async def execute_multiple_agents(
    request: MultiAgentExecutionRequest,
    loader = Depends(get_loader)
):
    """Execute multiple agents with same query"""
    try:
        result = loader.execute_multiple_agents(
            agent_names=request.agent_names,
            query=request.query,
            user_id=request.user_id
        )
        
        return MultiAgentExecutionResponse(**result)
        
    except Exception as e:
        logger.error(f"Multi-agent execution error: {e}")
        raise HTTPException(status_code=500, detail=f"Multi-agent execution failed: {str(e)}")

@router.post("/execute/capability", response_model=MultiAgentExecutionResponse)
async def execute_by_capability(
    request: CapabilityExecutionRequest,
    loader = Depends(get_loader)
):
    """Execute agents that have specific capability"""
    try:
        result = loader.execute_by_capability(
            capability=request.capability,
            query=request.query,
            user_id=request.user_id
        )
        
        if not result.get("successful_executions"):
            raise HTTPException(status_code=404, detail=f"No agents found with capability: {request.capability}")
        
        return MultiAgentExecutionResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Capability execution error: {e}")
        raise HTTPException(status_code=500, detail=f"Capability execution failed: {str(e)}")

@router.post("/execute/keywords", response_model=MultiAgentExecutionResponse)
async def execute_by_keywords(
    request: KeywordExecutionRequest,
    loader = Depends(get_loader)
):
    """Execute agents based on keyword matching"""
    try:
        result = loader.execute_by_keywords(
            query=request.query,
            user_id=request.user_id,
            max_agents=request.max_agents
        )
        
        return MultiAgentExecutionResponse(**result)
        
    except Exception as e:
        logger.error(f"Keyword execution error: {e}")
        raise HTTPException(status_code=500, detail=f"Keyword execution failed: {str(e)}")

@router.get("/agents", response_model=List[str])
async def get_agent_names(loader = Depends(get_loader)):
    """Get list of all loaded agent names"""
    return loader.get_agent_names()

@router.get("/agents/{agent_name}", response_model=AgentInfoResponse)
async def get_agent_info(
    agent_name: str,
    loader = Depends(get_loader)
):
    """Get detailed information about specific agent"""
    info = loader.get_agent_info(agent_name)
    if not info:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
    
    return AgentInfoResponse(**info)

@router.get("/capabilities/{capability}")
async def get_agents_by_capability(
    capability: str,
    loader = Depends(get_loader)
):
    """Get agents that have specific capability"""
    agents = loader.get_agents_by_capability(capability)
    return {
        "capability": capability,
        "agents": agents,
        "count": len(agents)
    }

@router.post("/agents")
async def add_agent(
    agent_config: AgentConfigRequest,
    loader = Depends(get_loader)
):
    """Add new agent dynamically"""
    try:
        config_dict = agent_config.dict()
        success = loader.add_agent_dynamically(config_dict)
        
        if success:
            return {"message": f"Agent {agent_config.name} added successfully"}
        else:
            raise HTTPException(status_code=400, detail=f"Failed to add agent {agent_config.name}")
            
    except Exception as e:
        logger.error(f"Error adding agent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add agent: {str(e)}")

@router.delete("/agents/{agent_name}")
async def remove_agent(
    agent_name: str,
    loader = Depends(get_loader)
):
    """Remove agent"""
    try:
        success = loader.remove_agent(agent_name)
        
        if success:
            return {"message": f"Agent {agent_name} removed successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
            
    except Exception as e:
        logger.error(f"Error removing agent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove agent: {str(e)}")

@router.post("/agents/{agent_name}/reload")
async def reload_agent(
    agent_name: str,
    loader = Depends(get_loader)
):
    """Reload specific agent"""
    try:
        success = loader.reload_agent(agent_name)
        
        if success:
            return {"message": f"Agent {agent_name} reloaded successfully"}
        else:
            raise HTTPException(status_code=400, detail=f"Failed to reload agent {agent_name}")
            
    except Exception as e:
        logger.error(f"Error reloading agent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reload agent: {str(e)}")

@router.post("/reload")
async def reload_all_agents(loader = Depends(get_loader)):
    """Reload all agents"""
    try:
        results = loader.reload_all_agents()
        successful_reloads = sum(1 for success in results.values() if success)
        
        return {
            "message": f"Reloaded {successful_reloads}/{len(results)} agents successfully",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error reloading all agents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reload agents: {str(e)}")

@router.get("/stats", response_model=LoaderStatsResponse)
async def get_loader_statistics(loader = Depends(get_loader)):
    """Get dynamic agent loader statistics"""
    try:
        stats = loader.get_agent_statistics()
        return LoaderStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@router.get("/execution-log")
async def get_execution_log(
    limit: int = 50,
    loader = Depends(get_loader)
):
    """Get execution log"""
    try:
        log = loader.get_execution_log()
        return {
            "total_entries": len(log),
            "entries": log[-limit:] if limit > 0 else log
        }
        
    except Exception as e:
        logger.error(f"Error getting execution log: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get execution log: {str(e)}")

@router.delete("/execution-log")
async def clear_execution_log(loader = Depends(get_loader)):
    """Clear execution log"""
    try:
        loader.clear_execution_log()
        return {"message": "Execution log cleared successfully"}
        
    except Exception as e:
        logger.error(f"Error clearing execution log: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear execution log: {str(e)}")

@router.get("/validate")
async def validate_configuration(loader = Depends(get_loader)):
    """Validate current agent configuration"""
    try:
        validation = loader.validate_configuration()
        return validation
        
    except Exception as e:
        logger.error(f"Error validating configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate configuration: {str(e)}")

@router.get("/agents/{agent_name}/functions")
async def get_agent_functions(
    agent_name: str,
    loader = Depends(get_loader)
):
    """Get available functions in agent module"""
    try:
        functions = loader.list_available_functions(agent_name)
        return {
            "agent": agent_name,
            "functions": functions,
            "count": len(functions)
        }
        
    except Exception as e:
        logger.error(f"Error getting agent functions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent functions: {str(e)}")

@router.post("/agents/{agent_name}/execute-function")
async def execute_agent_function(
    agent_name: str,
    function_data: Dict[str, Any] = Body(...),
    loader = Depends(get_loader)
):
    """Execute specific function in agent module"""
    try:
        function_name = function_data.get("function_name")
        args = function_data.get("args", [])
        kwargs = function_data.get("kwargs", {})
        
        if not function_name:
            raise HTTPException(status_code=400, detail="function_name is required")
        
        result = loader.execute_agent_function(agent_name, function_name, *args, **kwargs)
        
        return {
            "agent": agent_name,
            "function": function_name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error executing agent function: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute function: {str(e)}")

# Export router
__all__ = ['router']