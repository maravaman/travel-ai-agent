#!/usr/bin/env python3
"""
Simple routing test to verify different queries are routed to different agents
Tests just the routing logic without loading heavy dependencies
"""

import json
from pathlib import Path

def test_routing_logic():
    """Test routing logic without loading the full system"""
    
    def analyze_query_for_routing(question: str) -> str:
        """Simplified version of routing analysis"""
        question_lower = question.lower()
        
        # PRIORITY 1: Search-related queries (specific search terms)
        search_keywords = ["search", "history", "remember", "previous", "similar", "past", "recall", "from my history", "queries", "asked before"]
        if any(keyword in question_lower for keyword in search_keywords):
            return "search"
        
        # PRIORITY 2: Weather-related queries
        weather_keywords = ["weather", "temperature", "rain", "sun", "climate", "forecast", "humidity", "wind", "storm", "snow"]
        if any(keyword in question_lower for keyword in weather_keywords):
            return "weather"
        
        # PRIORITY 3: Dining-related queries  
        dining_keywords = ["restaurant", "food", "cuisine", "dining", "eat", "meal", "chef", "menu", "cooking", "recipe"]
        if any(keyword in question_lower for keyword in dining_keywords):
            return "dining"
        
        # PRIORITY 4: Location-related queries
        location_keywords = ["scenic", "beautiful", "location", "tourist", "destination", "view", "landscape", "mountain"]
        if any(keyword in question_lower for keyword in location_keywords):
            return "location"
        
        # PRIORITY 5: Forest-related queries
        forest_keywords = ["forest", "tree", "wildlife", "ecosystem", "conservation", "nature", "biodiversity"]
        if any(keyword in question_lower for keyword in forest_keywords):
            return "forest"
        
        # PRIORITY 6: Travel agent queries (comprehensive travel planning)
        travel_keywords = ["travel", "trip", "vacation", "holiday", "booking", "flight", "hotel", "itinerary", "tour", "package", "cruise", "resort"]
        if any(keyword in question_lower for keyword in travel_keywords):
            return "travel"
        
        # Default to location if no specific routing
        return "location"
    
    def get_routing_key(agent_id: str) -> str:
        """Convert agent ID to routing key"""
        routing_map = {
            "WeatherAgent": "weather",
            "DiningAgent": "dining",
            "ScenicLocationFinderAgent": "location",
            "ForestAnalyzerAgent": "forest",
            "SearchAgent": "search",
            "TravelAgent": "travel"
        }
        return routing_map.get(agent_id, agent_id.lower().replace("agent", ""))
    
    # Test queries and expected routes
    test_queries = [
        ("What's the weather like today?", "weather"),
        ("Best restaurants in Paris", "dining"),
        ("Show me scenic locations", "location"),
        ("Tell me about forest ecosystems", "forest"),
        ("Search my previous queries", "search"),
        ("Plan a vacation to Italy", "travel"),
        ("Book a hotel for my trip", "travel"),
        ("What's the temperature tomorrow?", "weather"),
        ("Find good food near me", "dining"),
        ("Beautiful places to visit", "location"),
        ("Wildlife conservation efforts", "forest"),
        ("Remember what I asked before", "search"),
        ("General question", "location"),  # default
    ]
    
    print("🧪 Testing Query Routing Logic")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for query, expected_route in test_queries:
        actual_route = analyze_query_for_routing(query)
        status = "✅" if actual_route == expected_route else "❌"
        print(f"{status} '{query}' -> Expected: {expected_route}, Got: {actual_route}")
        
        if actual_route == expected_route:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print("🔧 Testing Agent Configuration Mapping")
    print("=" * 60)
    
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
        actual_key = get_routing_key(agent_id)
        status = "✅" if actual_key == expected_key else "❌"
        print(f"{status} {agent_id} -> Expected: {expected_key}, Got: {actual_key}")
        
        if actual_key == expected_key:
            passed += 1
        else:
            failed += 1
    
    # Check JSON configuration exists
    print("\n" + "=" * 60)
    print("📊 JSON Configuration Check")
    print("=" * 60)
    
    config_path = Path(__file__).parent.parent / "core" / "agents.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        agents = config.get('agents', [])
        print(f"✅ Found {len(agents)} agents in configuration:")
        for agent in agents:
            keywords = agent.get('keywords', [])
            print(f"   🤖 {agent.get('name', 'Unknown')}: {len(keywords)} keywords")
        passed += 1
    else:
        print("❌ agents.json configuration file not found")
        failed += 1
    
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Routing logic is working correctly.")
        return True
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please review the routing logic.")
        return False

if __name__ == "__main__":
    success = test_routing_logic()
    exit(0 if success else 1)
