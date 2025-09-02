"""
Improved Ollama integration for local LLM responses
Enhanced with better timeout handling, retry logic, and connection pooling
"""
import requests
import json
import logging
import os
import time
from typing import Dict, List, Optional, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Try to import decouple, fallback to os.getenv
try:
    from decouple import config
except ImportError:
    def config(key, default=None, cast=None):
        value = os.getenv(key, default)
        if cast and value is not None:
            return cast(value)
        return value

logger = logging.getLogger(__name__)

# Optional mock fallback
try:
    from core.mock_ollama_client import mock_ollama_client as MOCK_OLLAMA_CLIENT
except Exception:
    MOCK_OLLAMA_CLIENT = None

FALLBACK_TO_MOCK = os.getenv('OLLAMA_ENABLE_MOCK_FALLBACK', 'true').lower() == 'true'

class ImprovedOllamaClient:
    """Enhanced client for interacting with local Ollama server"""
    
    def __init__(self):
        self.base_url = config('OLLAMA_BASE_URL', default='http://localhost:11434')
        self.default_model = config('OLLAMA_DEFAULT_MODEL', default='llama3:latest')
        
        # Enhanced timeout configuration
        self.timeout = config('OLLAMA_TIMEOUT', default=300, cast=int)  # 5 minutes total timeout
        self.connection_timeout = config('OLLAMA_CONNECTION_TIMEOUT', default=10, cast=int)
        self.read_timeout = config('OLLAMA_READ_TIMEOUT', default=300, cast=int)
        
        # Retry configuration
        self.max_retries = config('OLLAMA_MAX_RETRIES', default=3, cast=int)
        self.retry_delay = config('OLLAMA_RETRY_DELAY', default=2.0, cast=float)
        
        # Initialize session with connection pooling and retry strategy
        self.session = self._create_session()
        
        logger.info(f"Initialized OllamaClient with timeout={self.timeout}s, retries={self.max_retries}")
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with optimal settings for Ollama"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1.0,  # Exponential backoff
            status_forcelist=[500, 502, 503, 504, 408],  # HTTP status codes to retry on
            allowed_methods=["GET", "POST"],  # HTTP methods to retry
        )
        
        # Configure HTTP adapter with retry strategy
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,  # Number of connection pools
            pool_maxsize=20,      # Max connections per pool
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'ImprovedOllamaClient/2.0',
            'Connection': 'keep-alive'
        })
        
        return session
    
    def _get_timeout_tuple(self) -> tuple:
        """Get timeout as a tuple (connection_timeout, read_timeout)"""
        return (self.connection_timeout, self.read_timeout)
    
    def _execute_with_retry(self, func, *args, **kwargs):
        """Execute a function with custom retry logic"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except requests.exceptions.Timeout as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Timeout on attempt {attempt + 1}/{self.max_retries + 1}, retrying in {delay}s")
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries + 1} attempts failed due to timeout")
                    break
            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Request failed on attempt {attempt + 1}/{self.max_retries + 1}, retrying in {delay}s: {e}")
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries + 1} attempts failed: {e}")
                    break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                last_exception = e
                break
        
        raise last_exception
    
    def is_available(self) -> bool:
        """Check if Ollama server is available"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/tags", 
                timeout=(5, 10)  # Quick connection check
            )
            is_available = response.status_code == 200
            if is_available:
                logger.debug("Ollama server is available")
            return is_available
        except Exception as e:
            logger.warning(f"Ollama server not available: {e}")
            return False
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models"""
        try:
            def _list_models():
                response = self.session.get(
                    f"{self.base_url}/api/tags", 
                    timeout=self._get_timeout_tuple()
                )
                response.raise_for_status()
                return response.json().get('models', [])
            
            return self._execute_with_retry(_list_models)
            
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            # Fallback to mock models if enabled
            if FALLBACK_TO_MOCK and MOCK_OLLAMA_CLIENT:
                logger.warning("Using mock model list due to Ollama error")
                try:
                    return MOCK_OLLAMA_CLIENT.list_models()
                except Exception:
                    return []
            return []
    
    def generate_response(
        self, 
        prompt: str, 
        model: Optional[str] = None, 
        system_prompt: Optional[str] = None,
        context: Optional[List[str]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Generate response from Ollama model with enhanced reliability"""
        try:
            model = model or self.default_model
            max_tokens = max_tokens or config('OLLAMA_MAX_TOKENS', default=1000, cast=int)
            temperature = temperature or config('OLLAMA_TEMPERATURE', default=0.7, cast=float)
            
            # Prepare the prompt with context if provided
            full_prompt = prompt
            if context:
                context_str = "\n".join(context)
                full_prompt = f"Context:\n{context_str}\n\nQuery: {prompt}"
            
            payload = {
                "model": model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            # Log request details for debugging
            logger.debug(f"Generating response with model={model}, timeout={self.timeout}s")
            
            def _generate():
                response = self.session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=self._get_timeout_tuple()
                )
                response.raise_for_status()
                return response.json()
            
            result = self._execute_with_retry(_generate)
            response_text = result.get('response', 'No response generated')
            
            logger.debug(f"Successfully generated response ({len(response_text)} characters)")
            return response_text
            
        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out after all retries")
