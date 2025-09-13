# 🚀 Dynamic Agent Loading with Reflection - Complete Guide

## Overview

This system implements dynamic loading and execution of Python agent files using JSON configuration and Python reflection. You can add, remove, and execute agents at runtime without modifying core system code.

## 🎯 Key Features

### ✅ JSON-Based Configuration
- All agent configurations stored in `core/dynamic_agents.json`
- No hardcoded agent references in code
- Easy to add/remove agents by editing JSON

### ✅ Reflection-Based Loading
- Uses `importlib` to dynamically load .py files
- Automatic class discovery using `inspect` module
- Runtime module execution and function calling

### ✅ Intelligent Agent Routing
- Keyword-based agent selection
- Capability-based execution
- Priority-based routing
- Multi-agent coordination

### ✅ Hot Reload Support
- Reload agents without system restart
- Update configurations on the fly
- Development-friendly workflow

## 🏗️ Architecture

```
JSON Config → Reflection Loader → Agent Instances → Execution Engine
     ↓              ↓                    ↓              ↓
dynamic_agents.json → importlib → BaseAgent Classes → Query Processing
```

### Core Components

1. **DynamicAgentLoader** (`core/dynamic_agent_loader.py`)
   - Main loader class using reflection
   - Handles JSON configuration parsing
   - Manages agent lifecycle

2. **ReflectionUtils** (`core/reflection_utils.py`)
   - Utility functions for reflection operations
   - Module inspection and validation
   - Safe function execution

3. **Configuration** (`core/dynamic_agents.json`)
   - JSON-based agent definitions
   - Execution settings and routing rules
   - Capability and keyword mappings

## 📋 JSON Configuration Structure

### Agent Configuration
```json
{
  "name": "AgentName",
  "file_path": "agents/agent_file.py",
  "class_name": "AgentClassName",
  "enabled": true,
  "priority": 1,
  "entry_point": "main",
  "description": "What the agent does",
  "capabilities": ["capability1", "capability2"],
  "keywords": ["keyword1", "keyword2"],
  "execution_settings": {
    "timeout_seconds": 30,
    "temperature": 0.7,
    "max_tokens": 1500
  }
}
```

### Complete Configuration Example
```json
{
  "version": "1.0.0",
  "description": "Dynamic Agent Configuration",
  "agents": [
    {
      "name": "TextTripAnalyzer",
      "file_path": "agents/text_trip_analyzer.py",
      "class_name": "TextTripAnalyzerAgent",
      "enabled": true,
      "priority": 1,
      "entry_point": "main",
      "description": "Analyzes trip planning text",
      "capabilities": ["text_analysis", "goal_extraction"],
      "keywords": ["plan", "trip", "travel", "goal"],
      "execution_settings": {
        "timeout_seconds": 30,
        "temperature": 0.3,
        "max_tokens": 2000
      }
    }
  ],
  "execution_settings": {
    "max_concurrent_agents": 3,
    "timeout_seconds": 30,
    "retry_attempts": 2,
    "enable_logging": true
  },
  "routing_rules": {
    "default_agent": "TextTripAnalyzer",
    "fallback_agent": "TripSummarySynth",
    "multi_agent_threshold": 2
  }
}
```

## 🚀 Usage Examples

### Basic Agent Loading
```python
from core.dynamic_agent_loader import DynamicAgentLoader
from core.memory import MemoryManager

# Initialize loader
memory_manager = MemoryManager()
loader = DynamicAgentLoader(
    config_file="core/dynamic_agents.json",
    memory_manager=memory_manager
)

# Get loaded agents
agents = loader.get_all_agents()
print(f"Loaded {len(agents)} agents")
```

### Execute Agent by Keywords
```python
# Query automatically routed to best agents
result = loader.execute_by_keywords(
    query="I'm planning a trip to Japan and feeling overwhelmed",
    user_id=1001,
    max_agents=3
)

print(f"Executed {result['successful_executions']} agents")
for agent_result in result["individual_results"]:
    if agent_result["success"]:
        print(f"{agent_result['agent']}: {agent_result['response'][:100]}...")
```

### Execute Specific Agent
```python
# Execute specific agent directly
result = loader.execute_agent(
    agent_name="TripMoodDetector",
    query="I'm excited about my upcoming vacation!",
    user_id=1002
)

if result["success"]:
    print(f"Response: {result['response']}")
    print(f"Processing time: {result['processing_time']:.2f}s")
```

### Execute by Capability
```python
# Execute all agents with specific capability
result = loader.execute_by_capability(
    capability="stress_relief",
    query="I'm stressed about travel planning",
    user_id=1003
)

print(f"Agents with stress_relief capability executed")
```

### Hot Reload Agents
```python
# Reload specific agent
success = loader.reload_agent("TripMoodDetector")
print(f"Reload successful: {success}")

# Reload all agents
results = loader.reload_all_agents()
successful = sum(1 for s in results.values() if s)
print(f"Reloaded {successful}/{len(results)} agents")
```

