"""
PostgreSQL Configuration and Connection Helper
Handles PostgreSQL-specific setup, connection pooling, and optimization
"""

import os
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool

# Import BaseService for proper service registration
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.service_utils import BaseService, ServiceHealth, ServiceStatus

logger = logging.getLogger(__name__)

class PostgreSQLManager(BaseService):
    """Manages PostgreSQL connections and configuration"""
    
    def __init__(self, database_url: str):
        super().__init__("postgresql")  # Initialize BaseService with service name
        self.database_url = database_url
        self.parsed_url = urlparse(database_url)
        self.connection_params = self._parse_connection_params()
    
    async def _health_check(self) -> ServiceHealth:
        """Implement service-specific health check"""
        try:
            # Test connection
            conn = psycopg2.connect(
                host=self.connection_params["host"],
                port=self.connection_params["port"],
                database=self.connection_params["database"],
                user=self.connection_params["username"],
                password=self.connection_params["password"],
            )
            conn.close()
            
            return ServiceHealth(
                service_name="postgresql",
                status=ServiceStatus.HEALTHY,
                details={
                    "database": self.connection_params["database"],
                    "host": self.connection_params["host"],
                    "port": self.connection_params["port"]
                }
            )
        except Exception as e:
            return ServiceHealth(
                service_name="postgresql",
                status=ServiceStatus.UNHEALTHY,
                details={"error": str(e)}
            )
    
    def _parse_connection_params(self) -> Dict[str, Any]:
        """Parse database URL into connection parameters"""
        return {
            "host": self.parsed_url.hostname,
            "port": self.parsed_url.port or 5432,
            "database": self.parsed_url.path.lstrip("/"),
            "username": self.parsed_url.username,
            "password": self.parsed_url.password,
        }
    
    def test_connection(self) -> bool:
        """Test PostgreSQL connection"""
        try:
            conn = psycopg2.connect(
                host=self.connection_params["host"],
                port=self.connection_params["port"],
                database=self.connection_params["database"],
                user=self.connection_params["username"],
                password=self.connection_params["password"],
            )
            conn.close()
            logger.info("✅ PostgreSQL connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection failed: {e}")
            return False
    
    def create_database_if_not_exists(self, database_name: str) -> bool:
        """Create database if it doesn't exist"""
        try:
            # Connect to postgres database to create new database
            conn = psycopg2.connect(
                host=self.connection_params["host"],
                port=self.connection_params["port"],
                database="postgres",  # Connect to default postgres database
                user=self.connection_params["username"],
                password=self.connection_params["password"],
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute(
                "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (database_name,)
            )
            
            if cursor.fetchone():
                logger.info(f"ℹ️ Database '{database_name}' already exists")
            else:
                # Create database
                cursor.execute(f'CREATE DATABASE "{database_name}"')
                logger.info(f"✅ Created database '{database_name}'")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create database: {e}")
            return False
    
    def get_optimized_engine_config(self) -> Dict[str, Any]:
        """Get optimized SQLAlchemy engine configuration for PostgreSQL"""
        return {
            "poolclass": QueuePool,
            "pool_size": 20,
            "max_overflow": 30,
            "pool_timeout": 30,
            "pool_recycle": 3600,  # 1 hour
            "pool_pre_ping": True,
            "echo": False,
            "connect_args": {
                "connect_timeout": 10,
                "application_name": "swarm_multi_agent_system",
                "options": "-c timezone=UTC",
            },
        }
    
    def create_optimized_engine(self):
        """Create optimized SQLAlchemy engine for PostgreSQL"""
        config = self.get_optimized_engine_config()
        return create_engine(self.database_url, **config)
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get PostgreSQL database information"""
        try:
            engine = self.create_optimized_engine()
            
            with engine.connect() as conn:
                # Get PostgreSQL version
                version_result = conn.execute(text("SELECT version()"))
                version = version_result.scalar()
                
                # Get database size
                size_result = conn.execute(
                    text("""
                    SELECT pg_size_pretty(pg_database_size(current_database()))
                    """)
                )
                size = size_result.scalar()
                
                # Get connection count
                conn_result = conn.execute(
                    text("""
                    SELECT count(*) FROM pg_stat_activity 
                    WHERE datname = current_database()
                    """)
                )
                connections = conn_result.scalar()
                
                # Get table count
                table_result = conn.execute(
                    text("""
                    SELECT count(*) FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    """)
                )
                tables = table_result.scalar()
                
                return {
                    "version": version,
                    "size": size,
                    "active_connections": connections,
                    "table_count": tables,
                    "database_name": self.connection_params["database"],
                    "host": self.connection_params["host"],
                    "port": self.connection_params["port"],
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get database info: {e}")
            return {}
    
    def optimize_database(self) -> bool:
        """Apply PostgreSQL optimizations"""
        try:
            engine = self.create_optimized_engine()
            
            with engine.connect() as conn:
                # Enable some PostgreSQL optimizations
                optimizations = [
                    "SET shared_preload_libraries = 'pg_stat_statements'",
                    "SET log_statement = 'all'",
                    "SET log_min_duration_statement = 1000",  # Log slow queries
                    "SET checkpoint_completion_target = 0.9",
                    "SET wal_buffers = '16MB'",
                    "SET effective_cache_size = '1GB'",
                ]
                
                for optimization in optimizations:
                    try:
                        conn.execute(text(optimization))
                        logger.info(f"✅ Applied optimization: {optimization}")
                    except Exception as opt_error:
                        logger.warning(f"⚠️ Could not apply optimization {optimization}: {opt_error}")
                
                conn.commit()
                logger.info("✅ PostgreSQL optimizations applied")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to optimize database: {e}")
            return False
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get detailed connection status"""
        try:
            engine = self.create_optimized_engine()
            
            with engine.connect() as conn:
                # Get connection statistics
                stats_result = conn.execute(
                    text("""
                    SELECT 
                        state,
                        count(*) as count
                    FROM pg_stat_activity 
                    WHERE datname = current_database()
                    GROUP BY state
                    """)
                )
                
                connection_stats = {}
                for row in stats_result:
                    connection_stats[row[0] or 'unknown'] = row[1]
                
                # Get database locks
                locks_result = conn.execute(
                    text("""
                    SELECT count(*) FROM pg_locks 
                    WHERE database = (SELECT oid FROM pg_database WHERE datname = current_database())
                    """)
                )
                locks_count = locks_result.scalar()
                
                return {
                    "connection_stats": connection_stats,
                    "locks_count": locks_count,
                    "pool_info": {
                        "pool_size": 20,
                        "max_overflow": 30,
                        "timeout": 30
                    }
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get connection status: {e}")
            return {}


# Global PostgreSQL manager instance
postgresql_manager: Optional[PostgreSQLManager] = None

def initialize_postgresql(database_url: str) -> PostgreSQLManager:
    """Initialize PostgreSQL manager"""
    global postgresql_manager
    postgresql_manager = PostgreSQLManager(database_url)
    return postgresql_manager

def get_postgresql_manager() -> Optional[PostgreSQLManager]:
    """Get the global PostgreSQL manager instance"""
    return postgresql_manager

def get_postgresql_service() -> Optional[PostgreSQLManager]:
    """Alias for get_postgresql_manager for backward compatibility"""
    return get_postgresql_manager()

# Alias for backward compatibility
PostgreSQLService = PostgreSQLManager

