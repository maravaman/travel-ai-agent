#!/usr/bin/env python3
"""
[SYSTEM] LangGraph User Query Interface - Windows Compatible
Interactive interface for users to enter queries and get AI responses
"""
import sys
import os
from datetime import datetime
import requests
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def show_welcome():
    """Show welcome message and instructions"""
    print("[SYSTEM] LANGGRAPH AI SYSTEM - USER QUERY INTERFACE")
    print("=" * 70)
    print("[INFO] Welcome! You can ask questions about:")
    print("   *  Scenic locations and travel destinations")
    print("   *  Water bodies, lakes, rivers, and aquatic ecosystems") 
    print("   *  Forests, ecology, and conservation")
    print("   *  Search your conversation history")
    print("   *  General AI and technology questions")
    print()
    print("[INFO] The system automatically routes to the best specialized agent!")
    print("=" * 70)
    print()

def show_available_interfaces():
    """Show all available interfaces"""
    print("[INTERFACES] AVAILABLE INTERFACES:")
    print("-" * 40)
    print("1. [TERMINAL] This Interactive Terminal")
    print("2. [WEB] Web Interface: http://localhost:8000")
    print("3. [API] HTTP API: POST /run_graph")
    print("4. [PYTHON] Direct: langgraph_framework.process_request()")
    print("-" * 40)
    print()

def test_framework_direct():
    """Test direct framework access"""
    try:
        from core.langgraph_framework import langgraph_framework
        print("[PASS] Direct Framework Access: Available")
        return True
    except Exception as e:
        print(f"[FAIL] Direct Framework Access: Error - {e}")
        return False

def test_http_api():
    """Test HTTP API access"""
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=3)
        if response.status_code == 200:
            print("[PASS] HTTP API Server: Running on http://localhost:8000")
            return True
        else:
            print(f"[FAIL] HTTP API Server: Error {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] HTTP API Server: Not accessible - {e}")
        return False

def process_query_direct(user_name, query):
    """Process query using direct framework access"""
    try:
        from core.langgraph_framework import langgraph_framework
        
        result = langgraph_framework.process_request(
            user=user_name,
            user_id=int(datetime.now().timestamp()),
            question=query
        )
        
        return result, None
    except Exception as e:
        return None, str(e)

def process_query_http(user_name, query):
    """Process query using HTTP API"""
    try:
        data = {
            "user": user_name,
            "question": query
        }
        
        response = requests.post(
            "http://127.0.0.1:8000/run_graph_legacy",  # Use legacy endpoint to avoid auth
            json=data,
            timeout=180  # 3 minutes
        )
        
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"HTTP Error {response.status_code}: {response.text}"
            
    except Exception as e:
        return None, str(e)

def display_response(result):
    """Display the AI response beautifully"""
    print("\n" + "="*80)
    print("[RESPONSE] AI RESPONSE RECEIVED!")
    print("="*80)
    
    print(f"[USER] User: {result['user']}")
    print(f"[QUESTION] Question: {result['question']}")
    print(f"[AGENT] Agent: {result['agent']}")
    if result.get('edges_traversed'):
        print(f"[PATH] Agent Path: {' -> '.join(result['edges_traversed'])}")
    print(f"[TIME] Timestamp: {result['timestamp']}")
    print(f"[LENGTH] Response Length: {len(result['response'])} characters")
    
    print("\n[RESPONSE] FULL AI RESPONSE:")
    print("-" * 80)
    
    # Clean response text for better display
    response_text = result['response']
    if response_text.startswith('{') and response_text.endswith('}'):
        try:
            json_data = json.loads(response_text)
            if 'response' in json_data:
                response_text = json_data['response']
            elif 'content' in json_data:
                response_text = json_data['content']
            elif 'text' in json_data:
                response_text = json_data['text']
        except json.JSONDecodeError:
            pass
    
    print(response_text)
    print("-" * 80)
    
    # Show memory status if available
    if 'context' in result:
        stm_count = result['context'].get('stm', {}).get('count', 0)
        ltm_count = result['context'].get('ltm', {}).get('count', 0)
        print(f"\n[MEMORY] Memory Status: STM={stm_count} entries, LTM={ltm_count} entries")
    
    print("="*80)

def interactive_session():
    """Main interactive session"""
    show_welcome()
    
    # Test interfaces
    print("[STATUS] CHECKING SYSTEM STATUS:")
    print("-" * 40)
    direct_available = test_framework_direct()
    http_available = test_http_api()
    print()
    
    if not direct_available and not http_available:
        print("[ERROR] ERROR: No interfaces available!")
        print("Please ensure the system is properly set up.")
        return
    
    show_available_interfaces()
    
    # Choose interface
    if direct_available and http_available:
        print("[INFO] Both interfaces available! Using Direct Framework for best performance.")
        use_interface = "direct"
    elif direct_available:
        print("[INFO] Using Direct Framework interface.")
        use_interface = "direct"
    else:
        print("[INFO] Using HTTP API interface.")
        use_interface = "http"
    
    print("\n" + "="*70)
    print("[SESSION] INTERACTIVE QUERY SESSION STARTED")
    print("="*70)
    print("[HELP] Type your questions below. Type 'quit', 'exit', or 'q' to stop.")
    print("[HELP] Type 'help' for example queries.")
    print()
    
    while True:
        try:
            # Get user input
            print("[READY] Ready for your query!")
            user_name = input("[INPUT] Your name (press Enter for 'User'): ").strip() or "User"
            
            if user_name.lower() in ['quit', 'exit', 'q']:
                break
                
            if user_name.lower() == 'help':
                show_help()
                continue
            
            query = input("[INPUT] Your question: ").strip()
            
            if not query:
                print("[ERROR] Please enter a question!\n")
                continue
                
            if query.lower() in ['quit', 'exit', 'q']:
                break
                
            if query.lower() == 'help':
                show_help()
                continue
            
            # Process the query
            print(f"\n[PROCESSING] Processing your query using {use_interface} interface...")
            print(f"[TIME] {datetime.now().strftime('%H:%M:%S')} - Sending to AI agents...")
            
            start_time = datetime.now()
            
            if use_interface == "direct":
                result, error = process_query_direct(user_name, query)
            else:
                result, error = process_query_http(user_name, query)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            if error:
                print(f"[ERROR] Error: {error}")
                print("Please try again with a different query.\n")
                continue
            
            # Display results
            display_response(result)
            print(f"\n[TIMING] Processing time: {processing_time:.2f} seconds")
            print()
            
        except KeyboardInterrupt:
            print("\n\n[EXIT] Session ended by user.")
            break
        except Exception as e:
            print(f"\n[ERROR] Unexpected error: {e}")
            print("Please try again.\n")
    
    print("\n[GOODBYE] Thank you for using the LangGraph AI System!")
    print("[WEB] Web interface available at: http://localhost:8000")

def show_help():
    """Show example queries"""
    print("\n[HELP] EXAMPLE QUERIES:")
    print("=" * 50)
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

if __name__ == "__main__":
    try:
        interactive_session()
    except KeyboardInterrupt:
        print("\n\n[GOODBYE] Goodbye! Thanks for using LangGraph!")
