"""
MCP Filesystem Service - Model Context Protocol filesystem access for agents
Provides secure, sandboxed file operations for AI agents
"""

import hashlib
import json
import logging
import mimetypes
import os
import shutil
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Import BaseService using relative imports
from ..utils.service_utils import BaseService, ServiceHealth, ServiceStatus

logger = logging.getLogger(__name__)

@dataclass
class FileInfo:
    """Represents file information"""
    path: str
    name: str
    size: int
    mime_type: str
    created_at: str
    modified_at: str
    is_directory: bool
    permissions: str
    checksum: Optional[str] = None

@dataclass
class FileOperation:
    """Represents a file operation for audit logging"""
    operation: str  # read, write, create, delete, move, copy
    path: str
    agent_id: str
    timestamp: str
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class MCPFilesystemService(BaseService):
    """Service for secure filesystem access via Model Context Protocol"""
    
    def __init__(
        self, 
        base_path: str = "/tmp/swarm_workspace", 
        max_file_size: int = 10 * 1024 * 1024  # 10MB default
    ):
        super().__init__("mcp_filesystem")  # Initialize BaseService with service name
        self.base_path = Path(base_path).resolve()
        self.max_file_size = max_file_size
        self.allowed_extensions = {
            ".txt", ".md", ".json", ".yaml", ".yml", ".csv", ".log", 
            ".py", ".js", ".html", ".css", ".xml", ".sql", ".sh", 
            ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"
        }
        self.operation_log = []
        
        # Create base workspace if it doesn't exist
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Set up secure permissions
        os.chmod(self.base_path, 0o755)
        
        logger.info(f"✅ MCP Filesystem initialized with base path: {self.base_path}")
    
    async def _health_check(self) -> ServiceHealth:
        """Implement service-specific health check"""
        try:
            # Check if base path exists and is writable
            if not self.base_path.exists():
                return ServiceHealth(
                    status=ServiceStatus.UNHEALTHY, 
                    message="Base path does not exist", 
                    details={"error": "Base path does not exist"}, 
                    last_check=datetime.now(timezone.utc).isoformat()
                )
            
            # Test write permissions
            test_file = self.base_path / ".health_check"
            test_file.write_text("health check")
            test_file.unlink()
            
            return ServiceHealth(
                status=ServiceStatus.HEALTHY, 
                message="Service operational", 
                details={
                    "base_path": str(self.base_path),
                    "max_file_size": self.max_file_size,
                    "permissions": "writable"
                }, 
                last_check=datetime.now(timezone.utc).isoformat()
            )
        except Exception as e:
            return ServiceHealth(
                status=ServiceStatus.UNHEALTHY, 
                message=f"Filesystem error: {str(e)}", 
                details={"error": str(e)}, 
                last_check=datetime.now(timezone.utc).isoformat()
            )
    
    def _validate_path(self, path: str) -> Path:
        """Validate and resolve path within workspace boundaries"""
        try:
            # Convert to Path object and resolve
            target_path = Path(path)
            
            # If relative path, make it relative to base_path
            if not target_path.is_absolute():
                target_path = self.base_path / target_path
            else:
                target_path = target_path.resolve()
            
            # Ensure path is within workspace
            try:
                target_path.relative_to(self.base_path)
            except ValueError:
                raise ValueError(
                    f"Path outside workspace: {path}",
                    error_code="PATH_OUTSIDE_WORKSPACE",
                    details={"path": str(path), "workspace": str(self.base_path)},
                )
            
            return target_path
            
        except Exception as e:
            raise ValueError(
                f"Invalid path: {path} - {str(e)}",
                error_code="INVALID_PATH",
                details={"path": str(path)},
            )
    
    def _validate_file_extension(self, path: Path) -> bool:
        """Validate file extension is allowed"""
        return path.suffix.lower() in self.allowed_extensions
    
    def _validate_file_size(self, size: int) -> bool:
        """Validate file size is within limits"""
        return size <= self.max_file_size
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return ""
    
    def _log_operation(self, operation: FileOperation) -> None:
        """Log file operation for audit trail"""
        self.operation_log.append(operation)
        
        # Keep only last 1000 operations
        if len(self.operation_log) > 1000:
            self.operation_log = self.operation_log[-1000:]
        
        # Log to system logger
        status = "SUCCESS" if operation.success else "FAILED"
        logger.info(f"📁 {status}: {operation.operation.upper()} {operation.path} by {operation.agent_id}")
    
    def read_file(self, path: str, agent_id: str) -> Dict[str, Any]:
        """Read file content"""
        operation = FileOperation(
            operation="read",
            path=path,
            agent_id=agent_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=False
        )
        
        try:
            target_path = self._validate_path(path)
            
            if not target_path.exists():
                operation.error_message = "File not found"
                self._log_operation(operation)
                raise FileNotFoundError(f"File not found: {path}")
            
            if target_path.is_dir():
                operation.error_message = "Path is a directory"
                self._log_operation(operation)
                raise IsADirectoryError(f"Path is a directory: {path}")
            
            # Check file size
            file_size = target_path.stat().st_size
            if not self._validate_file_size(file_size):
                operation.error_message = f"File too large: {file_size} bytes"
                self._log_operation(operation)
                raise ValueError(f"File too large: {file_size} bytes (max: {self.max_file_size})")
            
            # Read file content
            try:
                with open(target_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try binary read for non-text files
                with open(target_path, 'rb') as f:
                    content = f.read()
                    content = f"<binary file: {len(content)} bytes>"
            
            operation.success = True
            operation.metadata = {"file_size": file_size}
            self._log_operation(operation)
            
            return {
                "success": True,
                "content": content,
                "path": str(target_path.relative_to(self.base_path)),
                "size": file_size,
                "mime_type": mimetypes.guess_type(str(target_path))[0] or "application/octet-stream"
            }
            
        except Exception as e:
            operation.error_message = str(e)
            self._log_operation(operation)
            raise
    
    def write_file(self, path: str, content: str, agent_id: str, create_dirs: bool = True) -> Dict[str, Any]:
        """Write content to file"""
        operation = FileOperation(
            operation="write",
            path=path,
            agent_id=agent_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=False
        )
        
        try:
            target_path = self._validate_path(path)
            
            # Validate file extension
            if not self._validate_file_extension(target_path):
                operation.error_message = f"File extension not allowed: {target_path.suffix}"
                self._log_operation(operation)
                raise ValueError(f"File extension not allowed: {target_path.suffix}")
            
            # Validate content size
            content_size = len(content.encode('utf-8'))
            if not self._validate_file_size(content_size):
                operation.error_message = f"Content too large: {content_size} bytes"
                self._log_operation(operation)
                raise ValueError(f"Content too large: {content_size} bytes (max: {self.max_file_size})")
            
            # Create parent directories if needed
            if create_dirs:
                target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Calculate checksum
            checksum = self._calculate_checksum(target_path)
            
            operation.success = True
            operation.metadata = {"file_size": content_size, "checksum": checksum}
            self._log_operation(operation)
            
            return {
                "success": True,
                "path": str(target_path.relative_to(self.base_path)),
                "size": content_size,
                "checksum": checksum,
                "created": True
            }
            
        except Exception as e:
            operation.error_message = str(e)
            self._log_operation(operation)
            raise
    
    def list_directory(self, path: str = "", agent_id: str = "") -> List[FileInfo]:
        """List directory contents"""
        operation = FileOperation(
            operation="list",
            path=path or "/",
            agent_id=agent_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=False
        )
        
        try:
            if path:
                target_path = self._validate_path(path)
            else:
                target_path = self.base_path
            
            if not target_path.exists():
                operation.error_message = "Directory not found"
                self._log_operation(operation)
                raise FileNotFoundError(f"Directory not found: {path}")
            
            if not target_path.is_dir():
                operation.error_message = "Path is not a directory"
                self._log_operation(operation)
                raise NotADirectoryError(f"Path is not a directory: {path}")
            
            files = []
            for item in target_path.iterdir():
                try:
                    stat = item.stat()
                    
                    file_info = FileInfo(
                        path=str(item.relative_to(self.base_path)),
                        name=item.name,
                        size=stat.st_size,
                        mime_type=mimetypes.guess_type(str(item))[0] or "application/octet-stream",
                        created_at=datetime.fromtimestamp(stat.st_ctime, timezone.utc).isoformat(),
                        modified_at=datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                        is_directory=item.is_dir(),
                        permissions=oct(stat.st_mode)[-3:],
                        checksum=self._calculate_checksum(item) if item.is_file() and stat.st_size < 1024*1024 else None
                    )
                    files.append(file_info)
                except Exception as e:
                    logger.warning(f"⚠️ Could not get info for {item}: {e}")
                    continue
            
            operation.success = True
            operation.metadata = {"items_count": len(files)}
            self._log_operation(operation)
            
            return files
            
        except Exception as e:
            operation.error_message = str(e)
            self._log_operation(operation)
            raise
    
    def create_directory(self, path: str, agent_id: str) -> Dict[str, Any]:
        """Create directory"""
        operation = FileOperation(
            operation="create_dir",
            path=path,
            agent_id=agent_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=False
        )
        
        try:
            target_path = self._validate_path(path)
            
            target_path.mkdir(parents=True, exist_ok=True)
            
            operation.success = True
            self._log_operation(operation)
            
            return {
                "path": str(target_path.relative_to(self.base_path)),
                "created": True
            }
            
        except Exception as e:
            operation.error_message = str(e)
            self._log_operation(operation)
            raise
    
    def delete_file(self, path: str, agent_id: str) -> Dict[str, Any]:
        """Delete file or directory"""
        operation = FileOperation(
            operation="delete",
            path=path,
            agent_id=agent_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=False
        )
        
        try:
            target_path = self._validate_path(path)
            
            if not target_path.exists():
                operation.error_message = "File not found"
                self._log_operation(operation)
                raise FileNotFoundError(f"File not found: {path}")
            
            if target_path.is_dir():
                shutil.rmtree(target_path)
            else:
                target_path.unlink()
            
            operation.success = True
            self._log_operation(operation)
            
            return {
                "path": str(target_path.relative_to(self.base_path)),
                "deleted": True
            }
            
        except Exception as e:
            operation.error_message = str(e)
            self._log_operation(operation)
            raise
    
    def get_file_info(self, path: str, agent_id: str = "") -> FileInfo:
        """Get detailed file information"""
        try:
            target_path = self._validate_path(path)
            
            if not target_path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            
            stat = target_path.stat()
            
            return FileInfo(
                path=str(target_path.relative_to(self.base_path)),
                name=target_path.name,
                size=stat.st_size,
                mime_type=mimetypes.guess_type(str(target_path))[0] or "application/octet-stream",
                created_at=datetime.fromtimestamp(stat.st_ctime, timezone.utc).isoformat(),
                modified_at=datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                is_directory=target_path.is_dir(),
                permissions=oct(stat.st_mode)[-3:],
                checksum=self._calculate_checksum(target_path) if target_path.is_file() else None
            )
            
        except Exception as e:
            logger.error(f"❌ Error getting file info for {path}: {e}")
            raise
    
    def get_workspace_info(self) -> Dict[str, Any]:
        """Get workspace information and statistics"""
        try:
            total_size = 0
            file_count = 0
            dir_count = 0
            
            for item in self.base_path.rglob("*"):
                if item.is_file():
                    file_count += 1
                    total_size += item.stat().st_size
                elif item.is_dir():
                    dir_count += 1
            
            return {
                "workspace_path": str(self.base_path),
                "status": "healthy",
                "total_size": total_size,
                "file_count": file_count,
                "directory_count": dir_count,
                "max_file_size": self.max_file_size,
                "allowed_extensions": list(self.allowed_extensions),
                "recent_operations": len(self.operation_log)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting workspace info: {e}")
            return {"error": str(e), "status": "error"}
    
    def get_operation_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent file operations log"""
        recent_ops = self.operation_log[-limit:] if limit else self.operation_log
        return [asdict(op) for op in recent_ops]


# Global MCP filesystem service instance
mcp_filesystem_service: Optional[MCPFilesystemService] = None

def initialize_mcp_filesystem(
    base_path: str = "/tmp/swarm_workspace", 
    max_file_size: int = 10 * 1024 * 1024
) -> MCPFilesystemService:
    """Initialize MCP filesystem service"""
    global mcp_filesystem_service
    mcp_filesystem_service = MCPFilesystemService(base_path, max_file_size)
    return mcp_filesystem_service

def get_mcp_filesystem_service() -> Optional[MCPFilesystemService]:
    """Get the global MCP filesystem service instance"""
    return mcp_filesystem_service
