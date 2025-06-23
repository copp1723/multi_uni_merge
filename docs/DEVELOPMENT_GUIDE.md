# 🛠️ Development Guide - Swarm Multi-Agent System v3.0

## Overview

This guide covers development setup, architecture, and best practices for the enhanced Swarm Multi-Agent System.

## 🚀 Quick Development Setup

### 1. Prerequisites
```bash
# Required software
- Python 3.11+
- Node.js 20+
- Git
- PostgreSQL (or use Render)
- Redis (optional)
```

### 2. Clone and Setup
```bash
git clone <repository-url>
cd swarm-platform-v3/current

# Backend setup
cd backend
pip install -r ../config/requirements.txt

# Frontend setup
cd ../frontend
npm install

# Environment configuration
cp .env.example .env
# Edit .env with your configuration
```

### 3. Development Environment
```bash
# Terminal 1: Backend
cd backend
python main.py

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Redis (optional)
redis-server
```

## 🏗️ Architecture Overview

### Backend Architecture

```
backend/
├── main.py                 # Application entry point
├── swarm_orchestrator.py   # Enhanced orchestrator with Communication Agent
├── services/               # Service layer
│   ├── postgresql_service.py
│   ├── openrouter_service.py
│   ├── supermemory_service.py
│   ├── mcp_filesystem.py
│   ├── mailgun_service.py
│   └── websocket_service.py
└── utils/                  # Shared utilities
    ├── error_handler.py    # Modern error handling
    ├── async_utils.py      # Async patterns and helpers
    └── service_utils.py    # Common service patterns
```

### Key Components

#### 1. Swarm Orchestrator
- **Enhanced Agent Management**: 6 specialized agents including Communication Agent
- **Cross-Agent Memory**: Automatic context sharing via Supermemory
- **Performance Monitoring**: Real-time agent performance tracking
- **Intelligent Routing**: Smart task distribution based on agent capabilities

#### 2. Service Layer
- **Base Service Pattern**: All services inherit from `BaseService` class
- **Health Monitoring**: Automatic health checks and status reporting
- **Error Handling**: Standardized error patterns with proper logging
- **Async Support**: Modern async/await patterns throughout

#### 3. Utilities
- **Error Handler**: Comprehensive error management with context
- **Async Utils**: Task management, retry logic, caching
- **Service Utils**: Common patterns, validation, security helpers

## 🤖 Agent Development

### Communication Agent

The Communication Agent is designed to understand and maintain your authentic business tone:

```python
# Located in swarm_orchestrator.py
communication_agent = {
    "id": "communication",
    "name": "Communication Agent", 
    "role": "Text Transformation Specialist",
    "system_prompt": """You are a communication specialist who understands [USER]'s authentic business tone..."""
}
```

#### Key Features:
- **Tone Understanding**: Maintains professional yet approachable style
- **Business Context**: Emphasizes AI integration and customer experience
- **Storytelling**: Uses real examples and metaphors
- **Action-Oriented**: Includes direct calls to action

### Adding New Agents

1. **Define Agent Configuration**:
```python
new_agent = {
    "id": "unique_agent_id",
    "name": "Agent Display Name",
    "role": "Agent Specialty",
    "system_prompt": "Detailed system prompt...",
    "capabilities": ["capability1", "capability2"],
    "model_preferences": ["anthropic/claude-3.5-sonnet"]
}
```

2. **Add to Orchestrator**:
```python
# In swarm_orchestrator.py _initialize_agents method
self.agents["new_agent_id"] = SwarmAgent(new_agent)
```

3. **Test Agent**:
```python
# Test agent response
response = await orchestrator.process_message(
    "test message", 
    agent_id="new_agent_id"
)
```

## 🔧 Service Development

### Creating New Services

1. **Inherit from BaseService**:
```python
from utils.service_utils import BaseService, ServiceStatus, ServiceHealth

class MyService(BaseService):
    def __init__(self, config):
        super().__init__("my_service")
        self.config = config
    
    async def _health_check(self) -> ServiceHealth:
        # Implement health check logic
        return ServiceHealth(
            status=ServiceStatus.HEALTHY,
            message="Service is operational",
            details={"version": "1.0.0"}
        )
```

2. **Register Service**:
```python
from utils.service_utils import service_registry

# Initialize and register
my_service = MyService(config)
service_registry.register(my_service)
```

3. **Use Service**:
```python
from utils.service_utils import service_registry

service = service_registry.get_service("my_service")
health = await service.get_health()
```

### Service Patterns

#### Error Handling
```python
from utils.error_handler import handle_errors, SwarmError, ErrorCode

@handle_errors("Operation failed")
async def my_operation(self):
    try:
        result = await some_async_operation()
        self._record_request(success=True)
        return result
    except Exception as e:
        self._record_request(success=False)
        raise SwarmError(
            f"Operation failed: {str(e)}",
            ErrorCode.SERVICE_UNAVAILABLE
        )
```

#### Async Patterns
```python
from utils.async_utils import async_retry, async_timeout, AsyncCache

@async_retry(max_attempts=3, delay=1.0)
@async_timeout(30.0)
async def reliable_operation(self):
    # Operation with retry and timeout
    pass

# Caching
cache = AsyncCache(default_ttl=300)
await cache.set("key", "value")
result = await cache.get("key")
```

## 🎨 Frontend Development

### Component Structure

