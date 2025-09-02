#!/usr/bin/env python3
"""
Simple routing test to verify different queries are routed to different agents
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.langgraph_multiagent_system import langgraph_multiagent_system

def test_routing():
    """Test routing for different types of queries"""
    
    test_queries = [
        ("What's the weather like today?", "weather"),
        ("Best restaurants in Paris", "dining"),
        ("Show me scenic locations", "location"),
        ("Tell me about forest ecosystems", "forest"),
        ("Search my previous queries", "search"),
        ("Plan a vacation to Italy", "travel"),
        ("General question", "location"),  # default
    ]
    
    print("🧪 Testing Query Routing Logic")
    print("=" * 50)
    
    for query, expected_route in test_queries:
        actual_route = langgraph_multiagent_system._analyze_query_for_routing(query)
        status = "✅" if actual_route == expected_route else "❌"
        print(f"{status} '{query}' -> Expected: {expected_route}, Got: {actual_route}")
    
    print("\n" + "=" * 50)
    print("🔧 Testing Agent Configuration Mapping")
    print("=" * 50)
    
    # Test agent ID to routing key mapping
    agent_mappings = [
        ("WeatherAgent", "weather"),
        ("DiningAgent", "dining"), 
        ("ScenicLocationFinderAgent", "location"),
        ("ForestAnalyzerAgent", "forest"),
        ("SearchAgent", "search"),
        ("TravelAgent", "travel")
    ]
    
    for agent_id, expected_key in agent_mappings:
        actual_key = langgraph_multiagent_system._get_routing_key(agent_id)
        status = "✅" if actual_key == expected_key else "❌"
        print(f"{status} {agent_id} -> Expected: {expected_key}, Got: {actual_key}")
    
    print("\n" + "=" * 50)
    print("📊 Agent Configuration Summary")
    print("=" * 50)
    
    agents_config = langgraph_multiagent_system.agents_config
    for agent_id, config in agents_config.items():
        keywords = config.get('keywords', [])
        print(f"🤖 {agent_id}: {len(keywords)} keywords - {keywords[:5]}{'...' if len(keywords) > 5 else ''}")

if __name__ == "__main__":
    test_routing()
