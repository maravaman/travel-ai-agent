# 🚀 LangGraph Multi-Agent AI System v2.0

[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-green.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-Production%20Ready-brightgreen.svg)]()
[![Test Coverage](https://img.shields.io/badge/coverage-85%25+-green.svg)]()

An advanced **LangGraph-powered multi-agent AI system** featuring intelligent conditional routing, state management, agent collaboration, and comprehensive memory integration. Built for production with robust error handling, authentication, and a modern web interface.

## 🌟 Features

### 🧠 **Advanced LangGraph Multi-Agent System v2.0**
- **5 Specialized Agents**: WeatherAgent, DiningAgent, ScenicLocationFinder, ForestAnalyzer, SearchAgent
- **Intelligent Conditional Routing**: Advanced LangGraph-based query analysis and routing
- **Multi-Agent Collaboration**: Agents share context and collaborate for comprehensive responses
- **State Management**: Robust state tracking across agent interactions
- **Null Safety & Error Handling**: Production-ready error handling and failover mechanisms

### 🔐 **Secure Authentication System**
- **JWT Token Authentication**: Secure session management
- **User Registration & Login**: Complete user management system
- **Password Security**: bcrypt hashing with salt
- **Session Persistence**: Maintain user context across interactions

### 💾 **Advanced Memory Management**
- **Short-Term Memory (STM)**: Redis-based temporary session storage
- **Long-Term Memory (LTM)**: MySQL-based persistent data storage
- **Vector Search**: Semantic similarity search across conversation history
- **Context Awareness**: Agents use previous interactions for better responses

### 🌐 **Professional Web Interface**
- **Modern UI**: Responsive design with real-time interactions
- **Chat Interface**: Natural language query processing
- **User Dashboard**: Profile, query history, and usage statistics
- **Agent Visualization**: See which agents are active and their capabilities

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Agent System](#-agent-system)
- [Memory System](#-memory-system)
- [Development](#-development)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Contributing](#-contributing)

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Redis Server
- MySQL Server
- Ollama (for LLM processing)

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd python_new-main
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
# Set database credentials, API keys, etc.
```

### 4. Start Services
```bash
# Start Redis (Windows)
redis-server

# Start MySQL
# Ensure MySQL is running with the configured credentials

# Start Ollama
ollama serve
```

### 5. Initialize Database
```bash
python upgrade_database_schema.py
```

### 6. Run the Application
```bash
python -m api.main
```

### 7. Access Web Interface
Open your browser to: **http://localhost:8000**

## 📦 Installation

### System Requirements
- **Operating System**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **Python**: 3.13 or higher
- **Memory**: 4GB RAM minimum (8GB recommended)
- **Storage**: 2GB free space

### Dependencies Installation

#### 1. Python Dependencies
The system requires several key Python packages:

```bash
# Install all dependencies
pip install -r requirements.txt

# Or install core dependencies individually:
pip install fastapi>=0.104.0 uvicorn[standard]>=0.24.0
pip install langgraph>=0.2.0 langchain>=0.3.0 langchain-community>=0.3.0
pip install sentence-transformers>=2.2.0 faiss-cpu>=1.7.0
pip install redis>=5.0.0 mysql-connector-python>=8.0.0
pip install passlib[bcrypt]>=1.7.4 python-jose[cryptography]>=3.3.0
pip install pydantic>=2.5.0 python-dotenv>=1.0.0
```

**Core Dependencies:**
- **Web Framework**: FastAPI 0.104.0+, Uvicorn with standard extras
- **LangGraph/LangChain**: Latest compatible versions (0.2.0+ and 0.3.0+)
- **Vector Store**: Sentence Transformers 2.2.0+, FAISS CPU 1.7.0+
- **Memory Systems**: Redis 5.0.0+, MySQL Connector 8.0.0+
- **Authentication**: Passlib with bcrypt, Python JOSE with cryptography
- **Utilities**: Pydantic 2.5.0+, Python dotenv 1.0.0+, NumPy 1.24.0+

**Optional Testing Dependencies:**
```bash
pip install pytest pytest-asyncio coverage pytest-cov
```

#### 2. Redis Installation
**Windows:**
```bash
# Using Chocolatey
choco install redis-64

# Or download from: https://redis.io/download
```

**macOS:**
```bash
brew install redis
```

**Linux:**
```bash
sudo apt-get install redis-server
```

#### 3. MySQL Installation
**Windows:**
```bash
# Download MySQL Community Server from: https://dev.mysql.com/downloads/mysql/
```

**macOS:**
```bash
brew install mysql
```

**Linux:**
```bash
sudo apt-get install mysql-server
```

#### 4. Ollama Installation
```bash
# Visit: https://ollama.ai/download
# Download and install for your platform

# Pull required models
ollama pull llama3:latest
ollama pull gemma3:4b
```

## ⚙️ Configuration

### Environment Variables
Create a `.env` file in the project root:

```env
# Application Settings
APP_HOST=localhost
APP_PORT=8000
DEBUG=False
APP_TITLE=LangGraph Multi-Agent System
APP_DESCRIPTION=Enhanced multi-agent AI system with UI display and JSON storage
APP_VERSION=2.0.0-multiagent
SECRET_KEY=your-super-secret-key-change-in-production

# Security Settings
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

# Database Configuration
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your-mysql-password
MYSQL_DATABASE=langgraph_ai_system
MYSQL_PORT=3306
MYSQL_CONNECT_TIMEOUT=10
MYSQL_CHARSET=utf8mb4

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3:latest
OLLAMA_TIMEOUT=30
OLLAMA_MAX_TOKENS=1000
OLLAMA_TEMPERATURE=0.7

# Agent Configuration
AGENT_MAX_RESPONSE_LENGTH=5000
AGENT_PROCESSING_TIMEOUT=60
MULTI_AGENT_MAX_AGENTS=3

# UI Configuration
STATIC_DIR=static
TEMPLATES_DIR=templates

# Logging Configuration
LOG_LEVEL=INFO
# LOG_FILE=app.log  # Uncomment to enable file logging
```

### Agent Configuration
Edit `config/agent_config.yml` to customize agent behavior:

```yaml
# Agent Registry Configuration
agent_registry:
  agents_directory: "agents"
  auto_discovery: true
  minimum_confidence_threshold: 0.3
  max_agents_per_query: 5

# Memory Management Configuration
memory:
  stm_default_expiry_hours: 1
  ltm_retention_days: 365
  vector_search_limit: 10
  cross_agent_search_enabled: true

# Orchestration Configuration
orchestration:
  default_strategy: "auto_select_best_agent"
  fallback_agent: "ScenicLocationFinder"
  enable_multi_agent: false
  max_execution_time_seconds: 30

# LLM Configuration
llm:
  default_temperature: 0.7
  max_tokens: 2000
  timeout_seconds: 30
  enable_context_memory: true

# Agent Specific Configuration
agents:
  WeatherAgent:
    temperature: 0.7
    capabilities:
      - weather_forecast
      - climate_analysis
      - meteorology
      - weather_planning
  
  DiningAgent:
    temperature: 0.8
    capabilities:
      - restaurant_recommendations
      - cuisine_analysis
      - dining_planning
      - food_culture
  
  ScenicLocationFinder:
    temperature: 0.7
    capabilities:
      - scenic_location_recommendations
      - travel_planning
      - photography_tips
      - cultural_insights
  
  ForestAnalyzer:
    temperature: 0.6
    capabilities:
      - forest_ecosystem_analysis
      - biodiversity_assessment
      - conservation_recommendations
      - wildlife_identification
  
  SearchAgent:
    temperature: 0.8
    capabilities:
      - semantic_search
      - pattern_recognition
      - similarity_matching
      - historical_insights

# API Configuration
api:
  enable_authentication: false  # Set to true for production
  rate_limiting: false
  cors_enabled: true
  max_request_size_mb: 10

# Logging Configuration
logging:
  level: "INFO"
  log_agent_interactions: true
  log_memory_operations: true
  log_search_queries: true
```

## 🎯 Usage

### Web Interface

#### 1. User Registration
1. Navigate to http://localhost:8000
2. Click "Register here" 
3. Fill in username, email, and password
4. Submit to create account

#### 2. User Login
1. Enter your username and password
2. Click "Sign In"
3. Access the main chat interface

#### 3. Querying the System
1. Type natural language questions in the chat interface
2. The system automatically routes to appropriate agents
3. View comprehensive responses with agent information
4. Check query history in your profile

### Example Queries

#### Scenic Location Queries
```
"Find beautiful mountain locations for photography in the Swiss Alps"
"Tell me about scenic waterfalls in the Pacific Northwest"
"Recommend romantic sunset viewpoints in Tuscany"
```

#### Forest & Nature Queries
```
"What are the best forest conservation practices?"
"Tell me about biodiversity in tropical rainforests"
"How can I identify different tree species while hiking?"
```

#### Water Body Queries
```
"Find pristine lakes for kayaking in Canada"
"Tell me about marine ecosystems in coral reefs"
"What are the best beaches for surfing in California?"
```

#### Historical Queries
```
"Search my conversation history about mountain photography"
"Find previous discussions about forest conservation"
"Show me what I asked about water sports before"
```

### API Usage

#### Authentication
```bash
# Register new user
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "email": "your@email.com", "password": "your_password"}'

# Login
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```

#### Query Processing
```bash
# Authenticated query
curl -X POST "http://localhost:8000/run_graph" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user": "your_username", "question": "Your question here"}'

# Non-authenticated query
curl -X POST "http://localhost:8000/run_graph_legacy" \
  -H "Content-Type: application/json" \
  -d '{"user": "guest", "question": "Your question here"}'
```

### Command-Line Scripts

#### 1. Interactive Demo Script
Test the system with an interactive query interface:
```bash
python scripts/interactive_demo.py
```
**Features**:
- Interactive query input with real-time agent responses
- Agent routing visualization and response metrics
- Memory status tracking (STM/LTM entries)
- Built-in help system with example queries
- System statistics and usage analytics

#### 2. Server Startup Script
Start the FastAPI server with custom configuration:
```bash
python scripts/run.py
```
**Configuration Options**:
- Customizable host, port, and debug settings
- Environment variable integration
- Service dependency checking
- Comprehensive startup logging

#### 3. Complete System Test
Run comprehensive system validation and testing:
```bash
python scripts/run_complete_system.py
```
**Test Coverage**:
- Direct framework testing with multiple agents
- Memory system validation (STM/LTM)
- Database data verification
- HTTP API endpoint testing
- Performance metrics and timing

#### 4. Alternative Startup Options
```bash
# Start with specific server configuration
python start_server.py

# Run lightweight main server
python core/light_main.py

# Interactive user authentication interface
python user_auth_interface.py

# Query interface (Windows)
python user_query_interface_win.py

# Query interface (Unix/Linux)
python user_query_interface.py
```

### Usage Examples by Agent Type

#### Weather Agent Examples
```bash
# Using interactive demo
python scripts/interactive_demo.py
# Query: "What's the weather forecast for hiking in the Swiss Alps this weekend?"
# Query: "Tell me about climate patterns affecting outdoor photography in Norway"
```

#### Dining Agent Examples
```bash
# Query: "Find the best Italian restaurants with outdoor seating in downtown"
# Query: "Recommend romantic dinner spots with wine pairings for anniversary"
```

#### Scenic Location Finder Examples
```bash
# Query: "Find beautiful mountain photography locations in the Swiss Alps"
# Query: "Recommend scenic waterfalls in the Pacific Northwest for weekend trips"
```

#### Forest Analyzer Examples
```bash
# Query: "Analyze biodiversity conservation challenges in tropical rainforests"
# Query: "What are sustainable forestry practices for Canadian boreal forests?"
```

#### Search Agent Examples
```bash
# Query: "Search my conversation history about mountain photography"
# Query: "Find patterns in my travel-related questions and show connections"
```

## 📚 API Documentation

### Authentication Endpoints

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|-----------------|
| POST | `/auth/register` | Register new user | No |
| POST | `/auth/login` | User login | No |
| POST | `/auth/logout` | User logout | Yes |
| GET | `/auth/me` | Get user profile | Yes |
| GET | `/auth/activity` | Get user activity history (with limit param) | Yes |
| GET | `/auth/queries` | Get user query history (with limit param) | Yes |
| GET | `/auth/stats` | Get comprehensive user statistics | Yes |

### Core System Endpoints

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|-----------------|
| GET | `/` | Main web interface (HTML) | No |
| GET | `/health` | System health check | No |
| GET | `/ping` | Connectivity test | No |
| GET | `/agents` | List active agents and graph edges | No |
| POST | `/register_agents` | Register new agents and edges dynamically | No |
| POST | `/run_graph` | Process query (optional authentication) | Optional |
| POST | `/run_graph_legacy` | Legacy query endpoint (no auth) | No |
| GET | `/api/ollama/status` | Check Ollama status and models | No |

### Memory Management Endpoints

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|-----------------|
| POST | `/set_stm` | Set short-term memory (STMRequest model) | No |
| GET | `/get_stm/{user_id}/{agent_id}` | Get short-term memory | No |
| POST | `/memory/ltm/{user_id}/{agent_id}` | Set long-term memory | No |
| GET | `/memory/ltm/{user_id}/{agent_id}` | Get long-term memory by agent | No |
| GET | `/search_vector` | Vector similarity search with fallback | No |

## 🤖 Agent System v2.0

### Available Agents

#### 1. WeatherAgent 🌦️
- **Purpose**: Comprehensive weather information, forecasts, and climate analysis specialist
- **Capabilities**: 
  - Weather forecasts and current conditions
  - Climate analysis and seasonal patterns
  - Weather-related planning advice
  - Impact assessments for outdoor activities
  - Travel weather recommendations
  - Severe weather alerts and safety advice
  - Meteorological explanations and data interpretation
- **Keywords**: weather, temperature, rain, sun, climate, forecast, humidity, wind, storm, snow, hot, cold, sunny, cloudy, precipitation, barometric, pressure, degrees
- **Special Features**: Location context extraction, weather activity planning, multi-type weather analysis (forecast, current, climate, alerts)
- **Example Query**: "What's the weather forecast for hiking in the mountains this weekend?"

#### 2. DiningAgent 🍽️
- **Purpose**: Restaurant recommendations, cuisine analysis, and comprehensive dining experiences
- **Capabilities**:
  - Restaurant recommendations and reviews
  - Cuisine analysis with cultural context
  - Menu suggestions and dish recommendations
  - Local food specialties and hidden gems
  - Dietary accommodations and alternatives
  - Dining etiquette and cultural customs
  - Food and wine pairings
  - Culinary events and food festivals
  - Chef recommendations and signature dishes
  - Seasonal menu insights
- **Keywords**: restaurant, food, cuisine, dining, eat, meal, chef, menu, cooking, recipe, taste, flavor, dish, kitchen, cafe, bistro, eatery, dine, lunch, dinner, breakfast, culinary, gastronomy, delicious, tasty
- **Special Features**: Multi-agent context integration (weather, location), location hint extraction, cuisine-specific analysis, dining experience categorization
- **Example Query**: "Best Italian restaurants for a romantic dinner in downtown with outdoor seating?"

#### 3. ScenicLocationFinderAgent 🏔️
- **Purpose**: Expert recommendations for scenic locations with comprehensive travel information
- **Capabilities**:
  - Scenic location recommendations worldwide
  - Detailed travel planning assistance
  - Photography tips and best viewpoints
  - Cultural insights and local significance
  - Practical travel information (access, timing, costs)
  - Nearby amenities and accommodation options
  - Safety considerations and preparation tips
- **Keywords**: scenic, mountain, landscape, beautiful, view, tourist, visit, travel, place, location, destination, photography, sight, attraction
- **Special Features**: Historical query matching, recent context integration, specialized location type recommendations, photography guidance
- **Example Query**: "Find scenic mountain photography locations in the Swiss Alps with cultural significance?"

#### 4. ForestAnalyzerAgent 🌲
- **Purpose**: Scientific forest ecosystem analysis and conservation expertise
- **Capabilities**:
  - Forest ecosystem analysis and health assessment
  - Biodiversity and species composition analysis
  - Conservation status and threat assessment
  - Wildlife habitat and corridor analysis
  - Sustainable forest management practices
  - Scientific research support and findings
  - Ecological research insights
- **Keywords**: forest, tree, woodland, ecosystem, biodiversity, conservation, wildlife, nature, jungle, rainforest, deforestation, species, habitat, flora, fauna
- **Special Features**: Scientific accuracy focus, research-based responses, forest health analysis, conservation assessment, pattern detection across analysis types
- **Example Query**: "Analyze the biodiversity conservation challenges in tropical rainforest ecosystems?"

#### 5. SearchAgent 🔍
- **Purpose**: Advanced semantic search and pattern analysis across all user interactions
- **Capabilities**:
  - Semantic search using vector embeddings
  - Pattern recognition in historical data
  - Similarity matching across all agents
  - Content analysis and summarization
  - Trend identification over time
  - Cross-agent search capabilities
  - Historical insights and connections
- **Keywords**: search, history, previous, before, recall, remember, similar, past, find, lookup, pattern, trend
- **Special Features**: Cross-agent search, vector-based similarity, pattern analysis, comprehensive historical search (STM + LTM), relevance scoring
- **Example Query**: "Find similar conversations about mountain travel and show me the patterns in my interests?"

### LangGraph Multi-Agent System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT REQUEST                                        │
│                    (POST /run_graph with user query)                           │
└─────────────────────────────┬───────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────────────────┐
│                     LANGGRAPH ORCHESTRATOR                                     │
│                  (Multi-Agent State Management)                                │
│  • Load agents.json configuration  • Initialize agent capabilities            │
│  • Build StateGraph with conditional routing  • Manage execution state        │
└─────────────────────────────┬───────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────────────────┐
│                        ROUTER AGENT NODE                                       │
│                   (Dynamic Query Analysis & Routing)                           │
│  • Keyword matching  • Capability scoring  • Multi-agent selection            │
│  • Context building  • Execution path planning                                │
└─────┬───────────┬───────────┬───────────┬───────────┬─────────────────────────┘
      │           │           │           │           │
      ▼           ▼           ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐
│ Weather │ │ Dining  │ │ Scenic  │ │ Forest  │ │   Search    │
│  Agent  │ │  Agent  │ │Location │ │Analyzer │ │   Agent     │
│         │ │         │ │ Finder  │ │  Agent  │ │             │
│🌦️       │ │🍽️       │ │🏔️       │ │🌲       │ │🔍           │
└─────┬───┘ └─────┬───┘ └─────┬───┘ └─────┬───┘ └─────┬───────┘
      │           │           │           │           │
      ▼           ▼           ▼           ▼           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        MEMORY INTEGRATION LAYER                                │
│  ┌─────────────────┐              ┌─────────────────────────────────────────┐  │
│  │   REDIS (STM)   │              │            MySQL (LTM)                  │  │
│  │ • Session data  │◄────────────►│ • User profiles & query history         │  │
│  │ • Temp context  │              │ • Agent interactions & responses        │  │
│  │ • Active convos │              │ • Learning patterns & preferences       │  │
│  └─────────────────┘              └─────────────────────────────────────────┘  │
│           ▲                                           ▲                        │
│           └─────────── Vector Search Engine ─────────┘                        │
│              (Sentence Transformers + FAISS)                                  │
└─────────────────────────────┬───────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────────────────┐
│                    CONDITIONAL ROUTING & STATE UPDATES                         │
│  • Agent communication via shared MultiAgentState                              │
│  • Conditional edges: weather→location, dining→weather, etc.                   │
│  • Dynamic execution paths based on query complexity                           │
│  • Context sharing between agents (location_data, weather_data, etc.)          │
└─────────────────────────────┬───────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────────────────┐
│                      RESPONSE SYNTHESIZER NODE                                 │
│                    (Multi-Agent Response Combination)                          │
│  • Combine agent responses  • Apply response weighting                         │
│  • Generate execution summary  • Format final output                           │
└─────────────────────────────┬───────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────────────────┐
│                         FINAL RESPONSE                                         │
│  {
│    "agent": "primary_agent_used",
│    "response": "comprehensive_ai_response",
│    "edges_traversed": ["RouterAgent", "WeatherAgent", "ScenicLocationFinder"],
│    "execution_path": [...],
│    "context": { "stm": {...}, "ltm": {...} },
│    "timestamp": "2024-01-01T12:00:00Z"
│  }                                                                             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Key Features of the LangGraph Architecture:

🔄 **Conditional State Management**: Each agent updates the `MultiAgentState` with shared context

🧠 **Intelligent Agent Collaboration**: Agents can trigger other agents based on query needs:
- WeatherAgent → ScenicLocationFinder (for location-based weather)
- DiningAgent → WeatherAgent (for outdoor dining recommendations)  
- ScenicLocationFinder → ForestAnalyzer (for nature-based locations)

📊 **Dynamic Execution Paths**: The system determines optimal agent routing at runtime

💾 **Integrated Memory System**: All agents access shared STM/LTM with vector search capabilities

🔀 **Multi-Agent Responses**: Complex queries can involve multiple agents working together

⚡ **Production-Ready**: Built with LangGraph's StateGraph for robust error handling and state persistence

## 💾 Memory System

### Short-Term Memory (STM) - Redis
- **Purpose**: Store temporary session data and recent interactions
- **Retention**: 1 hour (configurable)
- **Use Cases**: Active conversations, temporary context, session state

### Long-Term Memory (LTM) - MySQL
- **Purpose**: Persistent storage of user data and query history
- **Retention**: 365 days (configurable)
- **Use Cases**: User profiles, conversation history, learning patterns

### Vector Search
- **Technology**: Sentence Transformers + FAISS
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Purpose**: Semantic similarity search across conversation history
- **Use Cases**: Finding related conversations, contextual recommendations

## 🔧 Development

### Project Structure
```
python_new-main/
├── api/                    # FastAPI application
│   ├── __init__.py
│   └── main.py            # Main API server
├── agents/                # Individual agent implementations
│   ├── __init__.py
│   ├── agent_template.py
│   ├── dining_agent.py
│   ├── forest_analyzer.py
│   ├── scenic_location_finder.py
│   ├── search_agent.py
│   └── weather_agent.py
├── auth/                  # Authentication system
│   ├── __init__.py
│   ├── auth_endpoints.py  # Auth API routes
│   ├── auth_service.py    # Auth business logic
│   ├── models.py          # User data models
│   ├── router.py          # Auth router
│   └── utils.py           # Auth utilities
├── core/                  # Core system components
│   ├── __init__.py
│   ├── agents/            # Core agent implementations
│   │   ├── forest_analyzer_agent.py
│   │   ├── orchestrator_agent.py
│   │   ├── scenic_location_finder_agent.py
│   │   └── search_agent.py
│   ├── agent_registry.py  # Agent registration system
│   ├── base_agent.py      # Base agent class
│   ├── config_loader.py   # Configuration loader
│   ├── dynamic_agents.py  # Dynamic agent management
│   ├── langgraph_framework.py      # LangGraph integration
│   ├── langgraph_multiagent_system.py  # Multi-agent system
│   ├── light_main.py      # Lightweight main runner
│   ├── location_extractor.py  # Location extraction utilities
│   ├── memory.py          # Memory management
│   ├── mock_ollama_client.py   # Mock LLM client for testing
│   ├── ollama_client.py   # LLM client
│   ├── orchestrator.py    # Agent orchestration
│   ├── registry.py        # Agent registry
│   └── vector_store.py    # Vector storage system
├── database/              # Database connections
│   ├── __init__.py
│   └── connection.py      # MySQL connection manager
├── scripts/               # Utility scripts
│   ├── interactive_demo.py
│   ├── run.py
│   ├── run_complete_system.py
│   └── simple_ollama_client.py
├── static/                # Web interface assets
│   ├── css/
│   └── js/
├── templates/             # HTML templates and agent templates
│   ├── create_agent.py
│   ├── sample_agent_template.py
│   ├── weather_agent_example.py
│   └── index.html         # Main UI template
├── tests/                 # Test suites
│   ├── __init__.py
│   ├── test_ai_system.py
│   ├── test_auth_system.py
│   ├── test_complete_system.py
│   ├── test_direct_framework.py
│   ├── test_enhanced_system.py
│   ├── test_full_system.py
│   ├── test_langgraph_framework.py
│   ├── test_memory.py
│   ├── test_multi_agent.py
│   ├── test_ollama.py
│   ├── test_orchestration.py
│   ├── test_search_agent.py
│   ├── test_server_and_framework.py
│   └── test_ui_responses.py
├── config/                # Configuration files
│   └── agent_config.yml   # Agent configuration
├── docs/                  # Documentation
├── comprehensive_multiagent_test.py  # Comprehensive system test
├── config.py              # Application configuration
├── final_test.py          # Final system test
├── simple_test.py         # Simple system test
├── start_server.py        # Server startup script
├── test_framework.py      # Framework testing
├── test_multiagent_system.py  # Multi-agent system tests
├── test_null_safety_fixes.py  # Null safety testing
├── test_web_interface.py  # Web interface tests
├── upgrade_database_schema.py  # Database schema upgrade
├── user_auth_interface.py # User authentication interface
├── user_query_interface.py    # User query interface (Unix)
├── user_query_interface_win.py # User query interface (Windows)
└── requirements.txt       # Python dependencies
```

### Adding New Agents

1. **Create Agent File**: Add new agent in `agents/` directory
2. **Update Configuration**: Add agent to `core/agents.json`
3. **Define Capabilities**: Specify keywords and capabilities in `config/agent_config.yml`
4. **Test Integration**: Use test scripts to verify functionality

### Extending Functionality

#### Add New Endpoints
```python
# In api/main.py
@app.post("/your_new_endpoint")
async def your_new_function(request_data: YourModel):
    # Your implementation
    pass
```

#### Customize Agent Behavior
```python
# In agents/your_agent.py
class YourAgent(BaseAgent):
    def process_query(self, query: str, context: dict) -> str:
        # Your agent logic
        return response
```

## 🧪 Testing

### Prerequisites
Install testing dependencies:
```bash
pip install pytest pytest-asyncio coverage
```

### Available Test Suites

#### Framework & System Tests
```bash
# Comprehensive multi-agent system test
python comprehensive_multiagent_test.py

# Main framework testing
python test_framework.py

# Multi-agent system integration test
python test_multiagent_system.py

# Null safety and error handling validation
python test_null_safety_fixes.py

# Final system validation test
python final_test.py

# Simple system smoke test
python simple_test.py

# Web interface testing
python test_web_interface.py
```

#### Interactive Interfaces
```bash
# User authentication interface (interactive)
python user_auth_interface.py

# Query interface for Unix/Linux systems
python user_query_interface.py

# Query interface for Windows systems
python user_query_interface_win.py
```

#### Component-Specific Tests (pytest)
```bash
# Test complete system integration
python -m pytest tests/test_complete_system.py

# Test AI system components
python -m pytest tests/test_ai_system.py

# Test authentication system
python -m pytest tests/test_auth_system.py

# Test memory management
python -m pytest tests/test_memory.py

# Test agent orchestration
python -m pytest tests/test_orchestration.py

# Test search agent functionality
python -m pytest tests/test_search_agent.py

# Test LangGraph framework
python -m pytest tests/test_langgraph_framework.py

# Test Ollama client integration
python -m pytest tests/test_ollama.py

# Test multi-agent interactions
python -m pytest tests/test_multi_agent.py

# Test enhanced system features
python -m pytest tests/test_enhanced_system.py

# Test full system functionality
python -m pytest tests/test_full_system.py

# Test direct framework access
python -m pytest tests/test_direct_framework.py

# Test server and framework integration
python -m pytest tests/test_server_and_framework.py

# Test UI response handling
python -m pytest tests/test_ui_responses.py
```

### Run All Tests at Once
```bash
# Run all pytest-based tests
python -m pytest tests/ -v

# Run all system validation tests
python test_framework.py && python test_multiagent_system.py && python comprehensive_multiagent_test.py

# Quick smoke test
python simple_test.py
```

### Test Coverage Analysis
```bash
# Install coverage tools
pip install coverage pytest-cov

# Generate comprehensive coverage report
coverage run -m pytest tests/
coverage report --show-missing

# Generate HTML coverage report
coverage html
# View report: open htmlcov/index.html

# Run tests with inline coverage
python -m pytest tests/ --cov=. --cov-report=term-missing
```

### Debugging Tests
```bash
# Run tests with verbose output
python -m pytest tests/ -v -s

# Run specific test with debugging
python -m pytest tests/test_memory.py::test_specific_function -v -s

# Run tests with pdb debugging
python -m pytest tests/ --pdb
```

### Performance Testing
```bash
# Test system performance under load
python test_framework.py --performance

# Test multi-agent response times
python comprehensive_multiagent_test.py --timing
```

### Integration Testing
```bash
# Test complete system with real services
# Ensure Redis, MySQL, and Ollama are running
python test_complete_system.py

# Test authentication flow
python tests/test_auth_system.py

# Test memory persistence
python tests/test_memory.py
```

## 🚀 Deployment

### Production Configuration

#### 1. Environment Setup
```env
# Production .env
DEBUG=False
SECRET_KEY=your-super-secure-production-key
MYSQL_PASSWORD=secure-production-password
```

#### 2. Database Setup
```bash
# Create production database
mysql -u root -p
CREATE DATABASE langgraph_ai_system_prod;
```

#### 3. Security Considerations
- Use HTTPS in production
- Set strong SECRET_KEY
- Configure firewall rules
- Use production-grade database credentials
- Enable authentication for all endpoints

### Docker Deployment (Optional)
```dockerfile
# Dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "-m", "api.main"]
```

### Cloud Deployment
- **AWS**: Use ECS, RDS for MySQL, ElastiCache for Redis
- **Google Cloud**: Use Cloud Run, Cloud SQL, Memorystore
- **Azure**: Use Container Instances, Azure Database, Azure Cache

## 📊 Monitoring & Analytics

### Health Checks
- **Endpoint**: `/health` - System status
- **Endpoint**: `/ping` - Connectivity test  
- **Endpoint**: `/api/ollama/status` - LLM availability

### User Analytics
- **Query Volume**: Track queries per user/agent
- **Response Times**: Monitor performance metrics
- **Agent Usage**: Analyze which agents are most used
- **Error Rates**: Track and alert on system errors

### Logging
```python
# Configure logging in config.py
LOG_LEVEL=INFO
LOG_FILE=app.log
```

## 🤝 Contributing

### Development Workflow
1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Code Standards
- **PEP 8**: Follow Python style guidelines
- **Type Hints**: Use type annotations where possible
- **Documentation**: Add docstrings to all functions
- **Testing**: Include tests for new features
- **Logging**: Add appropriate logging statements

### Commit Message Format
```
type(scope): description

feat(agents): add new WaterBodyAnalyzer agent
fix(auth): resolve token expiration issue
docs(readme): update installation instructions
test(memory): add vector search test cases
```

## 📈 Performance Optimization

### Caching Strategies
- **Redis**: Cache frequent queries and agent responses
- **Application**: Use LRU cache for expensive operations
- **Database**: Optimize queries with proper indexing

### Scaling Considerations
- **Horizontal Scaling**: Multiple API server instances
- **Database Optimization**: Read replicas, connection pooling
- **Agent Parallelization**: Concurrent agent execution
- **Load Balancing**: Distribute traffic across instances

## 🔒 Security

### Authentication Security
- **JWT Tokens**: Secure token-based authentication
- **Password Hashing**: bcrypt with salt
- **Session Management**: Secure session handling
- **CORS**: Configurable cross-origin resource sharing

### Data Protection
- **Encryption**: Sensitive data encryption at rest
- **Input Validation**: Sanitize all user inputs
- **SQL Injection**: Parameterized queries
- **XSS Protection**: Output encoding and validation

## 📞 Support

### Getting Help
- **Documentation**: Check docs/ directory
- **Issues**: Create GitHub issues for bugs
- **Discussions**: Use GitHub Discussions for questions
- **Email**: Contact developers@multiagent.system

### Known Issues
- **Ollama Timeouts**: Increase timeout for complex queries
- **Memory Usage**: Monitor Redis memory with large datasets
- **Browser Compatibility**: Tested on Chrome, Firefox, Safari

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **LangGraph**: Framework for building agent workflows
- **FastAPI**: Modern, fast web framework for building APIs
- **Ollama**: Local LLM inference server
- **Redis**: In-memory data structure store
- **MySQL**: Relational database management system
- **Sentence Transformers**: State-of-the-art text embeddings

## 📈 Project Stats

- **Lines of Code**: ~10,000+
- **Test Coverage**: 85%+
- **Documentation**: Comprehensive + System Ready Guide
- **Agents**: 5 specialized agents (v2.0)
- **API Endpoints**: 15+ endpoints
- **Features**: 25+ key features
- **Performance**: <2s for complex multi-agent queries
- **Framework**: LangGraph v2.0 with conditional routing
- **Architecture**: Production-ready multi-agent system

---

## 🎉 Ready to Get Started?

1. **Clone** the repository
2. **Install** dependencies  
3. **Configure** your environment
4. **Start** the services
5. **Launch** the application
6. **Begin** querying the multiagent system!

### 🌐 Access Your System
**Web Interface**: http://localhost:8000  
**API Documentation**: http://localhost:8000/docs  
**Health Check**: http://localhost:8000/health

---

*Built with ❤️ for intelligent AI interactions*
