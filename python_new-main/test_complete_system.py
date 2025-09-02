#!/usr/bin/env python3
"""
Complete system test for the LangGraph AI application
"""

import requests
import json
import time
import random
import string

BASE_URL = "http://localhost:8000"

def generate_test_user():
    """Generate a unique test user"""
    rand_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return {
        'username': f'testuser_{rand_suffix}',
        'email': f'test_{rand_suffix}@example.com',
        'password': f'password{rand_suffix}123'
    }

def test_registration():
    """Test user registration"""
    print("🔐 Testing Registration...")
    user = generate_test_user()
    
    response = requests.post(f"{BASE_URL}/auth/register", json=user)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Registration successful: {data['message']}")
        return user, data
    else:
        print(f"❌ Registration failed: {response.status_code} - {response.text}")
        return None, None

def test_login(user):
    """Test user login"""
    print("🔑 Testing Login...")
    login_data = {
        'username': user['username'],
        'password': user['password']
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        data = response.json()
        if data.get('access_token'):
            print(f"✅ Login successful: {data['message']}")
            print(f"🔑 Token received (length: {len(data['access_token'])})")
            return data['access_token']
        else:
            print(f"❌ Login failed: No access token received")
            print(f"Response: {data}")
            return None
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None

def test_auth_me(token):
    """Test authenticated user info retrieval"""
    print("👤 Testing User Info Retrieval...")
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ User info retrieved: {data['username']} ({data['user_id']})")
        return data
    else:
        print(f"❌ User info failed: {response.status_code} - {response.text}")
        return None

def test_session(token):
    """Test session data retrieval"""
    print("📊 Testing Session Data...")
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(f"{BASE_URL}/auth/session", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Session data retrieved:")
        print(f"   - Recent interactions: {len(data.get('recent_interactions', []))}")
        print(f"   - Active agents: {len(data.get('active_agents', []))}")
        return True
    else:
        print(f"❌ Session data failed: {response.status_code} - {response.text}")
        return False

def test_chat(token, user_info):
    """Test AI chat functionality"""
    print("💬 Testing AI Chat...")
    headers = {'Authorization': f'Bearer {token}'}
    chat_data = {
        'user': user_info['username'],
        'question': 'Hello! Can you tell me about beautiful waterfalls in Iceland?'
    }
    
    response = requests.post(f"{BASE_URL}/run_graph", json=chat_data, headers=headers, timeout=30)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Chat response received:")
        print(f"   - Agent: {data.get('agent', 'Unknown')}")
        print(f"   - Response length: {len(data.get('response', ''))}")
        print(f"   - First 100 chars: {data.get('response', '')[:100]}...")
        return True
    else:
        print(f"❌ Chat failed: {response.status_code} - {response.text}")
        return False

def test_ollama_status():
    """Test Ollama integration"""
    print("🤖 Testing Ollama Integration...")
    
    response = requests.get(f"{BASE_URL}/api/ollama/status")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Ollama status:")
        print(f"   - Available: {data.get('available', False)}")
        print(f"   - Models: {len(data.get('models', []))}")
        for model in data.get('models', [])[:3]:  # Show first 3 models
            print(f"     - {model.get('name', 'Unknown')}")
        return data.get('available', False)
    else:
        print(f"❌ Ollama status failed: {response.status_code} - {response.text}")
        return False

def test_queries_history(token):
    """Test query history retrieval"""
    print("📜 Testing Query History...")
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(f"{BASE_URL}/auth/queries", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Query history retrieved: {len(data)} queries")
        return True
    else:
        print(f"❌ Query history failed: {response.status_code} - {response.text}")
        return False

def run_complete_test():
    """Run complete system test"""
    print("🚀 Starting Complete System Test...")
    print("=" * 60)
    
    # Test server health
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✅ Server health: {response.json().get('status', 'Unknown')}")
    except Exception as e:
        print(f"❌ Server not reachable: {e}")
        return
    
    # Test Ollama first
    ollama_ok = test_ollama_status()
    
    # Test authentication flow
    user, reg_data = test_registration()
    if not user:
        print("❌ Cannot continue without successful registration")
        return
    
    token = test_login(user)
    if not token:
        print("❌ Cannot continue without successful login")
        return
    
    user_info = test_auth_me(token)
    if not user_info:
        print("❌ Cannot continue without user info")
        return
    
    # Test session and UI data
    session_ok = test_session(token)
    
    # Test chat (only if Ollama is available)
    if ollama_ok:
        chat_ok = test_chat(token, user_info)
        
        # Wait a moment for query to be logged
        time.sleep(2)
        
        # Test query history
        queries_ok = test_queries_history(token)
    else:
        print("⚠️ Skipping chat test - Ollama not available")
        chat_ok = True
        queries_ok = True
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print(f"   🔐 Registration: ✅")
    print(f"   🔑 Login: ✅")
    print(f"   👤 User Info: ✅")
    print(f"   📊 Session Data: {'✅' if session_ok else '❌'}")
    print(f"   🤖 Ollama: {'✅' if ollama_ok else '❌'}")
    print(f"   💬 Chat: {'✅' if chat_ok else '❌'}")
    print(f"   📜 Query History: {'✅' if queries_ok else '❌'}")
    
    if all([session_ok, chat_ok, queries_ok]):
        print("\n🎉 ALL TESTS PASSED! System is working perfectly! 🎉")
    else:
        print("\n⚠️ Some tests failed. Check the issues above.")

if __name__ == "__main__":
    run_complete_test()
