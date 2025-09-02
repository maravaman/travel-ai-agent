#!/usr/bin/env python3
"""
🎯 LangGraph User Query Interface
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
    print("📱 AVAILABLE INTERFACES:")
    print("-" * 40)
    print("1. 🖥️  This Interactive Terminal")
    print("2. 🌐 Web Interface: http://localhost:8000")
    print("3. 🔗 HTTP API: POST /run_graph")
    print("4. 🐍 Python: langgraph_framework.process_request()")
    print("-" * 40)
    print()

def test_framework_direct():
    """Test direct framework access"""
    try:
        from core.langgraph_framework import langgraph_framework
        print("✅ Direct Framework Access: Available")
        return True
    except Exception as e:
        print(f"❌ Direct Framework Access: Error - {e}")
        return False

def test_http_api():
    """Test HTTP API access"""
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=3)
        if response.status_code == 200:
            print("✅ HTTP API Server: Running on http://localhost:8000")
            return True
        else:
            print(f"❌ HTTP API Server: Error {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ HTTP API Server: Not accessible - {e}")
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
            "http://127.0.0.1:8000/run_graph",
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
    print("🎉 AI RESPONSE RECEIVED!")
    print("="*80)
    
    print(f"👤 User: {result['user']}")
    print(f"❓ Question: {result['question']}")
    print(f"🤖 Agent: {result['agent']}")
    print(f"🔗 Agent Path: {' → '.join(result['edges_traversed'])}")
    print(f"⏰ Timestamp: {result['timestamp']}")
    print(f"📊 Response Length: {len(result['response'])} characters")
    
    print("\n📝 FULL AI RESPONSE:")
    print("-" * 80)
    print(result['response'])
    print("-" * 80)
    
    # Show memory status if available
    if 'context' in result:
        stm_count = result['context'].get('stm', {}).get('count', 0)
        ltm_count = result['context'].get('ltm', {}).get('count', 0)
        print(f"\n💾 Memory Status: STM={stm_count} entries, LTM={ltm_count} entries")
    
    print("="*80)

def interactive_session():
    """Main interactive session"""
    show_welcome()
    
    # Test interfaces
    print("🔧 CHECKING SYSTEM STATUS:")
    print("-" * 40)
    direct_available = test_framework_direct()
    http_available = test_http_api()
    print()
    
    if not direct_available and not http_available:
        print("❌ ERROR: No interfaces available!")
        print("Please ensure the system is properly set up.")
        return
    
    show_available_interfaces()
    
    # Choose interface
    if direct_available and http_available:
        print("🚀 Both interfaces available! Using Direct Framework for best performance.")
        use_interface = "direct"
    elif direct_available:
        print("🚀 Using Direct Framework interface.")
        use_interface = "direct"
    else:
        print("🚀 Using HTTP API interface.")
        use_interface = "http"
    
    print("\n" + "="*70)
    print("💬 INTERACTIVE QUERY SESSION STARTED")
    print("="*70)
    print("📝 Type your questions below. Type 'quit', 'exit', or 'q' to stop.")
    print("📝 Type 'help' for example queries.")
    print()
    
    while True:
        try:
            # Get user input
            print("🎤 Ready for your query!")
            user_name = input("👤 Your name (press Enter for 'User'): ").strip() or "User"
            
            if user_name.lower() in ['quit', 'exit', 'q']:
                break
                
            if user_name.lower() == 'help':
                show_help()
                continue
            
            query = input("💭 Your question: ").strip()
            
            if not query:
                print("❌ Please enter a question!\n")
                continue
                
            if query.lower() in ['quit', 'exit', 'q']:
                break
                
            if query.lower() == 'help':
                show_help()
                continue
            
            # Process the query
            print(f"\n🔄 Processing your query using {use_interface} interface...")
            print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - Sending to AI agents...")
            
            start_time = datetime.now()
            
            if use_interface == "direct":
                result, error = process_query_direct(user_name, query)
            else:
                result, error = process_query_http(user_name, query)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            if error:
                print(f"❌ Error: {error}")
                print("Please try again with a different query.\n")
                continue
            
            # Display results
            display_response(result)
            print(f"\n⚡ Processing time: {processing_time:.2f} seconds")
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Session ended by user.")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            print("Please try again.\n")
    
    print("\n👋 Thank you for using the LangGraph AI System!")
    print("🌐 Web interface available at: http://localhost:8000")

def show_help():
    """Show example queries"""
    print("\n📚 EXAMPLE QUERIES:")
    print("=" * 50)
    print("🏞️  SCENIC & TRAVEL:")
    print("   • Find beautiful waterfalls in Iceland")
    print("   • Best scenic photography locations in Switzerland")
    print("   • Recommend hiking trails with mountain views")
    print("   • Where are the most beautiful lakes in Canada?")
    print()
    print("🌊 WATER & AQUATIC:")
    print("   • What are the best mountain lakes for swimming?")
    print("   • Analyze water quality in Norwegian fjords")
    print("   • Tell me about Great Lakes ecosystem")
    print("   • Find pristine rivers for kayaking")
    print()
    print("🌲 FOREST & ECOLOGY:")
    print("   • Tell me about Amazon rainforest conservation")
    print("   • Analyze biodiversity in Canadian forests")
    print("   • What are sustainable forestry practices?")
    print("   • How to protect endangered forest species?")
    print()
    print("🔍 SEARCH & HISTORY:")
    print("   • Search my previous conversations about lakes")
    print("   • What did I ask about forests before?")
    print("   • Find similar queries in my history")
    print()
    print("🤖 AI & TECHNOLOGY:")
    print("   • What is machine learning?")
    print("   • How do neural networks work?")
    print("   • Explain artificial intelligence simply")
    print("=" * 50)
    print()

if __name__ == "__main__":
    try:
        interactive_session()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye! Thanks for using LangGraph!")
