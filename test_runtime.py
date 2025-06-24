#!/usr/bin/env python3
"""
🧪 Runtime Test Script for Swarm Multi-Agent System
Tests the application runtime to catch issues before deployment
"""

import sys
import os
import traceback
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all critical imports"""
    print("🔍 Testing imports...")
    
    try:
        # Test basic imports
        import flask
        import psycopg2
        import requests
        import pydantic
        import gunicorn
        print("✅ Basic packages imported successfully")
        
        # Test backend imports
        from backend.main import create_app, SwarmApplication
        print("✅ Backend main module imported successfully")
        
        from backend.utils.error_handler import SwarmError, create_error_response
        from backend.utils.service_utils import service_registry
        from backend.utils.async_utils import task_manager
        print("✅ Backend utilities imported successfully")
        
        # Test service imports
        from backend.services.postgresql_service import initialize_postgresql
        from backend.services.openrouter_service import initialize_openrouter
        from backend.services.supermemory_service import initialize_supermemory
        from backend.services.mcp_filesystem import initialize_mcp_filesystem
        from backend.services.mailgun_service import initialize_mailgun
        from backend.services.websocket_service import initialize_websocket_service
        print("✅ All services imported successfully")
        
        # Test orchestrator import
        from backend.swarm_orchestrator import SwarmOrchestrator
        print("✅ Swarm orchestrator imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        traceback.print_exc()
        return False

def test_app_creation():
    """Test Flask app creation without services"""
    print("\n🏗️ Testing Flask app creation...")
    
    try:
        # Import the main module
        from backend.main import SwarmApplication
        
        # Create application instance
        swarm_app = SwarmApplication()
        print("✅ SwarmApplication instance created")
        
        # Create Flask app (without services)
        app = swarm_app.create_app()
        print("✅ Flask app created successfully")
        
        # Test basic app properties
        print(f"   App name: {app.name}")
        print(f"   Debug mode: {app.debug}")
        print(f"   Secret key configured: {'SECRET_KEY' in app.config}")
        
        # Test that routes are registered
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        expected_routes = ['/', '/api/health', '/api/system/status', '/api/agents']
        
        for route in expected_routes:
            if route in routes:
                print(f"✅ Route {route} registered")
            else:
                print(f"⚠️ Route {route} not found")
        
        return True
        
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        traceback.print_exc()
        return False

def test_configuration():
    """Test configuration loading"""
    print("\n⚙️ Testing configuration...")
    
    try:
        from backend.main import SwarmApplication
        
        swarm_app = SwarmApplication()
        config = swarm_app.config
        
        print("✅ Configuration loaded")
        
        # Check required configurations
        required_configs = ['HOST', 'PORT', 'SECRET_KEY']
        for key in required_configs:
            if key in config and config[key]:
                if key == 'SECRET_KEY':
                    print(f"✅ {key}: [SET]")
                else:
                    print(f"✅ {key}: {config[key]}")
            else:
                print(f"⚠️ {key}: not set or empty")
        
        # Check optional configurations
        optional_configs = [
            'DATABASE_URL', 'OPENROUTER_API_KEY', 
            'SUPERMEMORY_API_KEY', 'SUPERMEMORY_BASE_URL'
        ]
        for key in optional_configs:
            if key in config and config[key]:
                print(f"✅ {key}: [SET]")
            else:
                print(f"⚠️ {key}: not set (optional)")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        traceback.print_exc()
        return False

def test_health_endpoint():
    """Test health endpoint without full initialization"""
    print("\n🏥 Testing health endpoint...")
    
    try:
        from backend.main import SwarmApplication
        
        swarm_app = SwarmApplication()
        app = swarm_app.create_app()
        
        with app.test_client() as client:
            # Test health endpoint
            response = client.get('/api/health')
            print(f"✅ Health endpoint status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.get_json()
                print(f"   Response format: {'data' in data}")
                print(f"   System health included: {'system' in data.get('data', {})}")
            
            # Test root endpoint
            response = client.get('/')
            print(f"✅ Root endpoint status: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Health endpoint test failed: {e}")
        traceback.print_exc()
        return False

def test_environment():
    """Test environment setup"""
    print("\n🌍 Testing environment...")
    
    # Check Python version
    python_version = sys.version_info
    print(f"✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major == 3 and python_version.minor >= 10:
        print("✅ Python version compatible")
    else:
        print("⚠️ Python version might be too old")
    
    # Check working directory
    cwd = os.getcwd()
    print(f"✅ Working directory: {cwd}")
    
    # Check critical files
    critical_files = [
        'app.py', 'requirements.txt', 'backend/main.py',
        'backend/__init__.py', 'backend/services/__init__.py',
        'backend/utils/__init__.py'
    ]
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
    
    return True

def main():
    """Main test runner"""
    print("🧪 RUNTIME TESTING FOR SWARM MULTI-AGENT SYSTEM")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Python executable: {sys.executable}")
    print(f"Python path: {sys.path[:3]}...")  # Show first 3 entries
    print("=" * 60)
    
    tests = [
        ("Environment", test_environment),
        ("Imports", test_imports),
        ("Configuration", test_configuration),
        ("App Creation", test_app_creation),
        ("Health Endpoint", test_health_endpoint),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name.upper()} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("🎯 TEST SUMMARY")
    print("="*60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Application should start successfully.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
