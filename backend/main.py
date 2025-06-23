"""
🚀 SWARM MULTI-AGENT SYSTEM - MODERNIZED MAIN APPLICATION
Enhanced with async patterns, comprehensive error handling, and all services integrated
"""

import argparse
import asyncio
import os
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_migrate import Migrate, upgrade

# Add project paths
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

# Import utilities - using relative imports
from .utils.error_handler import SwarmError, create_error_response, handle_errors
from .utils.async_utils import task_manager
from .utils.service_utils import service_registry, format_api_response

# Import services - using relative imports
from .services.postgresql_service import initialize_postgresql, get_postgresql_service
from .services.openrouter_service import initialize_openrouter, get_openrouter_service
from .services.supermemory_service import initialize_supermemory, get_supermemory_service
from .services.mcp_filesystem import initialize_mcp_filesystem, get_mcp_filesystem_service
from .services.mailgun_service import initialize_mailgun, get_mailgun_service
from .services.websocket_service import initialize_websocket_service, SwarmNamespace

# Import orchestrator - using relative import
from .swarm_orchestrator import SwarmOrchestrator
from .models import db

import logging
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
        self.config = self._load_config()
        self._services_initialized = False
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        return {
            # Server configuration
            'HOST': os.getenv('HOST', '0.0.0.0'),
            'PORT': int(os.getenv('PORT', 5000)),
            'DEBUG': os.getenv('DEBUG', 'false').lower() == 'true',
            'SECRET_KEY': os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),
            
            # Database configuration
            'DATABASE_URL': os.getenv('DATABASE_URL', 'sqlite:///swarm.db'),
            
            # OpenRouter configuration
            'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY'),
            
            # Supermemory configuration
            'SUPERMEMORY_API_KEY': os.getenv('SUPERMEMORY_API_KEY'),
            'SUPERMEMORY_BASE_URL': os.getenv('SUPERMEMORY_BASE_URL'),
            
            # Mailgun configuration
            'MAILGUN_API_KEY': os.getenv('MAILGUN_API_KEY'),
            'MAILGUN_DOMAIN': os.getenv('MAILGUN_DOMAIN'),
            'MAILGUN_WEBHOOK_SIGNING_KEY': os.getenv('MAILGUN_WEBHOOK_SIGNING_KEY'),
            'NOTIFICATION_EMAIL': os.getenv('NOTIFICATION_EMAIL'),
            
            # MCP Filesystem configuration
            'MCP_WORKSPACE_PATH': os.getenv('MCP_WORKSPACE_PATH', '/tmp/swarm_workspace'),
        }
    
    def create_app(self) -> Flask:
        """Create and configure Flask application"""
        # Serve static files from frontend dist directory
        frontend_dist_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'dist')
        app = Flask(__name__, static_folder=frontend_dist_path, static_url_path='')
        
        # Configure CORS
        CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"])
        
        # Configure app
        app.config.update({
            'SECRET_KEY': self.config['SECRET_KEY'],
            'DEBUG': self.config['DEBUG'],
            'SQLALCHEMY_DATABASE_URI': self.config['DATABASE_URL'],
            'SQLALCHEMY_TRACK_MODIFICATIONS': False
        })
        
        # Initialize extensions
        db.init_app(app)
        migrate.init_app(app, db)

        # Initialize SocketIO
        socketio = SocketIO(
            app, 
            cors_allowed_origins="*", 
            async_mode='threading',
            logger=self.config['DEBUG'],
            engineio_logger=self.config['DEBUG']
        )
        
        self.app = app
        self.socketio = socketio
        
        # Register error handlers
        self._register_error_handlers()
        
        # Register routes
        self._register_routes()
        
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
            return jsonify({
                "error": {
                    "message": "Endpoint not found",
                    "code": "NOT_FOUND",
                    "details": {"path": request.path},
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }), 404
        
        @self.app.errorhandler(500)
        def handle_internal_error(error):
            logger.error(f"Internal error: {str(error)}")
            response, status_code = create_error_response(error, 500)
            return jsonify(response), status_code
    
    def _register_routes(self):
        """Register API routes"""
        
        @self.app.route('/', methods=['GET'])
        def root():
            """Serve the frontend application"""
            try:
                return self.app.send_static_file('index.html')
            except Exception:
                # Fallback to API info if frontend not available
                return jsonify(format_api_response({
                    'name': '🤖 Swarm Multi-Agent System',
                    'version': '3.0.0',
                    'status': 'operational',
                    'note': 'Frontend not built - showing API info',
                    'endpoints': {
                        'health': '/api/health',
                        'system': '/api/system',
                        'agents': '/api/agents',
                        'conversations': '/api/conversations',
                        'websocket': '/socket.io'
                    },
                    'features': [
                        '6 Specialized AI Agents (including Communication Agent)',
                        'Real-time Collaboration via WebSocket',
                        'Cross-Agent Memory Sharing',
                        'OpenRouter AI Integration',
                        'SuperMemory Knowledge Base',
                        'MCP Filesystem Access',
                        'Email Integration',
                        'Production Monitoring'
                    ]
                }))
        
        @self.app.route('/api/health', methods=['GET'])
        @handle_errors("Health check failed")
        def health_check():
            """Comprehensive health check endpoint"""
            try:
                # Get system health from service registry
                system_health = asyncio.run(service_registry.get_system_health())
                
                # Add configuration validation
                missing_configs = self._get_missing_configs()
                
                return jsonify(format_api_response({
                    'system': system_health,
                    'configuration': {
                        'valid': len(missing_configs) == 0,
                        'missing_configs': missing_configs
                    },
                    'services_initialized': self._services_initialized,
                    'version': '3.0.0'
                }))
                
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return jsonify(format_api_response(
                    data={'error': str(e)},
                    status='error',
                    message='Health check failed'
                )), 500
        
        @self.app.route('/api/system/status', methods=['GET'])
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
                
                return jsonify(format_api_response({
                    'services': {name: {
                        'status': health.status.value,
                        'message': health.message,
                        'response_time_ms': health.response_time_ms,
                        'last_check': health.last_check
                    } for name, health in all_health.items()},
                    'task_manager': task_status,
                    'orchestrator': orchestrator_status,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }))
                
            except Exception as e:
                logger.error(f"System status check failed: {e}")
                return jsonify(format_api_response(
                    data={'error': str(e)},
                    status='error',
                    message='System status check failed'
                )), 500
        
        @self.app.route('/api/agents', methods=['GET'])
        @handle_errors("Failed to get agents")
        def get_agents():
            """Get available agents"""
            if not self.orchestrator:
                raise SwarmError("Orchestrator not initialized")
            
            agents = self.orchestrator.get_available_agents()
            return jsonify(format_api_response(agents))
        
        @self.app.route('/api/agents/<agent_id>/config', methods=['GET'])
        @handle_errors("Failed to get agent config")
        def get_agent_config(agent_id: str):
            """Get agent configuration"""
            if not self.orchestrator:
                raise SwarmError("Orchestrator not initialized")
            
            config = self.orchestrator.get_agent_config(agent_id)
            if not config:
                raise SwarmError(f"Agent {agent_id} not found", status_code=404)

            return jsonify(format_api_response(config))

        @self.app.route('/api/models', methods=['GET'])
        @handle_errors("Failed to get model list")
        def get_models():
            """Get available OpenRouter models"""
            openrouter = get_openrouter_service()
            if not openrouter:
                raise SwarmError("OpenRouter service not initialized")

            models = openrouter.get_popular_models()
            data = [m.__dict__ for m in models]
            return jsonify(format_api_response(data))
    
    def _get_missing_configs(self) -> list:
        """Get list of missing required configurations"""
        required_configs = [
            'DATABASE_URL',
            'OPENROUTER_API_KEY',
            'SUPERMEMORY_API_KEY',
            'SUPERMEMORY_BASE_URL'
        ]

        optional_configs = ['MAILGUN_API_KEY', 'MAILGUN_DOMAIN']

        missing_required = [c for c in required_configs if not self.config.get(c)]
        missing_optional = [c for c in optional_configs if not self.config.get(c)]
        if missing_optional:
            logger.warning(f"⚠️ Optional configs missing: {missing_optional}")

        return missing_required
    
    async def initialize_services(self):
        """Initialize all services asynchronously"""
        logger.info("🔧 Initializing services...")
        
        try:
            # Initialize PostgreSQL service
            if self.config.get('DATABASE_URL'):
                postgresql_service = initialize_postgresql(self.config['DATABASE_URL'])
                service_registry.register(postgresql_service)
                logger.info("✅ PostgreSQL service initialized")
            else:
                logger.warning("⚠️ PostgreSQL not configured")
            
            # Initialize OpenRouter service
            if self.config.get('OPENROUTER_API_KEY'):
                openrouter_service = initialize_openrouter(self.config['OPENROUTER_API_KEY'])
                service_registry.register(openrouter_service)
                logger.info("✅ OpenRouter service initialized")
            else:
                logger.warning("⚠️ OpenRouter not configured")
            
            # Initialize Supermemory service
            if self.config.get('SUPERMEMORY_API_KEY') and self.config.get('SUPERMEMORY_BASE_URL'):
                supermemory_service = initialize_supermemory(
                    self.config['SUPERMEMORY_API_KEY'],
                    self.config['SUPERMEMORY_BASE_URL']
                )
                service_registry.register(supermemory_service)
                logger.info("✅ Supermemory service initialized")
            else:
                logger.warning("⚠️ Supermemory not configured")
            
            # Initialize MCP Filesystem service
            mcp_service = initialize_mcp_filesystem(self.config['MCP_WORKSPACE_PATH'])
            service_registry.register(mcp_service)
            logger.info("✅ MCP Filesystem service initialized")
            
            # Initialize Mailgun service (optional)
            if self.config.get('MAILGUN_API_KEY') and self.config.get('MAILGUN_DOMAIN'):
                mailgun_service = initialize_mailgun(
                    self.config['MAILGUN_API_KEY'],
                    self.config['MAILGUN_DOMAIN'],
                    self.config.get('MAILGUN_WEBHOOK_SIGNING_KEY')
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
            swarm_namespace = SwarmNamespace('/swarm', websocket_service)
            self.socketio.on_namespace(swarm_namespace)
            logger.info("✅ WebSocket service initialized")
            
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
            host = self.config['HOST']
            port = self.config['PORT']
            debug = self.config['DEBUG']
            
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
                app,
                host=host,
                port=port,
                debug=debug,
                allow_unsafe_werkzeug=True
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
            if hasattr(service, 'cleanup'):
                try:
                    await service.cleanup()
                except Exception as e:
                    logger.warning(f"Service cleanup warning: {e}")
        
        logger.info("✅ Cleanup completed")

# Create global application instance
swarm_app = SwarmApplication()

def create_app():
    """Factory function for creating Flask app (for testing/deployment)"""
    app = swarm_app.create_app()
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

if __name__ == '__main__':
    main()
