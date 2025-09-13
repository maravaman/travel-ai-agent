#!/usr/bin/env python3
"""
Interactive Demo for Dynamic Agent Loading System
Demonstrates JSON-based agent configuration and reflection-based execution
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.dynamic_agent_loader import DynamicAgentLoader
from core.memory import MemoryManager

def show_welcome():
    """Show welcome message"""
    print("🎯 DYNAMIC AGENT LOADER - INTERACTIVE DEMO")
    print("=" * 60)
    print("This demo shows how to dynamically load and execute .py agent files")
    print("using JSON configuration and Python reflection.")
    print()
    print("Features demonstrated:")
    print("   • JSON-based agent configuration")
    print("   • Reflection-based .py file loading")
    print("   • Dynamic agent execution")
    print("   • Keyword-based agent routing")
    print("   • Capability-based execution")
    print("   • Hot reload functionality")
    print("=" * 60)
    print()

def show_menu():
    """Show interactive menu"""
    print("\n📋 AVAILABLE COMMANDS:")
    print("-" * 30)
    print("1. 📝 Execute query (keyword-based routing)")
    print("2. 🎯 Execute specific agent")
    print("3. 🔧 Execute by capability")
    print("4. 📊 Show agent statistics")
    print("5. 🔍 Show agent information")
    print("6. 🔄 Reload agents")
    print("7. ➕ Add agent dynamically")
    print("8. 🗑️ Remove agent")
    print("9. ✅ Validate configuration")
    print("10. 📜 Show execution log")
    print("11. 🆘 Show help")
    print("12. 🚪 Exit")
    print("-" * 30)

def execute_query_demo(loader: DynamicAgentLoader):
    """Demo query execution with keyword routing"""
    print("\n📝 QUERY EXECUTION DEMO")
    print("-" * 30)
    
    query = input("Enter your travel query: ").strip()
    if not query:
        print("❌ No query entered")
        return
    
    user_id = int(input("Enter user ID (or press Enter for random): ").strip() or str(datetime.now().timestamp())[:10])
    max_agents = int(input("Max agents to execute (default 3): ").strip() or "3")
    
    print(f"\n🔄 Processing query with keyword-based routing...")
    print(f"Query: {query}")
    print(f"User ID: {user_id}")
    print(f"Max agents: {max_agents}")
    
    result = loader.execute_by_keywords(query, user_id, max_agents)
    
    print(f"\n📊 Execution Results:")
    print(f"   Agents executed: {result['agents_executed']}")
    print(f"   Successful: {result['successful_executions']}")
    print(f"   Total time: {result['total_processing_time']:.2f}s")
    
    print(f"\n📝 Individual Agent Responses:")
    for agent_result in result["individual_results"]:
        if agent_result["success"]:
            response_preview = agent_result["response"][:150] + "..." if len(agent_result["response"]) > 150 else agent_result["response"]
            print(f"   🤖 {agent_result['agent']} ({agent_result['processing_time']:.2f}s):")
            print(f"      {response_preview}")
        else:
            print(f"   ❌ {agent_result['agent']}: {agent_result.get('error', 'Unknown error')}")

def execute_specific_agent_demo(loader: DynamicAgentLoader):
    """Demo executing specific agent"""
    print("\n🎯 SPECIFIC AGENT EXECUTION DEMO")
    print("-" * 35)
    
    agents = loader.get_agent_names()
    print(f"Available agents: {', '.join(agents)}")
    
    agent_name = input("Enter agent name: ").strip()
    if agent_name not in agents:
        print(f"❌ Agent {agent_name} not found")
        return
    
    query = input("Enter query: ").strip()
    if not query:
        print("❌ No query entered")
        return
    
    user_id = int(input("Enter user ID (or press Enter for random): ").strip() or str(datetime.now().timestamp())[:10])
    
    print(f"\n🔄 Executing {agent_name}...")
    
    result = loader.execute_agent(agent_name, query, user_id)
    
    if result["success"]:
        print(f"✅ Execution successful!")
        print(f"   Processing time: {result['processing_time']:.2f}s")
        print(f"   Response length: {len(result['response'])} characters")
        print(f"   Response preview: {result['response'][:200]}...")
    else:
        print(f"❌ Execution failed: {result.get('error', 'Unknown error')}")

def execute_by_capability_demo(loader: DynamicAgentLoader):
    """Demo executing by capability"""
    print("\n🔧 CAPABILITY-BASED EXECUTION DEMO")
    print("-" * 35)
    
    # Get all unique capabilities
    all_capabilities = set()
    for agent_name in loader.get_agent_names():
        agent_info = loader.get_agent_info(agent_name)
        all_capabilities.update(agent_info["capabilities"])
    
    print(f"Available capabilities: {', '.join(sorted(all_capabilities))}")
    
    capability = input("Enter capability: ").strip()
    if capability not in all_capabilities:
        print(f"❌ Capability {capability} not found")
        return
    
    query = input("Enter query: ").strip()
    if not query:
        print("❌ No query entered")
        return
    
    user_id = int(input("Enter user ID (or press Enter for random): ").strip() or str(datetime.now().timestamp())[:10])
    
    print(f"\n🔄 Executing agents with capability '{capability}'...")
    
    result = loader.execute_by_capability(capability, query, user_id)
    
    if result.get("successful_executions", 0) > 0:
        print(f"✅ Executed {result['successful_executions']} agents successfully!")
        print(f"   Total time: {result['total_processing_time']:.2f}s")
        
        for agent_result in result["individual_results"]:
            if agent_result["success"]:
                print(f"   🤖 {agent_result['agent']}: {agent_result['response'][:100]}...")
    else:
        print(f"❌ No successful executions")

def show_agent_statistics(loader: DynamicAgentLoader):
    """Show agent statistics"""
    print("\n📊 AGENT STATISTICS")
    print("-" * 25)
    
    stats = loader.get_agent_statistics()
    
    print(f"Total Agents Loaded: {stats['total_agents_loaded']}")
    print(f"Total Executions: {stats['total_executions']}")
    print(f"Successful Executions: {stats['successful_executions']}")
    print(f"Success Rate: {stats['success_rate']:.2%}")
    
    if stats["agent_execution_counts"]:
        print(f"\nAgent Execution Counts:")
        for agent, count in stats["agent_execution_counts"].items():
            print(f"   • {agent}: {count} executions")

def show_agent_info(loader: DynamicAgentLoader):
    """Show detailed agent information"""
    print("\n🔍 AGENT INFORMATION")
    print("-" * 25)
    
    agents = loader.get_agent_names()
    print(f"Available agents: {', '.join(agents)}")
    
    agent_name = input("Enter agent name for details: ").strip()
    if agent_name not in agents:
        print(f"❌ Agent {agent_name} not found")
        return
    
    info = loader.get_agent_info(agent_name)
    
    print(f"\n📋 {agent_name} Details:")
    print(f"   Class: {info['class_name']}")
    print(f"   Description: {info['description']}")
    print(f"   File: {info['file_path']}")
    print(f"   Enabled: {info['enabled']}")
    print(f"   Priority: {info['priority']}")
    print(f"   Execution Count: {info['execution_count']}")
    print(f"   Success Rate: {info['success_rate']:.2%}")
    print(f"   Avg Processing Time: {info['avg_processing_time']:.2f}s")
    print(f"   Capabilities: {', '.join(info['capabilities'])}")
    print(f"   Keywords: {', '.join(info['keywords'])}")

def reload_agents_demo(loader: DynamicAgentLoader):
    """Demo agent reloading"""
    print("\n🔄 AGENT RELOAD DEMO")
    print("-" * 25)
    
    choice = input("Reload (1) specific agent or (2) all agents? Enter 1 or 2: ").strip()
    
    if choice == "1":
        agents = loader.get_agent_names()
        print(f"Available agents: {', '.join(agents)}")
        
        agent_name = input("Enter agent name to reload: ").strip()
        if agent_name not in agents:
            print(f"❌ Agent {agent_name} not found")
            return
        
        print(f"🔄 Reloading {agent_name}...")
        success = loader.reload_agent(agent_name)
        print(f"{'✅' if success else '❌'} Reload result: {success}")
        
    elif choice == "2":
        print(f"🔄 Reloading all agents...")
        results = loader.reload_all_agents()
        
        successful_reloads = sum(1 for success in results.values() if success)
        print(f"📊 Reloaded {successful_reloads}/{len(results)} agents successfully")
        
        for agent_name, success in results.items():
            print(f"   {'✅' if success else '❌'} {agent_name}")
    else:
        print("❌ Invalid choice")

def add_agent_demo(loader: DynamicAgentLoader):
    """Demo adding agent dynamically"""
    print("\n➕ ADD AGENT DYNAMICALLY DEMO")
    print("-" * 35)
    
    print("Enter new agent configuration:")
    name = input("Agent name: ").strip()
    file_path = input("File path (e.g., agents/my_agent.py): ").strip()
    class_name = input("Class name: ").strip()
    description = input("Description: ").strip()
    
    capabilities = input("Capabilities (comma-separated): ").strip().split(",")
    capabilities = [cap.strip() for cap in capabilities if cap.strip()]
    
    keywords = input("Keywords (comma-separated): ").strip().split(",")
    keywords = [kw.strip() for kw in keywords if kw.strip()]
    
    new_agent_config = {
        "name": name,
        "file_path": file_path,
        "class_name": class_name,
        "enabled": True,
        "priority": 2,
        "entry_point": "main",
        "description": description,
        "capabilities": capabilities,
        "keywords": keywords,
        "execution_settings": {
            "timeout_seconds": 30,
            "temperature": 0.7,
            "max_tokens": 1500
        }
    }
    
    print(f"\n🔄 Adding agent {name}...")
    success = loader.add_agent_dynamically(new_agent_config)
    print(f"{'✅' if success else '❌'} Addition result: {success}")
    
    if success:
        print(f"📊 Total agents after addition: {len(loader.get_all_agents())}")

def remove_agent_demo(loader: DynamicAgentLoader):
    """Demo removing agent"""
    print("\n🗑️ REMOVE AGENT DEMO")
    print("-" * 25)
    
    agents = loader.get_agent_names()
    print(f"Available agents: {', '.join(agents)}")
    
    agent_name = input("Enter agent name to remove: ").strip()
    if agent_name not in agents:
        print(f"❌ Agent {agent_name} not found")
        return
    
    confirm = input(f"Are you sure you want to remove {agent_name}? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Removal cancelled")
        return
    
    print(f"🗑️ Removing {agent_name}...")
    success = loader.remove_agent(agent_name)
    print(f"{'✅' if success else '❌'} Removal result: {success}")
    
    if success:
        print(f"📊 Total agents after removal: {len(loader.get_all_agents())}")

def validate_configuration_demo(loader: DynamicAgentLoader):
    """Demo configuration validation"""
    print("\n✅ CONFIGURATION VALIDATION DEMO")
    print("-" * 35)
    
    validation = loader.validate_configuration()
    
    print(f"Overall Valid: {'✅' if validation['valid'] else '❌'}")
    
    if validation["errors"]:
        print(f"\n❌ Errors ({len(validation['errors'])}):")
        for error in validation["errors"]:
            print(f"   • {error}")
    
    if validation["warnings"]:
        print(f"\n⚠️ Warnings ({len(validation['warnings'])}):")
        for warning in validation["warnings"]:
            print(f"   • {warning}")
    
    print(f"\n📊 Agent Validations:")
    for agent_name, agent_val in validation["agent_validations"].items():
        status_items = []
        for check, passed in agent_val.items():
            status_items.append(f"{check}: {'✅' if passed else '❌'}")
        print(f"   • {agent_name}:")
        for status in status_items:
            print(f"     - {status}")

def show_execution_log(loader: DynamicAgentLoader):
    """Show execution log"""
    print("\n📜 EXECUTION LOG")
    print("-" * 20)
    
    log = loader.get_execution_log()
    
    if not log:
        print("No executions recorded yet")
        return
    
    print(f"Total executions: {len(log)}")
    print(f"\nRecent executions (last 10):")
    
    for entry in log[-10:]:
        status = "✅" if entry["success"] else "❌"
        print(f"   {status} {entry['agent']} ({entry['processing_time']:.2f}s)")
        print(f"      Query: {entry['query'][:50]}...")
        print(f"      Time: {entry['timestamp']}")

def show_help():
    """Show help information"""
    print("\n🆘 HELP - DYNAMIC AGENT LOADER")
    print("=" * 40)
    print("This system allows you to:")
    print()
    print("📝 Execute Queries:")
    print("   • Enter natural language queries")
    print("   • System automatically selects best agents based on keywords")
    print("   • Multiple agents can be triggered for complex queries")
    print()
    print("🎯 Execute Specific Agents:")
    print("   • Choose exact agent to execute")
    print("   • Useful for testing specific agent functionality")
    print()
    print("🔧 Execute by Capability:")
    print("   • Find agents with specific capabilities")
    print("   • Execute all agents that can handle the capability")
    print()
    print("🔄 Hot Reload:")
    print("   • Reload agents without restarting the system")
    print("   • Useful during development and testing")
    print()
    print("➕ Dynamic Management:")
    print("   • Add new agents at runtime")
    print("   • Remove agents dynamically")
    print("   • Update configuration on the fly")
    print()
    print("Example Queries to Try:")
    print("   • 'I'm planning a trip to Japan and feeling stressed'")
    print("   • 'How should I communicate with my travel guide?'")
    print("   • 'I need help organizing my vacation planning'")
    print("   • 'I'm overwhelmed with too many destination choices'")

def interactive_demo():
    """Main interactive demo"""
    show_welcome()
    
    try:
        # Initialize system
        print("🔧 Initializing Dynamic Agent Loader...")
        memory_manager = MemoryManager()
        loader = DynamicAgentLoader(memory_manager=memory_manager)
        
        print(f"✅ Loaded {len(loader.get_all_agents())} agents from JSON configuration")
        
        while True:
            show_menu()
            
            try:
                choice = input("\nEnter your choice (1-12): ").strip()
                
                if choice == "1":
                    execute_query_demo(loader)
                elif choice == "2":
                    execute_specific_agent_demo(loader)
                elif choice == "3":
                    execute_by_capability_demo(loader)
                elif choice == "4":
                    show_agent_statistics(loader)
                elif choice == "5":
                    show_agent_info(loader)
                elif choice == "6":
                    reload_agents_demo(loader)
                elif choice == "7":
                    add_agent_demo(loader)
                elif choice == "8":
                    remove_agent_demo(loader)
                elif choice == "9":
                    validate_configuration_demo(loader)
                elif choice == "10":
                    show_execution_log(loader)
                elif choice == "11":
                    show_help()
                elif choice == "12" or choice.lower() in ['quit', 'exit', 'q']:
                    break
                else:
                    print("❌ Invalid choice. Please enter 1-12.")
                
            except KeyboardInterrupt:
                print("\n\n👋 Demo interrupted by user")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Please try again.")
    
    except Exception as e:
        print(f"❌ Failed to initialize system: {e}")
        return
    
    print("\n👋 Thank you for trying the Dynamic Agent Loader!")
    print("🌐 Web interface available at: http://localhost:8000/dynamic")

if __name__ == "__main__":
    interactive_demo()