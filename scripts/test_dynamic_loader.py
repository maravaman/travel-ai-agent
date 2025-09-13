#!/usr/bin/env python3
"""
Test script for Dynamic Agent Loader
Demonstrates dynamic loading and execution of .py agent files using JSON configuration
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.dynamic_agent_loader import DynamicAgentLoader, get_dynamic_agent_loader
from core.memory import MemoryManager

def test_dynamic_loading():
    """Test dynamic agent loading from JSON configuration"""
    print("🚀 Testing Dynamic Agent Loading with Reflection")
    print("=" * 60)
    
    try:
        # Initialize memory manager
        memory_manager = MemoryManager()
        
        # Create dynamic agent loader
        loader = DynamicAgentLoader(
            config_file="core/dynamic_agents.json",
            memory_manager=memory_manager
        )
        
        print(f"✅ Dynamic Agent Loader initialized")
        print(f"📊 Loaded {len(loader.get_all_agents())} agents from JSON configuration")
        
        # List loaded agents
        print(f"\n📋 Loaded Agents:")
        for agent_name in loader.get_agent_names():
            agent_info = loader.get_agent_info(agent_name)
            print(f"   • {agent_name}: {agent_info['description']}")
            print(f"     Capabilities: {', '.join(agent_info['capabilities'])}")
            print(f"     Keywords: {', '.join(agent_info['keywords'][:5])}...")
        
        return loader
        
    except Exception as e:
        print(f"❌ Dynamic loading failed: {e}")
        return None

def test_agent_execution(loader: DynamicAgentLoader):
    """Test executing agents dynamically"""
    print(f"\n🧪 Testing Dynamic Agent Execution")
    print("=" * 40)
    
    test_queries = [
        ("I'm planning a trip to Japan and feeling overwhelmed with choices", ["TripMoodDetector", "TripBehaviorGuide"]),
        ("How should I communicate with hotel staff about dietary restrictions?", ["TripCommsCoach"]),
        ("I need help organizing my travel planning process", ["TripBehaviorGuide", "TripSummarySynth"]),
        ("I'm stressed about my upcoming vacation planning", ["TripCalmPractice", "TripMoodDetector"])
    ]
    
    for query, expected_agents in test_queries:
        print(f"\n🔍 Testing Query: '{query[:50]}...'")
        
        # Test keyword-based execution
        result = loader.execute_by_keywords(query, user_id=1001, max_agents=2)
        
        if result.get("individual_results"):
            successful_agents = [r["agent"] for r in result["individual_results"] if r["success"]]
            print(f"✅ Executed agents: {successful_agents}")
            print(f"⏱️ Total processing time: {result['total_processing_time']:.2f}s")
            
            # Show first response preview
            for agent_result in result["individual_results"]:
                if agent_result["success"]:
                    response_preview = agent_result["response"][:100] + "..." if len(agent_result["response"]) > 100 else agent_result["response"]
                    print(f"   📝 {agent_result['agent']}: {response_preview}")
        else:
            print(f"❌ No agents executed for query")

def test_capability_execution(loader: DynamicAgentLoader):
    """Test executing agents by capability"""
    print(f"\n🎯 Testing Capability-Based Execution")
    print("=" * 40)
    
    capabilities_to_test = [
        "mood_detection",
        "communication_coaching", 
        "stress_relief",
        "behavioral_guidance"
    ]
    
    for capability in capabilities_to_test:
        print(f"\n🔧 Testing capability: {capability}")
        
        # Get agents with this capability
        matching_agents = loader.get_agents_by_capability(capability)
        print(f"   Agents with capability: {matching_agents}")
        
        if matching_agents:
            # Execute with test query
            test_query = f"I need help with {capability.replace('_', ' ')}"
            result = loader.execute_by_capability(capability, test_query, user_id=1002)
            
            if result.get("successful_executions", 0) > 0:
                print(f"   ✅ Successfully executed {result['successful_executions']} agents")
            else:
                print(f"   ❌ No successful executions")

def test_entry_point_execution(loader: DynamicAgentLoader):
    """Test executing entry points in agent modules"""
    print(f"\n🎬 Testing Entry Point Execution")
    print("=" * 40)
    
    for agent_name in loader.get_agent_names():
        print(f"\n🎯 Testing entry point for: {agent_name}")
        
        # List available functions
        functions = loader.list_available_functions(agent_name)
        print(f"   Available functions: {functions}")
        
        # Try to execute entry point
        try:
            result = loader.execute_entry_point(agent_name, "test_query", user_id=1003)
            if result is not None:
                print(f"   ✅ Entry point executed successfully")
            else:
                print(f"   ℹ️ Entry point returned None (may be normal)")
        except Exception as e:
            print(f"   ⚠️ Entry point execution: {e}")

def test_configuration_validation(loader: DynamicAgentLoader):
    """Test configuration validation"""
    print(f"\n🔍 Testing Configuration Validation")
    print("=" * 40)
    
    validation = loader.validate_configuration()
    
    print(f"Overall Valid: {'✅' if validation['valid'] else '❌'}")
    
    if validation["errors"]:
        print(f"\n❌ Errors:")
        for error in validation["errors"]:
            print(f"   • {error}")
    
    if validation["warnings"]:
        print(f"\n⚠️ Warnings:")
        for warning in validation["warnings"]:
            print(f"   • {warning}")
    
    print(f"\n📊 Agent Validations:")
    for agent_name, agent_val in validation["agent_validations"].items():
        status_items = []
        for check, passed in agent_val.items():
            status_items.append(f"{check}: {'✅' if passed else '❌'}")
        print(f"   • {agent_name}: {', '.join(status_items)}")

def test_hot_reload(loader: DynamicAgentLoader):
    """Test hot reloading of agents"""
    print(f"\n🔄 Testing Hot Reload Functionality")
    print("=" * 40)
    
    # Test reloading specific agent
    agent_to_reload = "TripMoodDetector"
    print(f"🔄 Reloading agent: {agent_to_reload}")
    
    success = loader.reload_agent(agent_to_reload)
    print(f"   {'✅' if success else '❌'} Reload result: {success}")
    
    # Test reloading all agents
    print(f"\n🔄 Reloading all agents...")
    reload_results = loader.reload_all_agents()
    
    successful_reloads = sum(1 for success in reload_results.values() if success)
    print(f"   📊 Reloaded {successful_reloads}/{len(reload_results)} agents successfully")
    
    for agent_name, success in reload_results.items():
        print(f"   {'✅' if success else '❌'} {agent_name}")

def test_dynamic_agent_addition():
    """Test adding new agent dynamically"""
    print(f"\n➕ Testing Dynamic Agent Addition")
    print("=" * 40)
    
    loader = get_dynamic_agent_loader()
    
    # Create new agent configuration
    new_agent_config = {
        "name": "TestDynamicAgent",
        "file_path": "agents/text_trip_analyzer.py",  # Reuse existing file for test
        "class_name": "TextTripAnalyzerAgent",
        "enabled": True,
        "priority": 3,
        "entry_point": "main",
        "description": "Dynamically added test agent",
        "capabilities": ["dynamic_testing"],
        "keywords": ["dynamic", "test", "runtime"],
        "execution_settings": {
            "timeout_seconds": 15,
            "temperature": 0.5,
            "max_tokens": 1000
        }
    }
    
    # Add agent dynamically
    success = loader.add_agent_dynamically(new_agent_config)
    print(f"   {'✅' if success else '❌'} Dynamic addition result: {success}")
    
    if success:
        print(f"   📊 Total agents after addition: {len(loader.get_all_agents())}")
        
        # Test executing the new agent
        result = loader.execute_agent("TestDynamicAgent", "test dynamic execution", user_id=1004)
        print(f"   {'✅' if result['success'] else '❌'} Dynamic agent execution: {result['success']}")
        
        # Remove the test agent
        loader.remove_agent("TestDynamicAgent")
        print(f"   🗑️ Test agent removed")

def show_statistics(loader: DynamicAgentLoader):
    """Show loader statistics"""
    print(f"\n📊 Dynamic Agent Loader Statistics")
    print("=" * 40)
    
    stats = loader.get_agent_statistics()
    
    print(f"Total Agents Loaded: {stats['total_agents_loaded']}")
    print(f"Total Executions: {stats['total_executions']}")
    print(f"Successful Executions: {stats['successful_executions']}")
    print(f"Success Rate: {stats['success_rate']:.2%}")
    print(f"Config File: {stats['config_file']}")
    
    if stats["agent_execution_counts"]:
        print(f"\nAgent Execution Counts:")
        for agent, count in stats["agent_execution_counts"].items():
            print(f"   • {agent}: {count} executions")

def main():
    """Main test function"""
    print("🎯 DYNAMIC AGENT LOADER - COMPREHENSIVE TEST")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test dynamic loading
    loader = test_dynamic_loading()
    if not loader:
        print("❌ Cannot continue without successful loader initialization")
        return
    
    # Test various execution methods
    test_agent_execution(loader)
    test_capability_execution(loader)
    test_entry_point_execution(loader)
    
    # Test configuration and validation
    test_configuration_validation(loader)
    
    # Test hot reload functionality
    test_hot_reload(loader)
    
    # Test dynamic agent addition
    test_dynamic_agent_addition()
    
    # Show final statistics
    show_statistics(loader)
    
    print(f"\n🎉 Dynamic Agent Loader Testing Complete!")
    print("=" * 70)
    print("✨ Key Features Demonstrated:")
    print("   • JSON-based agent configuration")
    print("   • Reflection-based .py file loading")
    print("   • Dynamic agent execution")
    print("   • Capability-based routing")
    print("   • Hot reload functionality")
    print("   • Runtime agent addition/removal")
    print("   • Comprehensive error handling")
    print("   • Execution logging and statistics")

if __name__ == "__main__":
    main()