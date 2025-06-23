import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from ..utils.service_utils import BaseService, ServiceHealth, ServiceStatus
from ..utils.error_handler import SwarmError
from ..swarm_orchestrator import SwarmOrchestrator

logger = logging.getLogger(__name__)


class AgentService(BaseService):
    """Service wrapper around the SwarmOrchestrator"""

    def __init__(self, orchestrator: SwarmOrchestrator):
        super().__init__("agent")
        self.orchestrator = orchestrator
        self.mcp_filesystem = None

    async def _health_check(self) -> ServiceHealth:
        return ServiceHealth(
            status=ServiceStatus.HEALTHY,
            message="Agent service operational",
            details={"orchestrator": self.orchestrator is not None},
            last_check=datetime.now(timezone.utc).isoformat(),
        )

    def set_mcp_filesystem_service(self, mcp_service) -> None:
        self.mcp_filesystem = mcp_service

    def get_agent_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        if not self.orchestrator:
            raise SwarmError("Orchestrator not initialized")
        return self.orchestrator.get_agent_config(agent_id)


# Global instance
agent_service: Optional[AgentService] = None


def initialize_agent_service(orchestrator: SwarmOrchestrator) -> AgentService:
    global agent_service
    agent_service = AgentService(orchestrator)
    return agent_service


def get_agent_service() -> Optional[AgentService]:
    return agent_service


def set_mcp_filesystem_service(mcp_service) -> None:
    if agent_service:
        agent_service.set_mcp_filesystem_service(mcp_service)


def get_agent_config(agent_id: str) -> Optional[Dict[str, Any]]:
    if agent_service:
        return agent_service.get_agent_config(agent_id)
    return None
