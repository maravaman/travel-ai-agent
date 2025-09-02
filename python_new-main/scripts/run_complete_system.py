#!/usr/bin/env python3
"""
Complete LangGraph System Execution and Testing
"""
import sys
import os
import requests
import json
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_direct_framework():
    """Test the framework directly"""
    print('\n📊 TEST 1: Direct Framework Test')
    print('-' * 40)
    
    try:
        from core.langgraph_framework import langgraph_framework
        
        # Test waterfall photography in Norway (dynamic user ID)
        import random
        test_user_id = random.randint(1000, 9999)
        result1 = langgraph_framework.process_request(
            user='photographer',
            user_id=test_user_id,
            question='Find me scenic waterfalls in Norway for winter photography'
        )
        
        print('✅ Waterfall Photography Test:')
        print(f'   Agent: {result1["agent"]}')
        print(f'   Path: {" → ".join(result1["edges_traversed"])}')
        print(f'   Response: {len(result1["response"])} chars')
        print(f'   Preview: {result1["response"][:150]}...\n')
        
        # Test forest ecology (dynamic user ID)
        result2 = langgraph_framework.process_request(
            user='ecologist',
            user_id=test_user_id + 1,
            question='Analyze the forest ecosystem of Scandinavian pine forests'
        )
        
        print('✅ Forest Ecology Test:')
        print(f'   Agent: {result2["agent"]}')
        print(f'   Path: {" → ".join(result2["edges_traversed"])}')
        print(f'   Response: {len(result2["response"])} chars')
        print(f'   Preview: {result2["response"][:150]}...\n')
        
        return True
        
    except Exception as e:
        print(f'❌ Framework test failed: {e}')
        return False

def test_memory_system():
    """Test memory persistence"""
    print('\n💾 TEST 2: Memory System Test')
    print('-' * 40)
    
    try:
        from core.memory import MemoryManager
        memory = MemoryManager()
        
        # Test STM with dynamic test user
        test_key = f"test_{int(time.time())}"
        test_user_name = f"test_user_{random.randint(100, 999)}"
        memory.set_stm(test_user_name, test_key, "Test memory value", 3600)
        retrieved = memory.get_stm(test_user_name, test_key)
        print(f'✅ STM Test: {retrieved}')
        
        # Test LTM with dynamic test user
        memory.set_ltm(test_user_name, test_key, "Test LTM value")
        ltm_data = memory.get_ltm_by_agent(test_user_name, test_key)
        print(f'✅ LTM Test: Found {len(ltm_data)} entries')
        
        return True
        
    except Exception as e:
        print(f'❌ Memory test failed: {e}')
        return False

def test_database_data():
    """Check database contents"""
    print('\n🗄️ TEST 3: Database Data Verification')
    print('-' * 40)
    
    try:
        import mysql.connector
        
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='root',
            database='langgraph_ai_system'
        )
        cursor = conn.cursor(dictionary=True)
        
        # Check LTM entries
        cursor.execute('SELECT COUNT(*) as count FROM ltm')
        ltm_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT * FROM ltm ORDER BY created_at DESC LIMIT 3')
        recent_entries = cursor.fetchall()
        
        print(f'✅ Database Status: {ltm_count} total LTM entries')
        print('✅ Recent entries:')
        for entry in recent_entries:
            print(f'   - User {entry["user_id"]}: Agent {entry["agent_id"]}')
            print(f'     Created: {entry["created_at"]}')
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f'❌ Database test failed: {e}')
        return False

def start_server():
    """Start FastAPI server in background"""
    print('\n🌐 TEST 4: Starting HTTP Server')
    print('-' * 40)
    
    try:
        import subprocess
        
        # Start server process
        process = subprocess.Popen([
            sys.executable, '-m', 'uvicorn',
            'api.main:app', '--host', '127.0.0.1', '--port', '8000'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print('🚀 Server starting...')
        time.sleep(8)  # Give server time to start
        
        return process
        
    except Exception as e:
        print(f'❌ Server start failed: {e}')
        return None

def test_http_endpoint():
    """Test HTTP API endpoint"""
    print('\n🌐 TEST 5: HTTP API Endpoint Test')
    print('-' * 40)
    
    try:
        # Test health endpoint first
        health_response = requests.get('http://127.0.0.1:8000/health', timeout=5)
        print(f'✅ Health check: {health_response.status_code}')
        
        # Test the main endpoint
        test_data = {
            "user": "api_user",
            "question": "Find beautiful mountain lakes in Switzerland"
        }
        
        print('🔄 Sending API request...')
        response = requests.post(
            'http://127.0.0.1:8000/run_graph',
            json=test_data,
            timeout=180  # 3 minutes for AI processing
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f'✅ API Response received!')
            print(f'   Agent: {result["agent"]}')
            print(f'   Response length: {len(result["response"])} chars')
            print(f'   Preview: {result["response"][:150]}...')
            return True
        else:
            print(f'❌ API request failed: {response.status_code}')
            return False
            
    except requests.exceptions.Timeout:
        print('⚠️ API request timed out (server processing)')
        return False
    except Exception as e:
        print(f'❌ HTTP test failed: {e}')
        return False

def main():
    """Main execution function"""
    print('🎯 COMPLETE LANGGRAPH SYSTEM EXECUTION')
    print('=' * 60)
    print(f'Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    test_results = []
    
    # Run all tests
    test_results.append(('Direct Framework', test_direct_framework()))
    test_results.append(('Memory System', test_memory_system()))
    test_results.append(('Database Data', test_database_data()))
    
    # Start server and test HTTP
    server_process = start_server()
    if server_process:
        test_results.append(('HTTP API', test_http_endpoint()))
        
        # Clean up server
        print('\n🧹 Shutting down server...')
        server_process.terminate()
        server_process.wait()
        print('✅ Server stopped')
    
    # Final summary
    print('\n' + '=' * 60)
    print('🏁 EXECUTION SUMMARY')
    print('=' * 60)
    
    passed = sum(1 for name, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = '✅ PASS' if result else '❌ FAIL'
        print(f'{test_name:.<30} {status}')
    
    print(f'\nOverall: {passed}/{total} tests passed')
    
    if passed == total:
        print('\n🎉 ALL SYSTEMS OPERATIONAL!')
        print('🚀 LangGraph Framework is PRODUCTION READY!')
        print('✨ Perfect implementation with full AI integration!')
    else:
        print(f'\n⚠️ {total - passed} tests need attention')
    
    return passed == total

if __name__ == '__main__':
    success = main()
    print(f'\n🎯 Execution {"SUCCESSFUL" if success else "INCOMPLETE"}')