```
frontend/src/
├── components/
│   ├── ui/                 # Reusable UI components
│   └── EnhancedComponents.jsx  # Agent-specific components
├── hooks/                  # Custom React hooks
├── lib/                    # Utility libraries
└── App.jsx                # Main application
```

### Key Components

#### Enhanced Agent Card
```jsx
<EnhancedAgentCard
  agent={agent}
  isSelected={isSelected}
  onSelect={handleSelect}
  performance={performance}
  isOnline={isOnline}
/>
```

#### Real-time Messaging
```jsx
// WebSocket integration
const socket = io(API_BASE_URL);

socket.on('response_stream_chunk', (data) => {
  // Handle streaming response
});

socket.on('agent_status_update', (data) => {
  // Update agent status
});
```

### Adding New Features

1. **Create Component**:
```jsx
// components/NewFeature.jsx
import { useState, useEffect } from 'react';

export function NewFeature({ prop1, prop2 }) {
  const [state, setState] = useState(null);
  
  useEffect(() => {
    // Component logic
  }, []);
  
  return (
    <div>
      {/* Component JSX */}
    </div>
  );
}
```

2. **Add to App**:
```jsx
// App.jsx
import { NewFeature } from './components/NewFeature';

// In component
<NewFeature prop1={value1} prop2={value2} />
```

## 🧪 Testing

### Backend Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
cd backend
python -m pytest tests/ -v

# Test specific service
python -m pytest tests/test_services.py::test_postgresql_service -v
```

### Test Structure
```python
# tests/test_services.py
import pytest
from services.postgresql_service import PostgreSQLService

@pytest.mark.asyncio
async def test_postgresql_connection():
    service = PostgreSQLService("test_db_url")
    health = await service.get_health()
    assert health.status == ServiceStatus.HEALTHY
```

### Frontend Testing

```bash
cd frontend
npm test
```

## 🔍 Debugging

### Backend Debugging

1. **Enable Debug Mode**:
```bash
export DEBUG=true
python main.py
```

2. **Check Service Health**:
```bash
curl http://localhost:5000/api/health | jq
curl http://localhost:5000/api/system/status | jq
```

3. **Monitor Logs**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Frontend Debugging

1. **Browser DevTools**: Check console for errors
2. **Network Tab**: Monitor API calls and WebSocket connections
3. **React DevTools**: Inspect component state and props

## 📊 Performance Monitoring

### Backend Metrics

```python
# Service metrics
service = service_registry.get_service("service_name")
metrics = service.get_metrics()

# System health
system_health = await service_registry.get_system_health()
```

### Frontend Performance

```jsx
// Performance monitoring
const [responseTime, setResponseTime] = useState(0);

const sendMessage = async (message) => {
  const startTime = Date.now();
  await api.sendMessage(message);
  setResponseTime(Date.now() - startTime);
};
```

## 🔐 Security Best Practices

### Backend Security

1. **Input Validation**:
```python
from utils.service_utils import sanitize_input, validate_config

# Sanitize user input
clean_data = sanitize_input(user_data, max_length=1000)

# Validate configuration
validate_config(config, required_fields=["api_key", "url"])
```

2. **Error Handling**:
```python
# Don't expose internal errors
try:
    result = sensitive_operation()
except Exception as e:
    logger.error(f"Internal error: {e}")
    raise SwarmError("Operation failed", ErrorCode.INTERNAL_ERROR)
```

3. **Rate Limiting**:
```python
from utils.service_utils import RateLimiter

limiter = RateLimiter(max_requests=100, window_seconds=60)
if not limiter.is_allowed(user_id):
    raise SwarmError("Rate limit exceeded", ErrorCode.RATE_LIMITED)
```

### Frontend Security

1. **Environment Variables**: Use `VITE_` prefix for public variables
2. **API Keys**: Never expose in frontend code
3. **Input Sanitization**: Validate all user inputs
4. **HTTPS**: Always use HTTPS in production

## 🚀 Deployment

### Development Deployment

```bash
# Quick development deployment
cd current
docker-compose -f config/docker-compose.yml up -d
```

### Production Deployment

See `DEPLOYMENT_GUIDE.md` for comprehensive production deployment instructions.

## 📝 Code Style

### Python Style

```python
# Use type hints
def process_message(message: str, agent_id: str) -> Dict[str, Any]:
    pass

# Use async/await
async def async_operation() -> str:
    result = await some_async_call()
    return result

# Use dataclasses for structured data
from dataclasses import dataclass

@dataclass
class AgentConfig:
    id: str
    name: str
    role: str
```

### JavaScript Style

```jsx
// Use modern React patterns
const [state, setState] = useState(initialValue);

// Use async/await
const handleSubmit = async (data) => {
  try {
    await api.submitData(data);
  } catch (error) {
    console.error('Submit failed:', error);
  }
};

// Use proper prop types
function Component({ prop1, prop2, onAction }) {
  // Component logic
}
```

## 🤝 Contributing

1. **Work in `current/` directory only**
2. **Follow established patterns** in `utils/`
3. **Add tests** for new features
4. **Update documentation** for changes
5. **Use proper error handling** patterns
6. **Follow code style** guidelines

## 📚 Additional Resources

- **API Documentation**: Check `/api/health` for service status
- **WebSocket Events**: See `websocket_service.py` for event types
- **Error Codes**: Reference `error_handler.py` for standard codes
- **Service Patterns**: Follow examples in `service_utils.py`

---

**Note**: This development guide is for the current v3.0 system. Always work in the `current/` directory and follow the established patterns.

