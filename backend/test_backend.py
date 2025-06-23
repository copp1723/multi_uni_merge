#!/usr/bin/env python3
"""
Backend Service Testing Script
Tests all backend services and components
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_imports():
    """Test that all modules can be imported"""
    logger.info("🔍 Testing module imports...")

    try:
        # Test utility imports
        from utils.error_handler import SwarmError, ErrorCode, handle_errors  # noqa: F401
        from utils.async_utils import AsyncTaskManager, async_retry  # noqa: F401
        from utils.service_utils import BaseService, ServiceRegistry, service_registry  # noqa: F401

        logger.info("✅ Utility modules imported successfully")

        # Test service imports
        from services.postgresql_service import PostgreSQLService  # noqa: F401
        from services.openrouter_service import OpenRouterService  # noqa: F401
        from services.supermemory_service import SupermemoryService  # noqa: F401
        from services.mcp_filesystem import MCPFilesystemService  # noqa: F401
        from services.mailgun_service import MailgunService  # noqa: F401
        from services.websocket_service import WebSocketService  # noqa: F401

        logger.info("✅ Service modules imported successfully")

        # Test main application
        from main import SwarmApplication  # noqa: F401
        from swarm_orchestrator import SwarmOrchestrator  # noqa: F401

        logger.info("✅ Main application modules imported successfully")

        return True

    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error during imports: {e}")
        return False


def test_error_handling():
    """Test error handling utilities"""
    logger.info("🔍 Testing error handling...")

    try:
        from utils.error_handler import SwarmError, ErrorCode, create_error_response

        # Test basic error creation
        error = SwarmError("Test error", ErrorCode.VALIDATION_ERROR)
        assert error.message == "Test error"
        assert error.error_code == ErrorCode.VALIDATION_ERROR

        # Test error response creation
        response, status_code = create_error_response(error)
        assert status_code == 500  # Default status
        assert "error" in response

        logger.info("✅ Error handling tests passed")
        return True

    except Exception as e:
        logger.error(f"❌ Error handling test failed: {e}")
        return False


async def test_async_utilities():
    """Test async utilities"""
    logger.info("🔍 Testing async utilities...")

    try:
        from utils.async_utils import AsyncTaskManager, AsyncCache

        # Test task manager
        task_manager = AsyncTaskManager(max_workers=2)
        status = task_manager.get_status()
        assert "running_tasks" in status
        assert "max_workers" in status

        # Test async cache
        cache = AsyncCache(default_ttl=1)
        await cache.set("test_key", "test_value")
        value = await cache.get("test_key")
        assert value == "test_value"

        # Test cache expiration
        await asyncio.sleep(1.1)
        expired_value = await cache.get("test_key")
        assert expired_value is None

        logger.info("✅ Async utilities tests passed")
        return True

    except Exception as e:
        logger.error(f"❌ Async utilities test failed: {e}")
        return False


def test_service_registry():
    """Test service registry functionality"""
    logger.info("🔍 Testing service registry...")

    try:
        from utils.service_utils import (
            BaseService,
            ServiceRegistry,
            ServiceStatus,
            ServiceHealth,
        )

        # Create test service
        class TestService(BaseService):
            def __init__(self):
                super().__init__("test_service")

            async def _health_check(self):
                return ServiceHealth(
                    status=ServiceStatus.HEALTHY,
                    message="Test service is healthy",
                    details={"test": True},
                )

        # Test service registration
        registry = ServiceRegistry()
        test_service = TestService()
        registry.register(test_service)

        # Test service retrieval
        retrieved_service = registry.get_service("test_service")
        assert retrieved_service is not None
        assert retrieved_service.service_name == "test_service"

        logger.info("✅ Service registry tests passed")
        return True

    except Exception as e:
        logger.error(f"❌ Service registry test failed: {e}")
        return False


async def test_mcp_filesystem():
    """Test MCP filesystem service"""
    logger.info("🔍 Testing MCP filesystem service...")

    try:
        from services.mcp_filesystem import MCPFilesystemService

        # Create test workspace
        workspace_path = "/tmp/swarm_test_workspace"
        os.makedirs(workspace_path, exist_ok=True)

        # Initialize service
        mcp_service = MCPFilesystemService(workspace_path)

        # Test workspace info
        workspace_info = mcp_service.get_workspace_info()
        assert workspace_info["workspace_path"] == workspace_path
        assert workspace_info["status"] == "healthy"

        # Test file operations
        test_content = "Hello, Swarm!"
        result = mcp_service.write_file("test.txt", test_content, "test_agent")
        assert result["success"] is True

        read_result = mcp_service.read_file("test.txt", "test_agent")
        assert read_result["success"] is True
        assert read_result["content"] == test_content

        # Test file listing
        list_result = mcp_service.list_directory()
        assert len(list_result) > 0  # Should have at least the test file

        logger.info("✅ MCP filesystem tests passed")
        return True

    except Exception as e:
        logger.error(f"❌ MCP filesystem test failed: {e}")
        return False


def test_swarm_orchestrator():
    """Test swarm orchestrator"""
    logger.info("🔍 Testing swarm orchestrator...")

    try:
        from swarm_orchestrator import SwarmOrchestrator

        # Initialize orchestrator (without external services for testing)
        orchestrator = SwarmOrchestrator()

        # Test agent retrieval
        agents = orchestrator.get_available_agents()
        assert len(agents) > 0

        # Check for Communication Agent
        comm_agent = next(
            (agent for agent in agents if agent["id"] == "communication"), None
        )
        assert comm_agent is not None
        assert comm_agent["name"] == "Communication Agent"

        # Test agent configuration
        config = orchestrator.get_agent_config("communication")
        assert config is not None
        assert "system_prompt" in config

        # Test status
        status = orchestrator.get_status()
        assert "total_agents" in status
        assert (
            status["total_agents"] >= 6
        )  # Should have at least 6 agents including Communication Agent

        logger.info("✅ Swarm orchestrator tests passed")
        return True

    except Exception as e:
        logger.error(f"❌ Swarm orchestrator test failed: {e}")
        return False


def test_agent_service():
    """Test agent service registration and config retrieval"""
    logger.info("🔍 Testing agent service...")

    try:
        from swarm_orchestrator import SwarmOrchestrator
        from services.agent_service import (
            initialize_agent_service,
            get_agent_service,
            set_mcp_filesystem_service,
            get_agent_config,
        )
        from services.mcp_filesystem import MCPFilesystemService
        from utils.service_utils import service_registry

        orchestrator = SwarmOrchestrator()
        agent_service = initialize_agent_service(orchestrator)
        service_registry.register(agent_service)

        mcp_service = MCPFilesystemService("/tmp/swarm_test_workspace_agent")
        set_mcp_filesystem_service(mcp_service)

        retrieved = get_agent_service()
        assert retrieved is agent_service
        assert retrieved.mcp_filesystem is mcp_service

        config = get_agent_config("comms")
        assert config is not None

        logger.info("✅ Agent service tests passed")
        return True

    except Exception as e:
        logger.error(f"❌ Agent service test failed: {e}")
        return False


def test_sqlalchemy_setup():
    """Test SQLAlchemy initialization"""
    logger.info("🔍 Testing SQLAlchemy setup...")

    try:
        from main import SwarmApplication, db

        app_instance = SwarmApplication()
        flask_app = app_instance.create_app()

        assert "sqlalchemy" in flask_app.extensions
        assert app_instance.db is db

        logger.info("✅ SQLAlchemy setup tests passed")
        return True

    except Exception as e:
        logger.error(f"❌ SQLAlchemy setup test failed: {e}")
        return False


async def test_models_endpoint():
    """Test /api/models endpoint"""
    logger.info("🔍 Testing /api/models endpoint...")

    try:
        from main import SwarmApplication
        from services.openrouter_service import get_openrouter_service

        app_instance = SwarmApplication()
        flask_app = app_instance.create_app()
        await app_instance.initialize_services()

        openrouter = get_openrouter_service()
        if openrouter:
            openrouter.get_available_models = lambda: []

        with flask_app.test_client() as client:
            response = client.get("/api/models")
            assert response.status_code == 200

        logger.info("✅ /api/models endpoint tests passed")
        return True

    except Exception as e:
        logger.error(f"❌ /api/models endpoint test failed: {e}")
        return False


async def test_application_creation():
    """Test main application creation"""
    logger.info("🔍 Testing application creation...")

    try:
        from main import SwarmApplication

        # Create application instance
        app_instance = SwarmApplication()

        # Test configuration loading
        config = app_instance._load_config()
        assert isinstance(config, dict)
        assert "HOST" in config
        assert "PORT" in config

        # Test Flask app creation
        flask_app = app_instance.create_app()
        assert flask_app is not None
        assert hasattr(flask_app, "config")

        logger.info("✅ Application creation tests passed")
        return True

    except Exception as e:
        logger.error(f"❌ Application creation test failed: {e}")
        return False


async def run_all_tests():
    """Run all backend tests"""
    logger.info("🚀 Starting Backend Service Tests")
    logger.info("=" * 50)

    test_results = []

    # Synchronous tests
    test_results.append(("Module Imports", test_imports()))
    test_results.append(("Error Handling", test_error_handling()))
    test_results.append(("Service Registry", test_service_registry()))
    test_results.append(("Swarm Orchestrator", test_swarm_orchestrator()))
    test_results.append(("Agent Service", test_agent_service()))

    # Asynchronous tests
    test_results.append(("Async Utilities", await test_async_utilities()))
    test_results.append(("MCP Filesystem", await test_mcp_filesystem()))
    test_results.append(("Application Creation", await test_application_creation()))
    test_results.append(("SQLAlchemy Setup", test_sqlalchemy_setup()))
    test_results.append(("Models Endpoint", await test_models_endpoint()))

    # Print results
    logger.info("\n" + "=" * 50)
    logger.info("📊 TEST RESULTS SUMMARY")
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
        logger.info("🎉 All backend tests passed!")
        return True
    else:
        logger.error(f"❌ {failed} test(s) failed")
        return False


if __name__ == "__main__":
    # Set test environment
    os.environ.update(
        {
            "DATABASE_URL": "sqlite:///test_swarm.db",
            "OPENROUTER_API_KEY": "test-key",
            "SUPERMEMORY_API_KEY": "test-key",
            "SUPERMEMORY_BASE_URL": "http://localhost:8080",
            "DEBUG": "true",
        }
    )

    # Run tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