# Try enhanced mock fallback
            logger.warning("Ollama not available, falling back to enhanced mock client")
            try:
                from core.enhanced_mock_ollama_client import enhanced_mock_client
                return enhanced_mock_client.generate_response(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    context=context,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            except Exception as mock_error:
                logger.error(f"Mock fallback also failed: {mock_error}")
            return "Request timed out after multiple attempts. Please try again or check Ollama server status."
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama request failed after all retries: {e}")
            # Try enhanced mock fallback
            logger.warning("Falling back to enhanced mock client due to request failure")
            try:
                from core.enhanced_mock_ollama_client import enhanced_mock_client
                return enhanced_mock_client.generate_response(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    context=context,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            except Exception as mock_error:
                logger.error(f"Mock fallback also failed: {mock_error}")
            return f"Error generating response after retries: {str(e)}"
            
        except Exception as e:
            logger.error(f"Unexpected error in generate_response: {e}")
            # Try enhanced mock fallback
            logger.warning("Falling back to enhanced mock client due to unexpected error")
            try:
                from core.enhanced_mock_ollama_client import enhanced_mock_client
                return enhanced_mock_client.generate_response(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    context=context,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            except Exception as mock_error:
                logger.error(f"Mock fallback also failed: {mock_error}")
            return "An unexpected error occurred. Please try again."
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Chat completion with message history"""
        try:
            model = model or self.default_model
            
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            def _chat():
                response = self.session.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=self._get_timeout_tuple()
                )
                response.raise_for_status()
                return response.json()
            
            result = self._execute_with_retry(_chat)
            return result.get('message', {}).get('content', 'No response generated')
            
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            return f"Error in chat completion: {str(e)}"

    def generate_embedding(self, text: str, model: str = "nomic-embed-text") -> List[float]:
        """Generate embeddings for text using Ollama"""
        try:
            payload = {
                "model": model,
                "prompt": text
            }
            
            def _embed():
                response = self.session.post(
                    f"{self.base_url}/api/embeddings",
                    json=payload,
                    timeout=self._get_timeout_tuple()
                )
                response.raise_for_status()
                return response.json()
            
            result = self._execute_with_retry(_embed)
            return result.get('embedding', [])
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return []

    def close(self):
        """Close the session and cleanup resources"""
        if hasattr(self, 'session'):
            self.session.close()
            logger.debug("Ollama session closed")

    def __del__(self):
        """Cleanup on destruction"""
        try:
            self.close()
        except:
            pass

class AgentPromptManager:
    """Manages prompts and system messages for different agents"""
    
    def __init__(self):
        self.agent_prompts = {
            "SearchAgent": {
                "system": """You are a search agent specialized in finding similar content from user history.
                Analyze the query and find the most relevant historical interactions.
                Always return responses in valid JSON format with similarity scores.""",
                "template": """Based on the user's history, find content similar to: {query}
                
                History context:
                {context}
                
                Return a JSON response with relevant matches and similarity explanations."""
            },
            
            "ScenicLocationFinder": {
                "system": """You are a scenic location finding agent. You help users discover beautiful, 
                interesting, and scenic places based on their preferences and queries.""",
                "template": """Help find scenic locations based on: {query}
                
                Consider factors like:
                - Natural beauty and landscapes
                - Accessibility and safety
                - Season and weather considerations
                - User preferences from context: {context}
                
                Provide detailed recommendations with practical information."""
            },
            
            "ForestAnalyzer": {
                "system": """You are a forest analysis agent specializing in forest ecology, 
                conservation, and forest-related information.""",
                "template": """Analyze forest-related query: {query}
                
                Context from previous interactions: {context}
                
                Provide detailed analysis covering:
                - Ecosystem characteristics
                - Biodiversity considerations
                - Conservation status
                - Management recommendations if applicable"""
            },
            
            "WaterBodyAnalyzer": {
                "system": """You are a water body analysis agent specializing in hydrology, 
                water quality, and aquatic ecosystems.""",
                "template": """Analyze water body related query: {query}
                
                Previous context: {context}
                
                Cover aspects like:
                - Hydrological characteristics
                - Water quality parameters
                - Aquatic ecosystem health
                - Environmental factors and impacts"""
            },
            
            "WeatherAgent": {
                "system": """You are WeatherAgent, a specialized weather analysis assistant. Provide accurate, helpful weather information including:
                - Current conditions and forecasts
                - Climate analysis and seasonal patterns
                - Weather-related planning advice
                - Impact on outdoor activities
                Be practical and actionable in your responses.""",
                "template": """Weather Query: {query}
                
                Context: {context}
                
                Please provide comprehensive weather information including:
                1. Current conditions or forecast as appropriate
                2. Temperature information
                3. Precipitation chances if relevant
                4. Wind conditions
                5. Any weather advisories or recommendations
                6. Impact on activities if mentioned
                
                Be specific, practical, and helpful."""
            },
            
            "DiningAgent": {
                "system": """You are DiningAgent, a culinary and restaurant specialist. Provide excellent dining recommendations including:
                - Restaurant suggestions and cuisine types
                - Local food culture and specialties
                - Dining experiences and ambiance
                - Food and weather/location considerations
                Be descriptive and helpful for dining decisions.""",
                "template": """Dining Query: {query}
                
                Context: {context}
                
                Please provide comprehensive dining recommendations including:
                1. Restaurant suggestions or cuisine types
                2. Location considerations and accessibility
                3. Ambiance and dining experience
                4. Menu highlights or signature dishes
                5. Price range and value considerations
                6. Special dietary accommodations if mentioned
                
                Be specific, enticing, and practical in your recommendations."""
            },
            
            "OrchestratorAgent": {
                "system": """You are an orchestrator agent that routes queries to appropriate specialist agents.
                Analyze the query and determine which agents should handle it.""",
                "template": """Analyze this query for routing: {query}
                
                Available agents and their capabilities:
                - SearchAgent: Similarity search in user history
                - ScenicLocationFinder: Finding beautiful locations
                - ForestAnalyzer: Forest ecology and analysis
                - WaterBodyAnalyzer: Water bodies and hydrology
                - WeatherAgent: Weather forecasts and climate analysis
                - DiningAgent: Restaurant recommendations and cuisine analysis
                
                Determine which agent(s) should handle this query and why.
                Return routing decision as JSON."""
            }
        }
    
    def get_prompt(self, agent_name: str, query: str, context: str = "") -> Optional[Dict[str, str]]:
        """Get formatted prompt for an agent with comprehensive null safety"""
        try:
            # Validate inputs
            if not agent_name or not isinstance(agent_name, str):
                logger.warning(f"Invalid agent_name: {agent_name}, using default")
                agent_name = "ScenicLocationFinder"
            
            if not query or not isinstance(query, str):
                logger.warning(f"Invalid query: {query}, using default")
                query = "General query"
            
            if context is None:
                context = ""
            
            # Check if agent exists, fallback to default
            if agent_name not in self.agent_prompts:
                # Handle ScenicLocationFinderAgent mapping to ScenicLocationFinder
                if agent_name == "ScenicLocationFinderAgent":
                    logger.debug(f"Mapping {agent_name} to ScenicLocationFinder")
                    agent_name = "ScenicLocationFinder"
                else:
                    logger.warning(f"Agent {agent_name} not found, using ScenicLocationFinder")
                    agent_name = "ScenicLocationFinder"
            
            agent_config = self.agent_prompts.get(agent_name)
            if not agent_config or not isinstance(agent_config, dict):
                logger.error(f"Invalid agent config for {agent_name}")
                return self._get_fallback_prompt(query, context)
            
            # Safely get template and system prompt
            template = agent_config.get("template", "Query: {query}\nContext: {context}")
            system_prompt = agent_config.get("system", "You are a helpful AI assistant.")
            
            if not template or not system_prompt:
                logger.error(f"Missing template or system prompt for {agent_name}")
                return self._get_fallback_prompt(query, context)
            
            # Format prompt safely
            try:
                formatted_prompt = template.format(
                    query=query or "General query", 
                    context=context or "No previous context available"
                )
            except KeyError as e:
                logger.error(f"Template formatting error for {agent_name}: {e}")
                formatted_prompt = f"Query: {query}\nContext: {context or 'No context'}"
            
            result = {
                "system": system_prompt,
                "prompt": formatted_prompt
            }
            
            # Final validation
            if not result.get("system") or not result.get("prompt"):
                logger.error(f"Invalid result structure for {agent_name}")
                return self._get_fallback_prompt(query, context)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in get_prompt for {agent_name}: {e}")
            return self._get_fallback_prompt(query, context)
    
    def _get_fallback_prompt(self, query: str, context: str) -> Dict[str, str]:
        """Get fallback prompt when normal prompt generation fails"""
        return {
            "system": "You are a helpful AI assistant. Provide accurate and helpful responses.",
            "prompt": f"Please respond to this query: {query or 'General query'}\n\nContext: {context or 'No context available'}"
        }

# Create improved client instance
improved_ollama_client = ImprovedOllamaClient()

# Maintain backward compatibility by aliasing the old client
OllamaClient = ImprovedOllamaClient
ollama_client = improved_ollama_client

# Global instances for compatibility
prompt_manager = AgentPromptManager()