### Add Agent Dynamically
```python
new_agent_config = {
    "name": "NewTravelAgent",
    "file_path": "agents/new_travel_agent.py",
    "class_name": "NewTravelAgentClass",
    "enabled": True,
    "priority": 2,
    "description": "New travel agent",
    "capabilities": ["new_capability"],
    "keywords": ["new", "travel"]
}

success = loader.add_agent_dynamically(new_agent_config)
print(f"Agent added: {success}")
```

## 🔧 Agent File Structure

### Required Agent Structure
Each agent .py file must:

1. **Inherit from BaseAgent**
```python
from core.base_agent import BaseAgent, GraphState

class YourAgentClass(BaseAgent):
    def __init__(self, memory_manager=None, name: str = "YourAgent"):
        super().__init__(memory_manager, name)
        # Agent initialization
    
    def process(self, state: GraphState) -> GraphState:
        # Main processing logic
        pass
    
    def get_capabilities(self) -> List[str]:
        # Return agent capabilities
        pass
```

2. **Optional Entry Point Function**
```python
def main(*args, **kwargs):
    """Entry point function for direct execution"""
    print("Agent executed directly!")
    return "Success"
```

### Example Agent File
```python
# agents/example_agent.py
from typing import Dict, Any, List
from core.base_agent import BaseAgent, GraphState

class ExampleAgent(BaseAgent):
    def __init__(self, memory_manager=None, name: str = "ExampleAgent"):
        super().__init__(memory_manager, name)
        self._capabilities = ["example_capability"]
        self._description = "Example agent for demonstration"
    
    @property
    def keywords(self) -> List[str]:
        return ["example", "demo", "test"]
    
    def process(self, state: GraphState) -> GraphState:
        query = state.get("question", "")
        user_id = state.get("user_id", 0)
        
        # Your agent logic here
        response = f"Example agent processed: {query}"
        
        return self.format_state_response(state, response)
    
    def get_capabilities(self) -> List[str]:
        return self._capabilities

def main():
    """Entry point for direct execution"""
    print("Example agent main function executed!")
    return "Example agent ready"
```

## 🌐 REST API Endpoints

### Agent Execution
```http
POST /dynamic/execute
{
  "agent_name": "TripMoodDetector",
  "query": "I'm excited about my trip!",
  "user_id": 1001
}
```

### Multi-Agent Execution
```http
POST /dynamic/execute/multiple
{
  "agent_names": ["TripMoodDetector", "TripBehaviorGuide"],
  "query": "I need travel planning help",
  "user_id": 1001
}
```

### Capability-Based Execution
```http
POST /dynamic/execute/capability
{
  "capability": "stress_relief",
  "query": "I'm stressed about planning",
  "user_id": 1001
}
```

### Keyword-Based Execution
```http
POST /dynamic/execute/keywords
{
  "query": "I'm planning a trip and feeling overwhelmed",
  "user_id": 1001,
  "max_agents": 3
}
```

### Agent Management
```http
GET /dynamic/agents                    # List all agents
GET /dynamic/agents/{agent_name}       # Get agent info
POST /dynamic/agents                   # Add new agent
DELETE /dynamic/agents/{agent_name}    # Remove agent
POST /dynamic/agents/{agent_name}/reload # Reload agent
POST /dynamic/reload                   # Reload all agents
```

### Statistics and Monitoring
```http
GET /dynamic/stats                     # Get loader statistics
GET /dynamic/execution-log             # Get execution log
DELETE /dynamic/execution-log          # Clear execution log
GET /dynamic/validate                  # Validate configuration
```

## 🧪 Testing and Validation

### Run Comprehensive Tests
```bash
# Test dynamic loading system
python scripts/test_dynamic_loader.py

# Interactive demo
python scripts/demo_dynamic_agents.py
```

### Validation Features
- **File Existence**: Checks if agent files exist
- **Class Inheritance**: Validates BaseAgent inheritance
- **Entry Points**: Verifies entry point functions exist
- **Configuration**: Validates JSON structure
- **Execution**: Tests agent execution capabilities

## 🔄 Hot Reload Workflow

### Development Workflow
1. **Edit Agent File**: Modify your .py agent file
2. **Reload Agent**: Call `loader.reload_agent("AgentName")`
3. **Test Changes**: Execute queries to test modifications
4. **No Restart**: System continues running with updated agent

### API Hot Reload
```bash
# Reload specific agent
curl -X POST http://localhost:8000/dynamic/agents/TripMoodDetector/reload

# Reload all agents
curl -X POST http://localhost:8000/dynamic/reload
```

## 📊 Monitoring and Analytics

### Execution Statistics
- Total agents loaded
- Execution counts per agent
- Success rates
- Average processing times
- Error tracking

