# LangGraph AI Agent System

A comprehensive multi-agent AI system built with LangGraph, featuring intelligent orchestration, vector-based similarity search, and dynamic agent management.

## 🚀 Features

✅ **User Authentication & Registration** - Separate credentials for each user with session management  
✅ **Vector-based Similarity Search Agent** - Search conversation history using vector embeddings  
✅ **Dynamic LangGraph Nodes & Edges** - Update agents and connections without code changes  
✅ **Intelligent Query Orchestration** - Route queries to single or multiple agents based on complexity  
✅ **Local Ollama Integration** - Dynamic AI responses using local LLM models  
✅ **Agent-based LTM Storage** - Long-term memory grouped by agent rather than user  
✅ **Interactive Web UI** - Clean, responsive interface for agent interactions  

## 📋 Requirements

### System Prerequisites
- Python 3.8+
- MySQL Server 8.0+
- Redis Server 6.0+
- Ollama (for local LLM)

### Python Dependencies
All dependencies are listed in `requirements.txt` - install with:
```bash
pip install -r requirements.txt
```

## 🛠️ Setup Instructions

### 1. Database Setup

#### MySQL
```sql
-- Create database and run schema
CREATE DATABASE langgraph_ai_system;
-- Then run the schema from database/schema.sql
```

#### Redis
Make sure Redis server is running on default port 6379.

### 2. Ollama Setup
Install and start Ollama with a compatible model:
```bash
# Install Ollama (see https://ollama.ai)
ollama pull llama2  # or your preferred model
ollama serve
```

### 3. Environment Configuration
Copy `.env` and update with your settings:
```env
# Database Configuration
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=langgraph_ai_system

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Authentication
SECRET_KEY=your-super-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Application Settings
APP_HOST=localhost
APP_PORT=8000
DEBUG=True
```

### 4. Run the Application
```bash
python run.py
```

Visit `http://localhost:8000` to access the web interface.

## 🤖 Available Agents

1. **SearchAgent** - Vector-based similarity search of user history
2. **ScenicLocationFinder** - Discovers scenic locations and travel recommendations
3. **ForestAnalyzer** - Analyzes forest ecosystems and environmental data
4. **WaterBodyAnalyzer** - Analyzes water bodies and hydrological information
5. **OrchestratorAgent** - Intelligent query routing and multi-agent coordination

## 🎯 Client Constraints Addressed

1. ✅ **Search agent with vector similarity search** - Returns JSON responses with similarity scores
2. ✅ **Perfect nodes and edges system** - Dynamic agent configuration via database
3. ✅ **Perfect orchestrator** - Routes to single/multiple agents based on query complexity
4. ✅ **Local Ollama integration** - All responses generated locally, no external APIs
5. ✅ **LTM grouped by agent name** - Memory storage organized by agent, not user
6. ✅ **User credentials system** - Registration/login with recent usage tracking
7. ✅ **Simple effective UI** - Clean web interface with chat, auth, and usage display

## 🏗️ Architecture

### Core Components
- **FastAPI** - Web framework and API endpoints
- **LangGraph** - Agent orchestration and workflow management
- **MySQL** - User data, agent configs, and long-term memory
- **Redis** - Short-term memory and caching
- **Sentence Transformers** - Vector embeddings for similarity search
- **Ollama** - Local LLM integration

### Directory Structure
```
python_new-main/
├── api/                 # FastAPI application
├── auth/                # Authentication system
├── core/                # Core agent system
│   ├── agents/          # Agent implementations
│   └── plugins/         # Legacy agent plugins
├── database/            # Database schema and connection
├── static/              # Frontend assets (CSS/JS)
├── templates/           # HTML templates
├── .env                 # Environment configuration
├── requirements.txt     # Python dependencies
└── run.py              # Application startup script
```

## 🔧 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login  
- `GET /auth/me` - Get current user info
- `GET /auth/session` - Get user session with recent usage

### AI Chat
- `POST /ai/chat` - Main chat endpoint with orchestration
- `GET /api/ollama/status` - Check Ollama server status

### Agent Management
- `GET /api/agents` - Get all active agents
- `POST /api/agents` - Add new agent
- `POST /api/edges` - Add agent connections

### Search & Memory
- `POST /api/search` - Vector similarity search
- Various memory management endpoints for STM/LTM

## 🎮 Usage

1. **Register/Login** - Create account or sign in
2. **Chat Interface** - Ask questions in natural language
3. **Orchestration** - System automatically routes to appropriate agents
4. **History Search** - Use queries like "search my history" for similarity search
5. **Multi-agent** - Complex queries activate multiple agents automatically

### Example Queries
- "Find scenic mountain locations" → Routes to ScenicLocationFinder
- "Search my conversation history" → Routes to SearchAgent  
- "Tell me about forest ecosystems and nearby water" → Multi-agent orchestration
- "What did I ask about forests before?" → SearchAgent with forest context

## 🔍 Troubleshooting

### Common Issues
1. **Database connection failed** - Check MySQL is running and credentials are correct
2. **Redis connection failed** - Ensure Redis server is running on port 6379
3. **Ollama not available** - Start Ollama server and pull a model
4. **Agent loading errors** - Check agent configurations in database

### Logs
Check console output for detailed error messages and system status.

## 🚦 Production Deployment

For production deployment:
1. Update `.env` with production settings
2. Use proper SSL certificates
3. Configure firewall rules
4. Set up proper backup for MySQL
5. Consider using Docker containers
6. Update `SECRET_KEY` to a secure random value

## 📈 Performance Notes

- Vector similarity search may be slow on first run (model loading)
- Redis provides fast STM access
- MySQL stores persistent data efficiently
- Ollama performance depends on available hardware

---

**Developed for client requirements with all major constraints addressed effectively.**
