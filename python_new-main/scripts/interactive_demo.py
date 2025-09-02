#!/usr/bin/env python3
"""
Interactive LangGraph Demo - User Query Interface
Users can enter queries here and see real AI responses
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def interactive_demo():
    """Interactive demo where users can enter queries"""
    print("🎯 LANGGRAPH INTERACTIVE DEMO")
    print("=" * 60)
    print("Welcome! Enter your queries to get AI responses from specialized agents.")
    print("The system will automatically route to the best agent and provide detailed responses.")
    print("Type 'quit' to exit, 'help' for examples, 'stats' for system statistics.\n")
    
    from core.langgraph_framework import langgraph_framework
    
    import random
    user_id_counter = random.randint(1000, 9999)
    
    while True:
        try:
            # Get user input
            print("🤖 Ready for your query!")
            user_name = input("👤 Your name (or press Enter for 'user'): ").strip() or "user"
            
            if user_name.lower() in ['quit', 'exit', 'q']:
                break
                
            if user_name.lower() == 'help':
                show_help()
                continue
                
            if user_name.lower() == 'stats':
                show_stats()
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
            print(f"\n🔄 Processing your query...")
            print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - Sending to LangGraph framework...")
            
            result = langgraph_framework.process_request(
                user=user_name,
                user_id=user_id_counter,
                question=query
            )
            
            user_id_counter = random.randint(1000, 9999)
            
            # Display results
            print("\n" + "="*80)
            print("🎉 AI RESPONSE RECEIVED!")
            print("="*80)
            print(f"👤 User: {user_name}")
            print(f"❓ Question: {query}")
            print(f"🤖 Agent: {result['agent']}")
            print(f"🔗 Agent Path: {' → '.join(result['edges_traversed'])}")
            print(f"⏰ Timestamp: {result['timestamp']}")
            print(f"📊 Response Length: {len(result['response'])} characters")
            print("\n📝 FULL AI RESPONSE:")
            print("-" * 40)
            print(result['response'])
            print("-" * 40)
            
            # Show memory status
            stm_count = result['context']['stm']['count']
            ltm_count = result['context']['ltm']['count']
            print(f"\n💾 Memory Status: STM={stm_count} entries, LTM={ltm_count} entries")
            print("="*80)
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Thanks for using LangGraph!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again with a different query.\n")

def show_help():
    """Show example queries"""
    print("\n📚 EXAMPLE QUERIES:")
    print("-" * 40)
    print("🏞️  Water/Nature Queries:")
    print("   • Find beautiful waterfalls in Iceland")
    print("   • What are the best mountain lakes for swimming?")
    print("   • Analyze water quality in Norwegian fjords")
    print()
    print("🌲 Forest/Ecology Queries:")
    print("   • Tell me about Amazon rainforest conservation")
    print("   • Analyze biodiversity in Canadian forests")
    print("   • What are sustainable forestry practices?")
    print()
    print("📍 Scenic/Travel Queries:")
    print("   • Find scenic photography locations in Switzerland")
    print("   • Best places for landscape photography in winter")
    print("   • Recommend hiking trails with beautiful views")
    print()
    print("🤖 General AI/Tech Queries:")
    print("   • What is machine learning?")
    print("   • How does artificial intelligence work?")
    print("   • Explain neural networks simply")
    print("-" * 40)
    print("💡 The system automatically chooses the best agent for your query!\n")

def show_stats():
    """Show system statistics"""
    try:
        import mysql.connector
        
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='root',
            database='langgraph_ai_system'
        )
        cursor = conn.cursor(dictionary=True)
        
        # Get total queries
        cursor.execute("SELECT COUNT(*) as total FROM ltm")
        total_queries = cursor.fetchone()['total']
        
        # Get queries by agent
        cursor.execute("""
            SELECT agent_id, COUNT(*) as count 
            FROM ltm 
            GROUP BY agent_id 
            ORDER BY count DESC
        """)
        agent_stats = cursor.fetchall()
        
        # Get recent activity
        cursor.execute("""
            SELECT user_id, agent_id, created_at 
            FROM ltm 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        recent_activity = cursor.fetchall()
        
        print("\n📊 SYSTEM STATISTICS:")
        print("-" * 40)
        print(f"📈 Total Queries Processed: {total_queries}")
        print(f"🤖 Agent Usage:")
        for stat in agent_stats:
            print(f"   • {stat['agent_id']}: {stat['count']} queries")
        
        print(f"\n⏰ Recent Activity:")
        for activity in recent_activity:
            print(f"   • User {activity['user_id']} → {activity['agent_id']} ({activity['created_at']})")
        
        cursor.close()
        conn.close()
        print("-" * 40)
        print()
        
    except Exception as e:
        print(f"\n❌ Could not fetch stats: {e}\n")

if __name__ == "__main__":
    try:
        interactive_demo()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye! Thanks for using LangGraph!")
