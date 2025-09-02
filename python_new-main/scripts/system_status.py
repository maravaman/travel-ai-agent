#!/usr/bin/env python3
"""
System Status Checker
Validates configuration and system health
"""

import json
import sys
from pathlib import Path
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_json_config():
    """Validate JSON configuration"""
    config_path = "core/agents.json"
    
    print("🔍 Checking JSON configuration...")
    
    try:
        if not Path(config_path).exists():
            print(f"❌ Configuration file not found: {config_path}")
            return False
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Validate structure
        required_keys = ['entry_point', 'version', 'agents']
        for key in required_keys:
            if key not in config:
                print(f"❌ Missing required key: {key}")
                return False
        
        agents = config['agents']
        if not isinstance(agents, list) or len(agents) == 0:
            print("❌ No agents configured")
            return False
        
        # Validate each agent
        for i, agent in enumerate(agents):
            required_agent_keys = ['id', 'name', 'description', 'capabilities', 'keywords', 'priority', 'system_prompt_template']
            for key in required_agent_keys:
                if key not in agent:
                    print(f"❌ Agent {i}: Missing required key: {key}")
                    return False
        
        print(f"✅ JSON configuration valid")
        print(f"📊 Found {len(agents)} agents:")
        for agent in agents:
            print(f"   • {agent['name']} ({agent['id']})")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON syntax error: {e}")
        return False
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def check_system_loading():
    """Test system loading"""
    print("\n🔄 Testing system loading...")
    
    try:
        from core.langgraph_multiagent_system import langgraph_multiagent_system
        
        if not langgraph_multiagent_system.agents_config:
            print("❌ No agents loaded in system")
            return False
        
        print(f"✅ System loaded successfully")
        print(f"🤖 {len(langgraph_multiagent_system.agents_config)} agents loaded:")
        for agent_id, config in langgraph_multiagent_system.agents_config.items():
            print(f"   • {config.get('name', agent_id)} - {len(config.get('keywords', []))} keywords")
        
        return True
        
    except Exception as e:
        print(f"❌ System loading failed: {e}")
        return False

def check_dependencies():
    """Check required dependencies"""
    print("\n📦 Checking dependencies...")
    
    required_modules = [
        'langgraph',
        'ollama', 
        'redis',
        'mysql'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} - not installed")
            missing.append(module)
    
    if missing:
        print(f"\n⚠️ Missing dependencies: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False
    
    return True

def test_basic_query():
    """Test basic system functionality"""
    print("\n🧪 Testing basic query processing...")
    
    try:
        from core.langgraph_multiagent_system import langgraph_multiagent_system
        
        # Test a simple query
        test_query = "Hello, can you help me with travel planning?"
        
        # Just test routing, not full processing (which requires Ollama)
        routing_decision = langgraph_multiagent_system._analyze_query_for_routing(test_query)
        
        print(f"✅ Query routing test passed")
        print(f"📍 Test query: '{test_query}'")
        print(f"🎯 Routed to: {routing_decision}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic query test failed: {e}")
        return False

def main():
    """Run system status check"""
    print("🔧 JSON-Configurable Multi-Agent System Status Check")
    print("=" * 55)
    
    checks = [
        ("JSON Configuration", check_json_config),
        ("Dependencies", check_dependencies), 
        ("System Loading", check_system_loading),
        ("Basic Query Test", test_basic_query)
    ]
    
    results = []
    for check_name, check_func in checks:
        success = check_func()
        results.append((check_name, success))
    
    print("\n" + "=" * 55)
    print("📋 SYSTEM STATUS SUMMARY:")
    
    all_passed = True
    for check_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {check_name}: {status}")
        if not success:
            all_passed = False
    
    print("\n" + "=" * 55)
    if all_passed:
        print("🎉 ALL CHECKS PASSED - System ready!")
        print("🚀 Start the system with: python scripts/run.py")
    else:
        print("⚠️ SOME CHECKS FAILED - Review issues above")
        print("📖 See CLIENT_SYSTEM_GUIDE.md for troubleshooting")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
