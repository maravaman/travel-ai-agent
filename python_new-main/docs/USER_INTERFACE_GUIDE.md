# 🎯 LangGraph System - User Interface Guide

## 🌟 Multiple Ways to Interact with the System

Users can interact with the LangGraph AI system through **4 different interfaces**:

---

## 1. 🖥️ **Interactive Command Line Interface**

**File:** `interactive_demo.py`

### How to Use:
```bash
python interactive_demo.py
```

### Features:
- ✅ **Real-time chat interface** 
- ✅ **Personalized queries** with user names
- ✅ **Full AI responses** from specialized agents
- ✅ **System statistics** (type 'stats')
- ✅ **Help examples** (type 'help')
- ✅ **Memory tracking** (STM + LTM counts)

### Sample Session:
```
🎯 LANGGRAPH INTERACTIVE DEMO
============================================================
Welcome! Enter your queries to get AI responses from specialized agents.

🤖 Ready for your query!
👤 Your name: Alice
💭 Your question: Find beautiful waterfalls in Norway

🔄 Processing your query...
⏰ 20:30:45 - Sending to LangGraph framework...

================================================================================
🎉 AI RESPONSE RECEIVED!
================================================================================
👤 User: Alice
❓ Question: Find beautiful waterfalls in Norway
🤖 Agent: WaterBodyAnalyzer
🔗 Agent Path: WaterBodyAnalyzer → SearchAgent
⏰ Timestamp: 2025-08-19T20:30:47.123456
📊 Response Length: 3245 characters

📝 FULL AI RESPONSE:
----------------------------------------
[Detailed AI response about Norwegian waterfalls...]
----------------------------------------

💾 Memory Status: STM=1 entries, LTM=18 entries
================================================================================
```

---

## 2. 🌐 **Web Interface (HTML/JavaScript)**

**File:** `templates/index.html`

### How to Access:
1. Start the server: `python -m uvicorn api.main:app --host 127.0.0.1 --port 8000`
2. Open browser: `http://localhost:8000`

### Features:
- ✅ **Beautiful modern UI** with responsive design
- ✅ **Real-time agent selection** and routing display
- ✅ **Example query buttons** for easy testing
- ✅ **Agent information cards** showing specializations
- ✅ **System statistics dashboard**
- ✅ **Loading animations** during AI processing
- ✅ **Full response formatting** with agent path visualization

### Interface Elements:
- **Agent Cards**: Shows 4 specialized agents (Scenic, Water, Forest, Search)
- **Query Form**: Name + Question input with example suggestions
- **Response Section**: Full AI response with agent path and metadata
- **Statistics**: Live system stats and query counts

---

## 3. 🔗 **HTTP API Endpoints**

### Primary Endpoint:
```http
POST /run_graph
Content-Type: application/json

{
    "user": "username",
    "question": "your question here"
}
```

### Response Format:
```json
{
    "user": "username",
    "user_id": 123,
    "question": "your question",
    "agent": "WaterBodyAnalyzer",
    "response": "Full AI response...",
    "context": {
        "stm": {"count": 1, "recent_interactions": {...}},
        "ltm": {"count": 18, "recent_history": [...]}
    },
    "edges_traversed": ["WaterBodyAnalyzer", "SearchAgent"],
    "timestamp": "2025-08-19T20:30:47.123456",
    "framework_version": "1.0.0"
}
```

### Additional Endpoints:
- `GET /health` - System health check
- `GET /ping` - Simple ping test
- `POST /set_stm` - Direct memory manipulation
- `GET /search_vector` - Vector similarity search

---

## 4. 🐍 **Direct Python Integration**

### Code Example:
```python
from core.langgraph_framework import langgraph_framework

# Direct framework call
result = langgraph_framework.process_request(
    user="developer",
    user_id=999,
    question="Find scenic locations in Switzerland"
)

print(f"Agent: {result['agent']}")
print(f"Response: {result['response']}")
```

---

## 🚀 **Live Demonstration**

Let me run the interactive interface now:
