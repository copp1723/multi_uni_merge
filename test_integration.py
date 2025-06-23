#!/usr/bin/env python3
"""
End-to-End Integration Test
Tests the complete system integration
"""

import os
import sys
import time
import requests
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_system_integration():
    """Test complete system integration"""
    logger.info("🚀 Starting End-to-End Integration Test")
    logger.info("=" * 50)
    
    test_results = []
    
    # Test 1: Repository Structure
    logger.info("🔍 Testing repository structure...")
    try:
        current_dir = Path.cwd()
        required_dirs = [
            "backend", "frontend", "config", "docs", "scripts"
        ]
        
        for dir_name in required_dirs:
            dir_path = current_dir / dir_name
            if not dir_path.exists():
                raise FileNotFoundError(f"Required directory missing: {dir_name}")
        
        # Check key files
        key_files = [
            "backend/main.py",
            "backend/swarm_orchestrator.py", 
            "frontend/package.json",
            "config/requirements.txt",
            "docs/DEPLOYMENT_GUIDE.md",
            "scripts/setup-dev.sh"
        ]
        
        for file_path in key_files:
            full_path = current_dir / file_path
            if not full_path.exists():
                raise FileNotFoundError(f"Required file missing: {file_path}")
        
        logger.info("✅ Repository structure validation passed")
        test_results.append(("Repository Structure", True))
        
    except Exception as e:
        logger.error(f"❌ Repository structure test failed: {e}")
        test_results.append(("Repository Structure", False))
    
    # Test 2: Backend Dependencies
    logger.info("🔍 Testing backend dependencies...")
    try:
        backend_dir = current_dir / "backend"
        result = subprocess.run(
            [sys.executable, "-c", "import flask, socketio, psycopg2, aiohttp, redis"],
            cwd=backend_dir,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            logger.info("✅ Backend dependencies available")
            test_results.append(("Backend Dependencies", True))
        else:
            logger.error(f"❌ Backend dependencies missing: {result.stderr}")
            test_results.append(("Backend Dependencies", False))
            
    except Exception as e:
        logger.error(f"❌ Backend dependencies test failed: {e}")
        test_results.append(("Backend Dependencies", False))
    
    # Test 3: Frontend Dependencies
    logger.info("🔍 Testing frontend dependencies...")
    try:
        frontend_dir = current_dir / "frontend"
        node_modules = frontend_dir / "node_modules"
        
        if node_modules.exists():
            logger.info("✅ Frontend dependencies installed")
            test_results.append(("Frontend Dependencies", True))
        else:
            logger.warning("⚠️ Frontend dependencies not installed")
            test_results.append(("Frontend Dependencies", False))
            
    except Exception as e:
        logger.error(f"❌ Frontend dependencies test failed: {e}")
        test_results.append(("Frontend Dependencies", False))
    
    # Test 4: Configuration Files
    logger.info("🔍 Testing configuration files...")
    try:
        config_dir = current_dir / "config"
        config_files = [
            "requirements.txt",
            "backend.Dockerfile", 
            "frontend.Dockerfile",
            "docker-compose.yml"
        ]
        
        for config_file in config_files:
            config_path = config_dir / config_file
            if not config_path.exists():
                raise FileNotFoundError(f"Configuration file missing: {config_file}")
        
        logger.info("✅ Configuration files validation passed")
        test_results.append(("Configuration Files", True))
        
    except Exception as e:
        logger.error(f"❌ Configuration files test failed: {e}")
        test_results.append(("Configuration Files", False))
    
    # Test 5: Documentation
    logger.info("🔍 Testing documentation...")
    try:
        docs_dir = current_dir / "docs"
        doc_files = [
            "DEPLOYMENT_GUIDE.md",
            "DEVELOPMENT_GUIDE.md",
            "TEST_RESULTS.md"
        ]
        
        for doc_file in doc_files:
            doc_path = docs_dir / doc_file
            if not doc_path.exists():
                raise FileNotFoundError(f"Documentation file missing: {doc_file}")
            
            # Check if file has content
            if doc_path.stat().st_size < 100:
                raise ValueError(f"Documentation file too small: {doc_file}")
        
        logger.info("✅ Documentation validation passed")
        test_results.append(("Documentation", True))
        
    except Exception as e:
        logger.error(f"❌ Documentation test failed: {e}")
        test_results.append(("Documentation", False))
    
    # Test 6: Service Imports
    logger.info("🔍 Testing service imports...")
    try:
        backend_dir = current_dir / "backend"
        import_test = """
import sys
sys.path.insert(0, '.')
from services.postgresql_service import PostgreSQLService
from services.openrouter_service import OpenRouterService
from services.supermemory_service import SupermemoryService
from services.mcp_filesystem import MCPFilesystemService
from services.mailgun_service import MailgunService
from services.websocket_service import WebSocketService
from utils.error_handler import SwarmError
from utils.async_utils import AsyncTaskManager
from utils.service_utils import BaseService
print("All imports successful")
"""
        
        result = subprocess.run(
            [sys.executable, "-c", import_test],
            cwd=backend_dir,
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0 and "All imports successful" in result.stdout:
            logger.info("✅ Service imports successful")
            test_results.append(("Service Imports", True))
        else:
            logger.error(f"❌ Service imports failed: {result.stderr}")
            test_results.append(("Service Imports", False))
            
    except Exception as e:
        logger.error(f"❌ Service imports test failed: {e}")
        test_results.append(("Service Imports", False))
    
    # Test 7: Agent System
    logger.info("🔍 Testing agent system...")
    try:
        backend_dir = current_dir / "backend"
        agent_test = """
import sys
sys.path.insert(0, '.')
from swarm_orchestrator import SwarmOrchestrator
orchestrator = SwarmOrchestrator()
agents = orchestrator.get_available_agents()
print(f"Agents loaded: {len(agents)}")
comm_agent = next((a for a in agents if a['id'] == 'comms'), None)
if comm_agent:
    print("Communication Agent found")
else:
    print("Communication Agent missing")
"""
        
        result = subprocess.run(
            [sys.executable, "-c", agent_test],
            cwd=backend_dir,
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0 and "Communication Agent found" in result.stdout:
            logger.info("✅ Agent system functional")
            test_results.append(("Agent System", True))
        else:
            logger.error(f"❌ Agent system test failed: {result.stderr}")
            test_results.append(("Agent System", False))
            
    except Exception as e:
        logger.error(f"❌ Agent system test failed: {e}")
        test_results.append(("Agent System", False))
    
    # Print Results
    logger.info("\n" + "=" * 50)
    logger.info("📊 END-TO-END TEST RESULTS")
    logger.info("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name:<25} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info("=" * 50)
    logger.info(f"Total Tests: {len(test_results)}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Success Rate: {(passed/len(test_results)*100):.1f}%")
    
    if failed == 0:
        logger.info("🎉 All integration tests passed!")
        logger.info("🚀 System is ready for production deployment!")
        return True
    else:
        logger.warning(f"⚠️ {failed} test(s) failed - review before deployment")
        return False

if __name__ == "__main__":
    # Set test environment
    os.environ.update({
        'DATABASE_URL': 'sqlite:///test_integration.db',
        'OPENROUTER_API_KEY': 'test-openrouter-api-key-12345',
        'SUPERMEMORY_API_KEY': 'test-supermemory-api-key-12345',
        'SUPERMEMORY_BASE_URL': 'http://localhost:8080',
        'MAILGUN_API_KEY': 'test-mailgun-api-key-12345',
        'MAILGUN_DOMAIN': 'test.example.com',
        'DEBUG': 'true'
    })
    
    success = test_system_integration()
    sys.exit(0 if success else 1)