### Execution Log
- Complete audit trail
- Query and response tracking
- Performance metrics
- Error details

## 🛠️ Advanced Features

### Custom Entry Points
```python
# In your agent file
def custom_entry_point(param1, param2):
    """Custom entry point function"""
    return f"Custom execution with {param1} and {param2}"

# Execute via API
POST /dynamic/agents/YourAgent/execute-function
{
  "function_name": "custom_entry_point",
  "args": ["value1", "value2"],
  "kwargs": {}
}
```

### Function Discovery
```python
# List all functions in agent module
functions = loader.list_available_functions("TripMoodDetector")
print(f"Available functions: {functions}")

# Execute specific function
result = loader.execute_agent_function(
    "TripMoodDetector", 
    "analyze_mood", 
    "I'm excited about travel!"
)
```

### Configuration Validation
```python
# Validate current configuration
validation = loader.validate_configuration()

if validation["valid"]:
    print("✅ Configuration is valid")
else:
    print("❌ Configuration has issues:")
    for error in validation["errors"]:
        print(f"   • {error}")
```

## 🎉 Benefits

### For Developers
- **No Code Changes**: Add agents by editing JSON only
- **Hot Reload**: Test changes without restart
- **Reflection Power**: Full Python introspection capabilities
- **Error Safety**: Comprehensive error handling

### For System Administrators
- **Runtime Management**: Add/remove agents while system runs
- **Configuration Control**: Centralized JSON configuration
- **Monitoring**: Complete execution tracking
- **Validation**: Built-in configuration validation

### For Users
- **Seamless Experience**: Agents work transparently
- **Better Routing**: Intelligent agent selection
- **Faster Responses**: Optimized execution paths
- **Reliability**: Graceful error handling

## 🔧 Troubleshooting

### Common Issues

#### Agent Not Loading
```python
# Check if file exists
validation = loader.validate_configuration()
print(validation["agent_validations"]["YourAgent"])

# Check class inheritance
from core.reflection_utils import ReflectionUtils
module = ReflectionUtils.load_module_from_file("agents/your_agent.py")
classes = ReflectionUtils.find_classes_in_module(module, BaseAgent)
```

#### Execution Failures
```python
# Check execution log
log = loader.get_execution_log()
failed_executions = [e for e in log if not e["success"]]
for failure in failed_executions:
    print(f"Failed: {failure['agent']} - {failure.get('error')}")
```

#### Configuration Errors
```python
# Validate configuration
validation = loader.validate_configuration()
if validation["errors"]:
    for error in validation["errors"]:
        print(f"Error: {error}")
```

## 📚 Complete Example

### 1. Create Agent File
```python
# agents/my_custom_agent.py
from core.base_agent import BaseAgent, GraphState
from typing import List

class MyCustomAgent(BaseAgent):
    def __init__(self, memory_manager=None, name: str = "MyCustomAgent"):
        super().__init__(memory_manager, name)
        self._capabilities = ["custom_analysis"]
        self._description = "My custom travel agent"
    
    @property
    def keywords(self) -> List[str]:
        return ["custom", "special", "unique"]
    
    def process(self, state: GraphState) -> GraphState:
        query = state.get("question", "")
        response = f"Custom agent response to: {query}"
        return self.format_state_response(state, response)
    
    def get_capabilities(self) -> List[str]:
        return self._capabilities

def main():
    print("My custom agent is ready!")
    return "Custom agent initialized"
```

### 2. Add to JSON Configuration
```json
{
  "name": "MyCustomAgent",
  "file_path": "agents/my_custom_agent.py",
  "class_name": "MyCustomAgent",
  "enabled": true,
  "priority": 2,
  "entry_point": "main",
  "description": "My custom travel agent",
  "capabilities": ["custom_analysis"],
  "keywords": ["custom", "special", "unique"],
  "execution_settings": {
    "timeout_seconds": 25,
    "temperature": 0.6,
    "max_tokens": 1200
  }
}
```

### 3. Load and Execute
```python
# Load agent dynamically
loader = DynamicAgentLoader()

# Execute with query
result = loader.execute_by_keywords(
    "I need custom help with my special travel needs",
    user_id=1001
)

# Agent automatically selected based on keywords
print(f"Executed: {result['agents_executed']}")
```

## 🎯 Summary

This dynamic agent loading system provides:

- ✅ **Zero-Code Agent Addition**: Just edit JSON and add .py file
- ✅ **Reflection-Based Loading**: Full Python introspection power
- ✅ **Hot Reload**: Update agents without restart
- ✅ **Intelligent Routing**: Automatic agent selection
- ✅ **REST API**: Complete HTTP interface
- ✅ **Monitoring**: Execution tracking and analytics
- ✅ **Validation**: Configuration and runtime validation
- ✅ **Error Safety**: Comprehensive error handling

Perfect for building scalable, maintainable multi-agent systems that can evolve at runtime!