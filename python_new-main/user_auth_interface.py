#!/usr/bin/env python3
"""
[AUTH] LangGraph Authenticated User Interface
Interactive interface with user authentication, session management, and activity tracking
"""
import sys
import os
import json
import requests
import getpass
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class AuthenticatedUserInterface:
    def __init__(self):
        # Get API base from environment, default to localhost:8000
        app_host = os.getenv('APP_HOST', 'localhost')
        app_port = os.getenv('APP_PORT', '8000')
        self.api_base = f"http://{app_host}:{app_port}"
        self.current_user = None
        self.auth_token = None
        self.session_id = None
        
        # Try to load saved session
        self.load_session()
    
    def save_session(self):
        """Save session data to file"""
        session_data = {
            'user': self.current_user,
            'token': self.auth_token,
            'session_id': self.session_id
        }
        try:
            with open('.auth_session.json', 'w') as f:
                json.dump(session_data, f)
        except Exception:
            pass
    
    def load_session(self):
        """Load saved session data"""
        try:
            if os.path.exists('.auth_session.json'):
                with open('.auth_session.json', 'r') as f:
                    session_data = json.load(f)
                self.current_user = session_data.get('user')
                self.auth_token = session_data.get('token')
                self.session_id = session_data.get('session_id')
                
                # Validate session
                if self.auth_token:
                    if self.validate_session():
                        return
                    else:
                        self.clear_session()
        except Exception:
            pass
    
    def clear_session(self):
        """Clear session data"""
        self.current_user = None
        self.auth_token = None
        self.session_id = None
        try:
            if os.path.exists('.auth_session.json'):
                os.remove('.auth_session.json')
        except Exception:
            pass
    
    def validate_session(self) -> bool:
        """Validate current session"""
        if not self.auth_token:
            return False
        
        try:
            response = requests.get(
                f"{self.api_base}/auth/me",
                headers={'Authorization': f'Bearer {self.auth_token}'},
                timeout=5
            )
            if response.ok:
                self.current_user = response.json()
                return True
        except Exception:
            pass
        
        return False
    
    def show_welcome(self):
        """Show welcome message"""
        print(" >> LANGGRAPH AI SYSTEM - AUTHENTICATED USER INTERFACE")
        print("=" * 70)
        print(" >> Welcome! You can ask questions about:")
        print("   *  Scenic locations and travel destinations")
        print("   *  Water bodies, lakes, rivers, and aquatic ecosystems") 
        print("   *  Forests, ecology, and conservation")
        print("   *  Search your conversation history")
        print("   *  General AI and technology questions")
        print()
        print(" >> The system automatically routes to the best specialized agent!")
        print("=" * 70)
        print()
    
    def register_user(self) -> bool:
        """Register a new user"""
        print("\n[REGISTER] USER REGISTRATION")
        print("-" * 30)
        
        username = input("[USER] Username: ").strip()
        if not username:
            print("[ERROR] Username is required!")
            return False
        
        email = input("[EMAIL] Email: ").strip()
        if not email:
            print("[ERROR] Email is required!")
            return False
        
        password = getpass.getpass("[PASS] Password: ")
        if not password:
            print("[ERROR] Password is required!")
            return False
        
        if len(password) < 6:
            print("[ERROR] Password must be at least 6 characters long!")
            return False
        
        confirm_password = getpass.getpass("[PASS] Confirm Password: ")
        if password != confirm_password:
            print("[ERROR] Passwords do not match!")
            return False
        
        try:
            response = requests.post(
                f"{self.api_base}/auth/register",
                json={
                    'username': username,
                    'email': email,
                    'password': password
                },
                timeout=10
            )
            
            if response.ok:
                result = response.json()
                if result['success']:
                    self.current_user = result['user']
                    self.auth_token = result['token']
                    self.session_id = result['session_id']
                    self.save_session()
                    
                    print(f"[SUCCESS] Welcome, {username}! Account created successfully.")
                    return True
                else:
                    print(f"[ERROR] Registration failed: {result.get('message', 'Unknown error')}")
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                print(f"[ERROR] Registration failed: {error_data.get('detail', f'HTTP {response.status_code}')}")
                
        except requests.exceptions.Timeout:
            print("[ERROR] Registration timed out. Please try again.")
        except Exception as e:
            print(f"[ERROR] Registration failed: {e}")
        
        return False
    
    def login_user(self) -> bool:
        """Login user"""
        print("\n[LOGIN] USER LOGIN")
        print("-" * 20)
        
        username = input("[USER] Username: ").strip()
        if not username:
            print("[ERROR] Username is required!")
            return False
        
        password = getpass.getpass("[PASS] Password: ")
        if not password:
            print("[ERROR] Password is required!")
            return False
        
        try:
            response = requests.post(
                f"{self.api_base}/auth/login",
                json={
                    'username': username,
                    'password': password
                },
                timeout=10
            )
            
            if response.ok:
                result = response.json()
                if result['success']:
                    self.current_user = result['user']
                    self.auth_token = result['token']
                    self.session_id = result['session_id']
                    self.save_session()
                    
                    print(f"[SUCCESS] Welcome back, {username}!")
                    return True
                else:
                    print(f"[ERROR] Login failed: {result.get('message', 'Unknown error')}")
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                print(f"[ERROR] Login failed: {error_data.get('detail', f'HTTP {response.status_code}')}")
                
        except requests.exceptions.Timeout:
            print("[ERROR] Login timed out. Please try again.")
        except Exception as e:
            print(f"[ERROR] Login failed: {e}")
        
        return False
    
    def logout_user(self):
        """Logout user"""
        try:
            if self.auth_token:
                requests.post(
                    f"{self.api_base}/auth/logout",
                    headers={'Authorization': f'Bearer {self.auth_token}'},
                    timeout=5
                )
        except Exception:
            pass
        
        self.clear_session()
        print("[LOGOUT] Logged out successfully!")
    
    def show_user_profile(self):
        """Show user profile information"""
        if not self.current_user:
            print("[ERROR] Not logged in!")
            return
        
        print(f"\n[PROFILE] USER PROFILE")
        print("-" * 30)
        print(f"Username: {self.current_user.get('username', 'N/A')}")
        print(f"Email: {self.current_user.get('email', 'N/A')}")
        print(f"Member since: {self.current_user.get('created_at', 'N/A')}")
        if self.current_user.get('last_login'):
            print(f"Last login: {self.current_user.get('last_login', 'N/A')}")
    
    def show_user_stats(self):
        """Show user statistics"""
        if not self.auth_token:
            print("[ERROR] Not logged in!")
            return
        
        try:
            response = requests.get(
                f"{self.api_base}/auth/stats",
                headers={'Authorization': f'Bearer {self.auth_token}'},
                timeout=10
            )
            
            if response.ok:
                stats = response.json()
                print(f"\n[STATS] USER STATISTICS")
                print("-" * 30)
                print(f"Total Queries: {stats.get('total_queries', 0)}")
                print(f"Total Activities: {stats.get('total_activities', 0)}")
                print(f"Agents Used: {len(stats.get('agent_usage', {}))}")
                
                agent_usage = stats.get('agent_usage', {})
                if agent_usage:
                    print("\nMost Used Agents:")
                    sorted_agents = sorted(agent_usage.items(), key=lambda x: x[1], reverse=True)
                    for agent, count in sorted_agents[:5]:
                        print(f"  • {agent}: {count} queries")
            else:
                print("[ERROR] Failed to load statistics")
                
        except Exception as e:
            print(f"[ERROR] Error loading statistics: {e}")
    
    def show_query_history(self):
        """Show user query history"""
        if not self.auth_token:
            print("[ERROR] Not logged in!")
            return
        
        try:
            response = requests.get(
                f"{self.api_base}/auth/queries?limit=10",
                headers={'Authorization': f'Bearer {self.auth_token}'},
                timeout=10
            )
            
            if response.ok:
                queries = response.json()
                print(f"\n[HISTORY] RECENT QUERY HISTORY")
                print("-" * 40)
                
                if not queries:
                    print("No queries yet. Start asking questions!")
                    return
                
                for i, query in enumerate(queries, 1):
                    print(f"\n{i}. {query.get('question', 'N/A')[:80]}...")
                    print(f"   Agent: {query.get('agent_used', 'N/A')}")
                    print(f"   Date: {query.get('created_at', 'N/A')}")
                    if query.get('processing_time'):
                        print(f"   Time: {query.get('processing_time', 0):.2f}s")
            else:
                print("[ERROR] Failed to load query history")
                
        except Exception as e:
            print(f"[ERROR] Error loading query history: {e}")
    
    def process_query(self, question: str) -> Optional[Dict[str, Any]]:
        """Process query through authenticated API"""
        try:
            response = requests.post(
                f"{self.api_base}/run_graph",
                json={
                    'user': self.current_user['username'] if self.current_user else 'Anonymous',
                    'question': question
                },
                headers={'Authorization': f'Bearer {self.auth_token}'} if self.auth_token else {},
                timeout=180
            )
            
            if response.ok:
                return response.json()
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                print(f"[ERROR] Error: {error_data.get('detail', f'HTTP {response.status_code}')}")
                return None
                
        except requests.exceptions.Timeout:
            print("[ERROR] Query timed out. Please try again with a shorter question.")
            return None
        except Exception as e:
            print(f"[ERROR] Network error: {e}")
            return None
    
    def display_response(self, result: Dict[str, Any]):
        """Display AI response with proper formatting and error handling"""
        print("\n" + "="*80)
        print("[RESPONSE] AI RESPONSE RECEIVED!")
        print("="*80)
        
        # Handle error responses
        if result.get('error'):
            print(f"[ERROR] An error occurred: {result.get('response', 'Unknown error')}")
            print("="*80)
            return
        
        # Display metadata
        print(f"[USER] User: {result.get('user', 'N/A')}")
        print(f"[QUESTION] Question: {result.get('question', 'N/A')}")
        print(f"[AGENT] Agent: {result.get('agent', 'N/A')}")
        
        if result.get('edges_traversed'):
            print(f"[PATH] Agent Path: {' -> '.join(result['edges_traversed'])}")
        
        print(f"[TIME] Timestamp: {result.get('timestamp', 'N/A')}")
        
        # Get and clean the response
        response_text = result.get('response', 'No response')
        if response_text:
            # Clean any potential JSON formatting issues
            response_text = self._clean_response_text(response_text)
            print(f"[LENGTH] Response Length: {len(response_text)} characters")
            
            print("\n[RESPONSE] AI RESPONSE:")
            print("-" * 80)
            print(response_text)
            print("-" * 80)
        else:
            print("[WARNING] No response content received")
        
        print("="*80)
    
    def _clean_response_text(self, text: str) -> str:
        """Clean response text to ensure it's user-friendly and not JSON"""
        if not text or not isinstance(text, str):
            return "No response available"
        
        # Remove any JSON wrapper if present
        text = text.strip()
        if text.startswith('{') and text.endswith('}'):
            try:
                import json
                json_data = json.loads(text)
                # Extract actual response from common JSON keys
                if 'response' in json_data:
                    return str(json_data['response']).strip()
                elif 'content' in json_data:
                    return str(json_data['content']).strip()
                elif 'text' in json_data:
                    return str(json_data['text']).strip()
                elif 'message' in json_data:
                    return str(json_data['message']).strip()
            except (json.JSONDecodeError, KeyError, TypeError):
                # If JSON parsing fails, return original text
                pass
        
        # Clean up excessive whitespace
        lines = text.split('\n')
        cleaned_lines = [line.strip() for line in lines if line.strip()]
        
        return '\n'.join(cleaned_lines)
    
    def show_help(self):
        """Show help and example queries"""
        print("\n[HELP] HELP & EXAMPLE QUERIES:")
        print("=" * 50)
        print("[AUTH] AUTHENTICATION COMMANDS:")
        print("   • 'profile' - View your profile")
        print("   • 'stats' - View your statistics")
        print("   • 'history' - View query history")
        print("   • 'logout' - Logout from your account")
        print()
        print("[SCENIC] SCENIC & TRAVEL:")
        print("   • Find beautiful waterfalls in Iceland")
        print("   • Best scenic photography locations in Switzerland")
        print("   • Recommend hiking trails with mountain views")
        print("   • Where are the most beautiful lakes in Canada?")
        print()
        print("[WATER] WATER & AQUATIC:")
        print("   • What are the best mountain lakes for swimming?")
        print("   • Analyze water quality in Norwegian fjords")
        print("   • Tell me about Great Lakes ecosystem")
        print("   • Find pristine rivers for kayaking")
        print()
        print("[FOREST] FOREST & ECOLOGY:")
        print("   • Tell me about Amazon rainforest conservation")
        print("   • Analyze biodiversity in Canadian forests")
        print("   • What are sustainable forestry practices?")
        print("   • How to protect endangered forest species?")
        print()
        print("[SEARCH] SEARCH & HISTORY:")
        print("   • Search my previous conversations about lakes")
        print("   • What did I ask about forests before?")
        print("   • Find similar queries in my history")
        print()
        print("[AI] AI & TECHNOLOGY:")
        print("   • What is machine learning?")
        print("   • How do neural networks work?")
        print("   • Explain artificial intelligence simply")
        print("=" * 50)
        print()
    
    def authenticate(self) -> bool:
        """Handle user authentication"""
        if self.current_user:
            return True
        
        print("\n[AUTH] AUTHENTICATION REQUIRED")
        print("Please login or register to continue.")
        
        max_attempts = 5
        attempt = 0
        
        while attempt < max_attempts:
            try:
                choice = input("\nChoose an option:\n1. Login\n2. Register\n3. Exit\n\nEnter choice (1-3): ").strip()
                
                if choice == '1':
                    if self.login_user():
                        return True
                elif choice == '2':
                    if self.register_user():
                        return True
                elif choice == '3':
                    return False
                elif choice == '':
                    print("[ERROR] Please enter a choice (1-3)")
                else:
                    print("[ERROR] Invalid choice. Please enter 1, 2, or 3.")
                
                attempt += 1
                
            except (EOFError, KeyboardInterrupt):
                print("\n[GOODBYE] Goodbye!")
                return False
            except Exception as e:
                print(f"[ERROR] Input error: {e}")
                attempt += 1
        
        print("[ERROR] Too many invalid attempts. Exiting.")
        return False
    
    def interactive_session(self):
        """Main interactive session"""
        self.show_welcome()
        
        # Check authentication
        if not self.authenticate():
            print("\n[GOODBYE] Goodbye!")
            return
        
        print(f"\n[SUCCESS] Authenticated as: {self.current_user['username']}")
        print("=" * 70)
        print("[SESSION] INTERACTIVE QUERY SESSION STARTED")
        print("=" * 70)
        print("[HELP] Type your questions below. Available commands:")
        print("   • 'help' - Show help and examples")
        print("   • 'profile' - View your profile")
        print("   • 'stats' - View your statistics")  
        print("   • 'history' - View query history")
        print("   • 'logout' - Logout")
        print("   • 'quit', 'exit', or 'q' - Exit program")
        print()
        
        while True:
            try:
                print("[READY] Ready for your query!")
                query = input("[INPUT] Your question (or command): ").strip()
                
                if not query:
                    print("[ERROR] Please enter a question or command!\n")
                    continue
                
                # Handle commands
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                elif query.lower() == 'help':
                    self.show_help()
                    continue
                elif query.lower() == 'profile':
                    self.show_user_profile()
                    continue
                elif query.lower() == 'stats':
                    self.show_user_stats()
                    continue
                elif query.lower() == 'history':
                    self.show_query_history()
                    continue
                elif query.lower() == 'logout':
                    self.logout_user()
                    break
                
                # Process the query
                print(f"\n[PROCESSING] Processing your query...")
                print(f"[TIME] {datetime.now().strftime('%H:%M:%S')} - Sending to AI agents...")
                
                start_time = datetime.now()
                result = self.process_query(query)
                end_time = datetime.now()
                
                if result:
                    self.display_response(result)
                    processing_time = (end_time - start_time).total_seconds()
                    print(f"\n[TIMING] Processing time: {processing_time:.2f} seconds")
                else:
                    print("[ERROR] Failed to process query. Please try again.")
                
                print()
                
            except KeyboardInterrupt:
                print("\n\n[SESSION] Session ended by user.")
                break
            except Exception as e:
                print(f"\n[ERROR] Unexpected error: {e}")
                print("Please try again.\n")
        
        print("\n[GOODBYE] Thank you for using the LangGraph AI System!")
        print("[WEB] Web interface available at: http://localhost:8000")

def main():
    """Main entry point"""
    try:
        interface = AuthenticatedUserInterface()
        interface.interactive_session()
    except KeyboardInterrupt:
        print("\n\n[GOODBYE] Goodbye! Thanks for using LangGraph!")
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
