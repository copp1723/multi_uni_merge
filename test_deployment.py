#!/usr/bin/env python3
"""
Test script to verify the multi_uni_merge deployment
Tests all 4 core features:
1. MCP filesystem access
2. Supermemory integration
3. OpenRouter API responses
4. @mention collaboration chats
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"  # Change this to your deployment URL
TIMEOUT = 30

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f" {text}")
    print("="*60)

def print_result(test_name, success, details=""):
    """Print test result"""
    status = "✅ PASSED" if success else "❌ FAILED"
    print(f"{test_name}: {status}")
    if details:
        print(f"  Details: {details}")

def test_health_check():
    """Test basic health check"""
    print_header("Testing Health Check")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=TIMEOUT)
        data = response.json()
        
        success = response.status_code == 200 and data.get("status") == "success"
        print_result("Health Check", success, f"Services initialized: {data['data'].get('services_initialized', False)}")
        
        if not success:
            print("  Response:", json.dumps(data, indent=2))
        
        return success
    except Exception as e:
        print_result("Health Check", False, str(e))
        return False

def test_frontend():
    """Test if frontend is being served"""
    print_header("Testing Frontend")
    try:
        response = requests.get(BASE_URL, timeout=TIMEOUT)
        
        # Check if it's HTML (frontend) or JSON (API fallback)
        is_html = "text/html" in response.headers.get("Content-Type", "")
        is_react = "root" in response.text or "React" in response.text
        
        success = response.status_code == 200 and (is_html or is_react)
        print_result("Frontend Serving", success, 
                    f"Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
        
        return success
    except Exception as e:
        print_result("Frontend Serving", False, str(e))
        return False

def test_mcp_filesystem():
    """Test MCP filesystem access"""
    print_header("Testing MCP Filesystem")
    
    # Test 1: List files
    try:
        response = requests.get(f"{BASE_URL}/api/test/mcp-filesystem", timeout=TIMEOUT)
        data = response.json()
        
        list_success = response.status_code == 200 and data.get("status") == "success"
        print_result("MCP List Files", list_success, 
                    f"Workspace: {data['data'].get('workspace_path', 'Unknown')}")
    except Exception as e:
        print_result("MCP List Files", False, str(e))
        list_success = False
    
    # Test 2: Write file
    try:
        test_data = {
            "filename": f"test_{int(time.time())}.txt",
            "content": f"Test file created at {datetime.now().isoformat()}"
        }
        response = requests.post(f"{BASE_URL}/api/test/mcp-filesystem", 
                               json=test_data, timeout=TIMEOUT)
        data = response.json()
        
        write_success = response.status_code == 200 and data.get("status") == "success"
        print_result("MCP Write File", write_success, 
                    f"File: {data['data'].get('filepath', 'Unknown')}")
    except Exception as e:
        print_result("MCP Write File", False, str(e))
        write_success = False
    
    return list_success and write_success

def test_supermemory():
    """Test Supermemory integration"""
    print_header("Testing Supermemory")
    
    # Test 1: Store memory
    try:
        store_data = {
            "action": "store",
            "content": f"Test memory entry created at {datetime.now().isoformat()}",
            "metadata": {"type": "test", "source": "deployment_test"}
        }
        response = requests.post(f"{BASE_URL}/api/test/supermemory", 
                               json=store_data, timeout=TIMEOUT)
        data = response.json()
        
        store_success = response.status_code == 200 and data.get("status") == "success"
        print_result("Supermemory Store", store_success)
    except Exception as e:
        print_result("Supermemory Store", False, str(e))
        store_success = False
    
    # Test 2: Search memories
    try:
        search_data = {
            "action": "search",
            "query": "test",
            "limit": 5
        }
        response = requests.post(f"{BASE_URL}/api/test/supermemory", 
                               json=search_data, timeout=TIMEOUT)
        data = response.json()
        
        search_success = response.status_code == 200 and data.get("status") == "success"
        print_result("Supermemory Search", search_success, 
                    f"Results found: {data['data'].get('count', 0)}")
    except Exception as e:
        print_result("Supermemory Search", False, str(e))
        search_success = False
    
    return store_success or search_success  # At least one should work

def test_openrouter():
    """Test OpenRouter API"""
    print_header("Testing OpenRouter")
    
    try:
        test_data = {
            "prompt": "Say 'Hello from OpenRouter!' to confirm the API is working.",
            "model": "openai/gpt-3.5-turbo"
        }
        response = requests.post(f"{BASE_URL}/api/test/openrouter", 
                               json=test_data, timeout=TIMEOUT)
        data = response.json()
        
        success = response.status_code == 200 and data.get("status") == "success"
        print_result("OpenRouter API", success, 
                    f"Response: {data['data'].get('response', 'No response')[:100]}...")
        
        return success
    except Exception as e:
        print_result("OpenRouter API", False, str(e))
        return False

def test_collaboration():
    """Test @mention collaboration"""
    print_header("Testing @mention Collaboration")
    
    try:
        test_data = {
            "message": "@research Please analyze this test. @coding Can you help implement?",
            "agents": ["research", "coding", "debug"]
        }
        response = requests.post(f"{BASE_URL}/api/test/collaboration", 
                               json=test_data, timeout=TIMEOUT)
        data = response.json()
        
        success = response.status_code == 200 and data.get("status") == "success"
        mentioned = data['data'].get('mentioned_agents', [])
        print_result("Collaboration System", success, 
                    f"Mentioned agents: {', '.join(mentioned) if mentioned else 'None'}")
        
        if success:
            print(f"  Available agents: {len(data['data'].get('available_agents', []))}")
            print(f"  Collaboration ready: {data['data'].get('collaboration_ready', False)}")
        
        return success
    except Exception as e:
        print_result("Collaboration System", False, str(e))
        return False

def test_all_systems():
    """Test all systems endpoint"""
    print_header("Testing All Systems Summary")
    
    try:
        response = requests.get(f"{BASE_URL}/api/test/all", timeout=TIMEOUT)
        data = response.json()
        
        if response.status_code == 200 and data.get("status") == "success":
            tests = data['data'].get('tests', {})
            overall = data['data'].get('overall_status', 'unknown')
            
            print(f"\nOverall Status: {'✅ PASSED' if overall == 'passed' else '❌ FAILED'}")
            print("\nIndividual Test Results:")
            for test_name, result in tests.items():
                status = result.get('status', 'unknown')
                emoji = "✅" if status == "passed" else "❌"
                print(f"  {emoji} {test_name}: {status}")
                if status == "error":
                    print(f"     Error: {result.get('error', 'Unknown error')}")
            
            return overall == "passed"
        else:
            print("Failed to get system status")
            return False
            
    except Exception as e:
        print(f"Error testing all systems: {e}")
        return False

def main():
    """Run all tests"""
    print(f"\n🚀 Multi-Uni-Merge Deployment Test Suite")
    print(f"Testing deployment at: {BASE_URL}")
    print(f"Started at: {datetime.now().isoformat()}")
    
    # Check if server is reachable
    print("\n⏳ Checking if server is reachable...")
    try:
        requests.get(BASE_URL, timeout=5)
    except:
        print("❌ ERROR: Server is not reachable!")
        print(f"   Make sure the application is running at {BASE_URL}")
        print("   You can change the BASE_URL in this script if needed.")
        return 1
    
    # Run tests
    results = {
        "health": test_health_check(),
        "frontend": test_frontend(),
        "mcp_filesystem": test_mcp_filesystem(),
        "supermemory": test_supermemory(),
        "openrouter": test_openrouter(),
        "collaboration": test_collaboration(),
        "all_systems": test_all_systems()
    }
    
    # Summary
    print_header("Test Summary")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    print("\nDetailed Results:")
    for test, result in results.items():
        emoji = "✅" if result else "❌"
        print(f"  {emoji} {test}")
    
    print(f"\n{'🎉 All tests passed!' if passed == total else '⚠️  Some tests failed.'}")
    print(f"Completed at: {datetime.now().isoformat()}")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())