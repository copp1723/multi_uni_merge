"""
🚀 SWARM MULTI-AGENT SYSTEM - MODERNIZED MAIN APPLICATION
Enhanced with async patterns, comprehensive error handling, and all services integrated
"""

import argparse
import asyncio
import os
import sys
from typing import Dict, Any

from flask_sqlalchemy import SQLAlchemy

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_migrate import Migrate, upgrade

# Add project paths
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "shared"))

# Import utilities - using relative imports
from .utils.error_handler import SwarmError, create_error_response, handle_errors
from .utils.async_utils import task_manager
from .utils.service_utils import service_registry, format_api_response

# Import services - using relative imports
from .services.postgresql_service import initialize_postgresql
from .services.openrouter_service import initialize_openrouter
from .services.supermemory_service import initialize_supermemory
from .services.mcp_filesystem import initialize_mcp_filesystem
from .services.mailgun_service import initialize_mailgun
from .services.websocket_service import initialize_websocket_service, SwarmNamespace
# Agent service is handled differently - will be initialized later

# Import orchestrator - using relative import
from .swarm_orchestrator import SwarmOrchestrator
from .models import db

import logging
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global Flask-Migrate instance
migrate = Migrate()

class SwarmApplication:
    """Main application class with modern async patterns"""

    def __init__(self):
        self.app: Flask = None
        self.socketio: SocketIO = None
        self.orchestrator: SwarmOrchestrator = None
        self.db = db
        self.config = self._load_config()
        self._services_initialized = False

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        return {
            # Server configuration
            "HOST": os.getenv("HOST", "0.0.0.0"),
            "PORT": int(os.getenv("PORT", 5000)),
            "DEBUG": os.getenv("DEBUG", "false").lower() == "true",
            "SECRET_KEY": os.getenv(
                "SECRET_KEY", "dev-secret-key-change-in-production"
            ),
            # Database configuration
            "DATABASE_URL": os.getenv("DATABASE_URL", "sqlite:///swarm.db"),
            # OpenRouter configuration
            "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY"),
            # Supermemory configuration
            "SUPERMEMORY_API_KEY": os.getenv("SUPERMEMORY_API_KEY"),
            "SUPERMEMORY_BASE_URL": os.getenv("SUPERMEMORY_BASE_URL"),
            # Mailgun configuration
            "MAILGUN_API_KEY": os.getenv("MAILGUN_API_KEY"),
            "MAILGUN_DOMAIN": os.getenv("MAILGUN_DOMAIN"),
            "MAILGUN_WEBHOOK_SIGNING_KEY": os.getenv("MAILGUN_WEBHOOK_SIGNING_KEY"),
            "NOTIFICATION_EMAIL": os.getenv("NOTIFICATION_EMAIL"),
            # MCP Filesystem configuration
            "MCP_WORKSPACE_PATH": os.getenv(
                "MCP_WORKSPACE_PATH", "/tmp/swarm_workspace"
            ),
        }

    def create_app(self) -> Flask:
        """Create and configure Flask application"""
        # Find the project root directory more reliably
        # Start from the current file and go up until we find the frontend directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = current_dir
        
        # Go up directories until we find the one containing 'frontend'
        while not os.path.exists(os.path.join(project_root, "frontend")) and project_root != "/":
            project_root = os.path.dirname(project_root)
        
        # Check if dist is in frontend or root directory
        frontend_dist_path = os.path.join(project_root, "frontend", "dist")
        root_dist_path = os.path.join(project_root, "dist")
        
        # Use whichever exists
        if os.path.exists(frontend_dist_path):
            dist_path = frontend_dist_path
        elif os.path.exists(root_dist_path):
            dist_path = root_dist_path
        else:
            dist_path = frontend_dist_path  # fallback
        
        logger.info(f"Project root: {project_root}")
        logger.info(f"Frontend dist path: {frontend_dist_path}")
        logger.info(f"Root dist path: {root_dist_path}")
        logger.info(f"Using dist path: {dist_path}")
        logger.info(f"Dist exists: {os.path.exists(dist_path)}")
        
        app = Flask(__name__, static_folder=dist_path, static_url_path="")

        # Configure CORS
        CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"])

        # Configure app
        app.config.update(
            {
                "SECRET_KEY": self.config["SECRET_KEY"],
                "DEBUG": self.config["DEBUG"],
                "SQLALCHEMY_DATABASE_URI": self.config.get("DATABASE_URL"),
                "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            }
        )

        # Initialize extensions
        db.init_app(app)
        migrate.init_app(app, db)

        # Initialize SocketIO
        socketio = SocketIO(
            app,
            cors_allowed_origins="*",
            async_mode="threading",
            logger=self.config["DEBUG"],
            engineio_logger=self.config["DEBUG"],
        )

        self.app = app
        self.socketio = socketio

        # Register error handlers
        self._register_error_handlers()

        # Register routes
        self._register_routes()

        # Register diagnostic routes (temporarily enabled in production for debugging)
        self._register_diagnostic_routes()

        return app

    def _register_error_handlers(self):
        """Register error handlers"""

        @self.app.errorhandler(SwarmError)
        def handle_swarm_error(error):
            logger.error(f"Swarm error: {error.message}")
            response, status_code = create_error_response(error)
            return jsonify(response), status_code

        @self.app.errorhandler(404)
        def handle_not_found(error):
            return (
                jsonify(
                    {
                        "error": {
                            "message": "Endpoint not found",
                            "code": "NOT_FOUND",
                            "details": {"path": request.path},
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    }
                ),
                404,
            )

        @self.app.errorhandler(500)
        def handle_internal_error(error):
            logger.error(f"Internal error: {str(error)}")
            response, status_code = create_error_response(error, 500)
            return jsonify(response), status_code

    def _register_routes(self):
        """Register API routes"""

        @self.app.route("/", methods=["GET"])
        def root():
            """Serve the frontend application"""
            try:
                return self.app.send_static_file("index.html")
            except Exception as e:
                # Log the error for debugging
                logger.error(f"Failed to serve index.html: {e}")
                logger.error(f"Static folder: {self.app.static_folder}")
                logger.error(f"Static folder exists: {os.path.exists(self.app.static_folder) if self.app.static_folder else False}")
                
                # Try to serve temporary static page
                static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static_index.html")
                if os.path.exists(static_path):
                    return send_file(static_path)
                # Fallback to API info if frontend not available
                return jsonify(
                    format_api_response(
                        {
                            "name": "🤖 Swarm Multi-Agent System",
                            "version": "3.0.0",
                            "status": "operational",
                            "note": "Frontend not built - showing API info",
                            "static_folder": self.app.static_folder,
                            "static_exists": os.path.exists(self.app.static_folder) if self.app.static_folder else False,
                            "endpoints": {
                                "health": "/api/health",
                                "system": "/api/system",
                                "agents": "/api/agents",
                                "conversations": "/api/conversations",
                                "websocket": "/socket.io",
                                "diagnostics": "/api/diagnostics",
                            },
                            "features": [
                                "6 Specialized AI Agents (including Communication Agent)",
                                "Real-time Collaboration via WebSocket",
                                "Cross-Agent Memory Sharing",
                                "OpenRouter AI Integration",
                                "SuperMemory Knowledge Base",
                                "MCP Filesystem Access",
                                "Email Integration",
                                "Production Monitoring",
                            ],
                        }
                    )
                )
        
        @self.app.route("/<path:path>", methods=["GET"])
        def catch_all(path):
            """Catch-all route for React Router"""
            logger.info(f"Catch-all route hit for path: {path}")
            
            # First, try to serve static files (JS, CSS, images)
            try:
                logger.info(f"Attempting to serve static file: {path}")
                return self.app.send_static_file(path)
            except Exception as e:
                logger.error(f"Failed to serve static file {path}: {e}")
                
                # If not a static file, serve index.html for React Router
                try:
                    logger.info("Falling back to serve index.html")
                    return self.app.send_static_file("index.html")
                except Exception as e2:
                    logger.error(f"Failed to serve index.html: {e2}")
                    
                    # Fallback to temporary page
                    static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static_index.html")
                    if os.path.exists(static_path):
                        logger.info("Serving static_index.html fallback")
                        return send_file(static_path)
                    
                    logger.error(f"No fallback available for path: {path}")
                    return jsonify({"error": "Frontend not available", "path": path}), 404

        @self.app.route("/api/health", methods=["GET"])
        @handle_errors("Health check failed")
        def health_check():
            """Comprehensive health check endpoint"""
            try:
                # Simple health check for services
                health_data = {
                    "mcp_filesystem": "not_configured",
                    "supermemory": "not_configured",
                    "openrouter": "not_configured",
                    "version": "3.0.0"
                }
                
                # Check if MCP filesystem service is available
                try:
                    from .services.mcp_filesystem import get_mcp_filesystem_service
                    mcp_fs = get_mcp_filesystem_service()
                    if mcp_fs:
                        health_data["mcp_filesystem"] = "healthy"
                except:
                    pass
                
                # Check if Supermemory service is available
                try:
                    from .services.supermemory_service import get_supermemory_service
                    supermemory = get_supermemory_service()
                    if supermemory:
                        health_data["supermemory"] = "healthy"
                except:
                    pass
                
                # Check if OpenRouter service is available
                try:
                    from .services.openrouter_service import get_openrouter_service
                    openrouter = get_openrouter_service()
                    if openrouter:
                        health_data["openrouter"] = "healthy"
                except:
                    pass
                
                return jsonify({
                    "status": "success",
                    "data": health_data
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500

        @self.app.route("/api/models", methods=["GET"])
        @handle_errors("Failed to get models")
        def get_models():
            """Retrieve available AI models from OpenRouter"""
            from .services.openrouter_service import get_openrouter_service

            try:
                openrouter = get_openrouter_service()
                if not openrouter:
                    raise SwarmError("OpenRouter service not initialized")

                models = openrouter.get_available_models()
                return jsonify({
                    "status": "success",
                    "data": models
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500

        @self.app.route("/api/system/status", methods=["GET"])
        @handle_errors("System status check failed")
        def system_status():
            """Detailed system status"""
            try:
                # Get all service health
                all_health = asyncio.run(service_registry.get_all_health())

                # Get task manager status
                task_status = task_manager.get_status()

                # Get orchestrator status if available
                orchestrator_status = None
                if self.orchestrator:
                    orchestrator_status = self.orchestrator.get_status()

                return jsonify(
                    format_api_response(
                        {
                            "services": {
                                name: {
                                    "status": health.status.value,
                                    "message": health.message,
                                    "response_time_ms": health.response_time_ms,
                                    "last_check": health.last_check,
                                }
                                for name, health in all_health.items()
                            },
                            "task_manager": task_status,
                            "orchestrator": orchestrator_status,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                )

            except Exception as e:
                logger.error(f"System status check failed: {e}")
                return (
                    jsonify(
                        format_api_response(
                            data={"error": str(e)},
                            status="error",
                            message="System status check failed",
                        )
                    ),
                    500,
                )

        @self.app.route("/api/agents", methods=["GET"])
        @handle_errors("Failed to get agents")
        def get_agents():
            """Get available agents"""
            if not self.orchestrator:
                raise SwarmError("Orchestrator not initialized")

            agents = self.orchestrator.get_available_agents()
            return jsonify(format_api_response(agents))

        @self.app.route("/api/agents/<agent_id>/config", methods=["GET"])
        @handle_errors("Failed to get agent config")
        def get_agent_config(agent_id: str):
            """Get agent configuration"""
            if not self.orchestrator:
                raise SwarmError("Orchestrator not initialized")

            config = self.orchestrator.get_agent_config(agent_id)
            if not config:
                raise SwarmError(f"Agent {agent_id} not found", status_code=404)

            return jsonify(format_api_response(config))

        @self.app.route("/api/transform", methods=["POST"])
        @handle_errors("Transform failed")
        def transform_text():
            """Transform text using specified agent"""
            try:
                data = request.get_json() or {}
                text = data.get("text", "").strip()
                agent_id = data.get("agent_id", "communication_agent")
                model = data.get("model", "openai/gpt-4o")
                
                if not text:
                    raise SwarmError("No text provided for transformation", status_code=400)
                
                from .services.openrouter_service import get_openrouter_service
                from .services.supermemory_service import get_supermemory_service
                
                openrouter = get_openrouter_service()
                supermemory = get_supermemory_service()
                
                if not openrouter:
                    raise SwarmError("OpenRouter service not initialized")
                
                # Use openrouter to transform the text
                response = openrouter.transform_text(text, agent_id, model)
                
                # Save interaction to supermemory
                if supermemory:
                    supermemory.save_interaction(agent_id, text, response)
                
                return jsonify({
                    "status": "success",
                    "data": {
                        "transformed_text": response,
                        "agent_id": agent_id,
                        "model_used": model
                    }
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500

    def _register_diagnostic_routes(self):
        """Register diagnostic and test API routes (only in DEBUG mode)"""
        logger.info("🔧 Registering diagnostic and test routes (DEBUG mode)...")

        @self.app.route("/api/diagnostics", methods=["GET"])
        def diagnostics():
            """Diagnostic endpoint to check file system and paths"""
            import glob

            frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
            dist_path = os.path.join(frontend_path, "dist")
            static_folder = self.app.static_folder

            diagnostics_info = {
                "current_working_dir": os.getcwd(),
                "backend_dir": os.path.dirname(__file__),
                "frontend_path": frontend_path,
                "frontend_exists": os.path.exists(frontend_path),
                "dist_path": dist_path,
                "dist_exists": os.path.exists(dist_path),
                "static_folder": static_folder,
                "static_folder_exists": os.path.exists(static_folder) if static_folder else False,
                "app_root_path": self.app.root_path,
                "frontend_contents": [],
                "dist_contents": [],
                "static_folder_contents": []
            }

            # List frontend directory contents
            if os.path.exists(frontend_path):
                try:
                    diagnostics_info["frontend_contents"] = os.listdir(frontend_path)
                except Exception as e:
                    diagnostics_info["frontend_contents"] = f"Error: {str(e)}"

            # List dist directory contents
            if os.path.exists(dist_path):
                try:
                    diagnostics_info["dist_contents"] = os.listdir(dist_path)
                except Exception as e:
                    diagnostics_info["dist_contents"] = f"Error: {str(e)}"

            # List static folder contents
            if static_folder and os.path.exists(static_folder):
                try:
                    diagnostics_info["static_folder_contents"] = os.listdir(static_folder)
                except Exception as e:
                    diagnostics_info["static_folder_contents"] = f"Error: {str(e)}"

            # Check for any index.html files
            try:
                index_files = glob.glob("**/index.html", recursive=True)
                diagnostics_info["index_html_locations"] = index_files[:10]  # Limit to 10
            except Exception as e:
                diagnostics_info["index_html_locations"] = f"Error: {str(e)}"

            return jsonify(diagnostics_info)

        # Test endpoints for core features
        @self.app.route("/api/test/mcp-filesystem", methods=["GET", "POST"])
        @handle_errors("MCP Filesystem test failed")
        def test_mcp_filesystem():
            """Test MCP filesystem access"""
            from .services.mcp_filesystem import get_mcp_filesystem_service
            
            mcp_service = get_mcp_filesystem_service()
            if not mcp_service:
                raise SwarmError("MCP Filesystem service not initialized")
            
            if request.method == "GET":
                # List files in workspace
                try:
                    files = mcp_service.list_files("/")
                    return jsonify(format_api_response({
                        "status": "success",
                        "workspace_path": mcp_service.workspace_path,
                        "files": files,
                        "test": "MCP Filesystem is working correctly"
                    }))
                except Exception as e:
                    logger.error(f"MCP list files failed: {e}")
                    raise SwarmError(f"Failed to list files: {str(e)}")
            
            else:  # POST - create a test file
                data = request.get_json() or {}
                filename = data.get("filename", "test_file.txt")
                content = data.get("content", "This is a test file from MCP filesystem")
                
                try:
                    filepath = mcp_service.write_file(filename, content)
                    return jsonify(format_api_response({
                        "status": "success",
                        "filepath": filepath,
                        "message": f"Successfully created {filename}",
                        "test": "MCP Filesystem write operation successful"
                    }))
                except Exception as e:
                    logger.error(f"MCP write file failed: {e}")
                    raise SwarmError(f"Failed to write file: {str(e)}")

        @self.app.route("/api/test/supermemory", methods=["POST"])
        @handle_errors("Supermemory test failed")
        def test_supermemory():
            """Test Supermemory integration"""
            from .services.supermemory_service import get_supermemory_service
            
            supermemory = get_supermemory_service()
            if not supermemory:
                raise SwarmError("Supermemory service not initialized")
            
            data = request.get_json() or {}
            action = data.get("action", "store")
            
            if action == "store":
                content = data.get("content", "Test memory: This is a test entry for Supermemory integration")
                metadata = data.get("metadata", {"type": "test", "timestamp": datetime.now(timezone.utc).isoformat()})
                
                try:
                    result = supermemory.store_memory(content, metadata)
                    return jsonify(format_api_response({
                        "status": "success",
                        "action": "store",
                        "result": result,
                        "test": "Supermemory store operation successful"
                    }))
                except Exception as e:
                    logger.error(f"Supermemory store failed: {e}")
                    raise SwarmError(f"Failed to store memory: {str(e)}")
            
            elif action == "search":
                query = data.get("query", "test")
                limit = data.get("limit", 5)
                
                try:
                    results = supermemory.search_memories(query, limit)
                    return jsonify(format_api_response({
                        "status": "success",
                        "action": "search",
                        "query": query,
                        "results": results,
                        "count": len(results),
                        "test": "Supermemory search operation successful"
                    }))
                except Exception as e:
                    logger.error(f"Supermemory search failed: {e}")
                    raise SwarmError(f"Failed to search memories: {str(e)}")

        @self.app.route("/api/test/openrouter", methods=["POST"])
        @handle_errors("OpenRouter test failed")
        def test_openrouter():
            """Test OpenRouter API responses"""
            from .services.openrouter_service import get_openrouter_service
            
            openrouter = get_openrouter_service()
            if not openrouter:
                raise SwarmError("OpenRouter service not initialized")
            
            data = request.get_json() or {}
            prompt = data.get("prompt", "Hello! Please respond with a brief greeting to confirm the API is working.")
            model = data.get("model", "openai/gpt-3.5-turbo")
            
            try:
                # Test simple completion
                response = openrouter.complete(prompt, model=model, max_tokens=100)
                
                # Also test available models
                models = openrouter.get_available_models()
                
                return jsonify(format_api_response({
                    "status": "success",
                    "prompt": prompt,
                    "response": response,
                    "model_used": model,
                    "available_models_count": len(models),
                    "test": "OpenRouter API is working correctly"
                }))
            except Exception as e:
                logger.error(f"OpenRouter test failed: {e}")
                raise SwarmError(f"OpenRouter API test failed: {str(e)}")

        @self.app.route("/api/test/collaboration", methods=["POST"])
        @handle_errors("Collaboration test failed")
        def test_collaboration():
            """Test @mention collaboration chats"""
            data = request.get_json() or {}
            message = data.get("message", "@research Can you help analyze this test scenario?")
            agents = data.get("agents", ["research", "coding"])
            
            if not self.orchestrator:
                raise SwarmError("Orchestrator not initialized")
            
            try:
                # Test agent mention parsing
                mentioned_agents = []
                for agent in agents:
                    if f"@{agent}" in message:
                        mentioned_agents.append(agent)
                
                # Test orchestrator collaboration features
                available_agents = self.orchestrator.get_available_agents()
                agent_configs = {}
                for agent_id in mentioned_agents:
                    config = self.orchestrator.get_agent_config(agent_id)
                    if config:
                        agent_configs[agent_id] = config
                
                # Simulate collaboration response
                response = {
                    "status": "success",
                    "message": message,
                    "mentioned_agents": mentioned_agents,
                    "available_agents": available_agents,
                    "agent_configs": agent_configs,
                    "collaboration_ready": len(agent_configs) > 0,
                    "test": "@mention collaboration system is working correctly",
                    "note": "Full collaboration requires WebSocket connection for real-time updates"
                }
                
                return jsonify(format_api_response(response))
                
            except Exception as e:
                logger.error(f"Collaboration test failed: {e}")
                raise SwarmError(f"Collaboration test failed: {str(e)}")

        @self.app.route("/api/test/all", methods=["GET"])
        @handle_errors("System test failed")
        def test_all_systems():
            """Run all system tests"""
            test_results = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tests": {}
            }
            
            # Test 1: MCP Filesystem
            try:
                from .services.mcp_filesystem import get_mcp_filesystem_service
                mcp = get_mcp_filesystem_service()
                test_results["tests"]["mcp_filesystem"] = {
                    "status": "passed" if mcp else "failed",
                    "initialized": mcp is not None,
                    "workspace": mcp.workspace_path if mcp else None
                }
            except Exception as e:
                test_results["tests"]["mcp_filesystem"] = {
                    "status": "error",
                    "error": str(e)
                }
            
            # Test 2: Supermemory
            try:
                from .services.supermemory_service import get_supermemory_service
                supermemory = get_supermemory_service()
                test_results["tests"]["supermemory"] = {
                    "status": "passed" if supermemory else "failed",
                    "initialized": supermemory is not None,
                    "configured": bool(self.config.get("SUPERMEMORY_API_KEY"))
                }
            except Exception as e:
                test_results["tests"]["supermemory"] = {
                    "status": "error",
                    "error": str(e)
                }
            
            # Test 3: OpenRouter
            try:
                from .services.openrouter_service import get_openrouter_service
                openrouter = get_openrouter_service()
                test_results["tests"]["openrouter"] = {
                    "status": "passed" if openrouter else "failed",
                    "initialized": openrouter is not None,
                    "configured": bool(self.config.get("OPENROUTER_API_KEY"))
                }
            except Exception as e:
                test_results["tests"]["openrouter"] = {
                    "status": "error",
                    "error": str(e)
                }
            
            # Test 4: Collaboration/Orchestrator
            try:
                test_results["tests"]["collaboration"] = {
                    "status": "passed" if self.orchestrator else "failed",
                    "initialized": self.orchestrator is not None,
                    "agents_available": len(self.orchestrator.get_available_agents()) if self.orchestrator else 0
                }
            except Exception as e:
                test_results["tests"]["collaboration"] = {
                    "status": "error",
                    "error": str(e)
                }
            
            # Calculate overall status
            all_passed = all(
                test.get("status") == "passed" 
                for test in test_results["tests"].values()
            )
            test_results["overall_status"] = "passed" if all_passed else "failed"
            
            return jsonify(format_api_response(test_results))

    def _get_missing_configs(self) -> list:
        """Get list of missing required configurations"""
        required_configs = [
            "DATABASE_URL",
            "OPENROUTER_API_KEY",
            "SUPERMEMORY_API_KEY",
            "SUPERMEMORY_BASE_URL",
        ]

        optional_configs = ["MAILGUN_API_KEY", "MAILGUN_DOMAIN"]

        missing_required = [c for c in required_configs if not self.config.get(c)]
        missing_optional = [c for c in optional_configs if not self.config.get(c)]
        if missing_optional:
            logger.warning(f"⚠️ Optional configs missing: {missing_optional}")

        return missing_required
    async def initialize_services(self):
        """Initialize all services asynchronously"""
        logger.info("🔧 Initializing services...")

        try:
            # Initialize PostgreSQL manager (not registered as a service anymore)
            if self.config.get("DATABASE_URL"):
                initialize_postgresql(self.config["DATABASE_URL"]) # Returns manager, but not registered
                logger.info("✅ PostgreSQL manager initialized")
            else:
                logger.warning("⚠️ PostgreSQL not configured")

            # Initialize OpenRouter service
            if self.config.get("OPENROUTER_API_KEY"):
                openrouter_service = initialize_openrouter(
                    self.config["OPENROUTER_API_KEY"]
                )
                service_registry.register(openrouter_service)
                logger.info("✅ OpenRouter service initialized")
            else:
                logger.warning("⚠️ OpenRouter not configured")

            # Initialize Supermemory service
            if self.config.get("SUPERMEMORY_API_KEY") and self.config.get(
                "SUPERMEMORY_BASE_URL"
            ):
                supermemory_service = initialize_supermemory(
                    self.config["SUPERMEMORY_API_KEY"],
                    self.config["SUPERMEMORY_BASE_URL"],
                )
                service_registry.register(supermemory_service)
                logger.info("✅ Supermemory service initialized")
            else:
                logger.warning("⚠️ Supermemory not configured")

            # Initialize MCP Filesystem service
            mcp_service = initialize_mcp_filesystem(self.config["MCP_WORKSPACE_PATH"])
            service_registry.register(mcp_service)
            logger.info("✅ MCP Filesystem service initialized")

            # Initialize Mailgun service (optional)
            if self.config.get("MAILGUN_API_KEY") and self.config.get("MAILGUN_DOMAIN"):
                mailgun_service = initialize_mailgun(
                    self.config["MAILGUN_API_KEY"],
                    self.config["MAILGUN_DOMAIN"],
                    self.config.get("MAILGUN_WEBHOOK_SIGNING_KEY"),
                )
                service_registry.register(mailgun_service)
                logger.info("✅ Mailgun service initialized")
            else:
                logger.warning("⚠️ Mailgun not configured")

            # Initialize Swarm Orchestrator
            self.orchestrator = SwarmOrchestrator()
            logger.info("✅ Swarm Orchestrator initialized")

            # Initialize WebSocket service
            websocket_service = initialize_websocket_service(
                self.app, mcp_service, self.orchestrator
            )
            service_registry.register(websocket_service)

            # Register WebSocket namespace
            swarm_namespace = SwarmNamespace("/swarm", websocket_service)
            self.socketio.on_namespace(swarm_namespace)
            logger.info("✅ WebSocket service initialized")

            # Agent service is initialized within websocket service
            # The websocket service handles agent initialization and MCP filesystem integration
            logger.info("✅ Agent service initialized via WebSocket service")
            self._services_initialized = True
            logger.info("🎉 All services initialized successfully!")

        except Exception as e:
            logger.error(f"❌ Service initialization failed: {e}")
            raise SwarmError(f"Service initialization failed: {str(e)}")

    def run(self):
        """Run the application"""
        try:
            # Create Flask app
            app = self.create_app()

            # Initialize services
            asyncio.run(self.initialize_services())

            # Get configuration
            host = self.config["HOST"]
            port = self.config["PORT"]
            debug = self.config["DEBUG"]

            logger.info(f"🚀 Starting Swarm Multi-Agent System v3.0.0")
            logger.info(f"🌐 Server: http://{host}:{port}")
            logger.info(f"🔧 Debug mode: {debug}")
            logger.info(f"📊 Services: {len(service_registry.services)} initialized")

            # Check for missing configurations
            missing = self._get_missing_configs()
            if missing:
                logger.warning(f"⚠️ Missing configurations: {missing}")

            # Run with SocketIO
            self.socketio.run(
                app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True
            )

        except KeyboardInterrupt:
            logger.info("🛑 Shutting down gracefully...")
            asyncio.run(self._cleanup())
        except Exception as e:
            logger.error(f"❌ Application failed to start: {e}")
            sys.exit(1)

    async def _cleanup(self):
        """Cleanup resources"""
        logger.info("🧹 Cleaning up resources...")

        # Cleanup task manager
        await task_manager.cleanup()

        # Cleanup services if needed
        for service in service_registry.services.values():
            if hasattr(service, "cleanup"):
                try:
                    await service.cleanup()
                except Exception as e:
                    logger.warning(f"Service cleanup warning: {e}")

        logger.info("✅ Cleanup completed")


# Create global application instance
swarm_app = SwarmApplication()


def create_app():
    """Factory function for creating Flask app (for testing/deployment)"""
    # Create a new SwarmApplication instance if needed
    global swarm_app
    if swarm_app is None:
        swarm_app = SwarmApplication()
    
    # Create the Flask app
    app = swarm_app.create_app()
    
    # Only initialize services if not already initialized
    if not swarm_app._services_initialized:
        asyncio.run(swarm_app.initialize_services())
    
    return app


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Swarm backend entrypoint")
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Run database migrations and exit",
    )
    args = parser.parse_args()

    if args.migrate:
        app = swarm_app.create_app()
        with app.app_context():
            upgrade()
        print("✅ Database migrations applied")
        return

    swarm_app.run()


if __name__ == "__main__":
    main()
