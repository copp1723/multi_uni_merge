#!/usr/bin/env python3
"""Test script for the transform functionality"""

import requests
import json

# API configuration
API_BASE_URL = "http://localhost:5000"

def test_transform():
    """Test the transform endpoint"""
    
    # First, get available agents
    print("1. Getting available agents...")
    agents_response = requests.get(f"{API_BASE_URL}/api/agents")
    
    if agents_response.status_code != 200:
        print(f"Failed to get agents: {agents_response.status_code}")
        print(agents_response.text)
        return
    
    agents_data = agents_response.json()
    agents = agents_data.get("data", [])
    
    if not agents:
        print("No agents available")
        return
    
    print(f"Found {len(agents)} agents:")
    for agent in agents:
        print(f"  - {agent['name']} (ID: {agent['id']})")
    
    # Test transform with first agent
    test_agent = agents[0]
    test_text = "This is a test message that needs to be transformed into something more professional."
    
    print(f"\n2. Testing transform with agent '{test_agent['name']}'...")
    print(f"Original text: {test_text}")
    
    transform_payload = {
        "text": test_text,
        "agent_id": test_agent["id"]
    }
    
    transform_response = requests.post(
        f"{API_BASE_URL}/api/transform",
        json=transform_payload,
        headers={"Content-Type": "application/json"}
    )
    
    if transform_response.status_code == 200:
        result = transform_response.json()
        if result.get("data"):
            print(f"\nTransform successful!")
            print(f"Transformed text: {result['data']['transformed_text']}")
            print(f"Agent used: {result['data']['agent_name']}")
            print(f"Model used: {result['data']['model_used']}")
        else:
            print(f"Transform returned no data: {result}")
    else:
        print(f"Transform failed: {transform_response.status_code}")
        print(transform_response.text)

if __name__ == "__main__":
    print("Testing Transform Functionality")
    print("=" * 50)
    test_transform()