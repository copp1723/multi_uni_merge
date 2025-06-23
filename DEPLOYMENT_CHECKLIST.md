# Multi-Uni-Merge Deployment Checklist

## Pre-Deployment Verification

### 1. Environment Variables Required
Ensure these are set in your deployment platform (e.g., Render):

```bash
# Required
DATABASE_URL=postgresql://user:pass@host:port/dbname
OPENROUTER_API_KEY=your-openrouter-api-key
SUPERMEMORY_API_KEY=your-supermemory-api-key
SUPERMEMORY_BASE_URL=https://api.supermemory.io

# Optional but recommended
MAILGUN_API_KEY=your-mailgun-key
MAILGUN_DOMAIN=your-domain.com
MAILGUN_WEBHOOK_SIGNING_KEY=your-webhook-key
NOTIFICATION_EMAIL=admin@example.com

# Server configuration
PORT=10000  # Render uses 10000
HOST=0.0.0.0
DEBUG=false
SECRET_KEY=your-secret-key-change-in-production
```

### 2. Frontend Build Status
- [x] Frontend is built and available in `frontend/dist/`
- [x] React app is properly configured
- [x] Static files are served from Flask

### 3. Backend Fixes Applied
- [x] Fixed `create_app()` function to handle module-level initialization
- [x] Updated `app.py` to properly export Flask app and SocketIO
- [x] Added test endpoints for all core features

## Deployment Steps

### 1. Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application locally
python app.py

# In another terminal, run the test suite
python test_deployment.py
```

### 2. Docker Testing (Optional)
```bash
# Build the Docker image
docker build -t multi-uni-merge .

# Run the container
docker run -p 5000:10000 \
  -e DATABASE_URL=sqlite:///test.db \
  -e OPENROUTER_API_KEY=test-key \
  -e SUPERMEMORY_API_KEY=test-key \
  -e SUPERMEMORY_BASE_URL=http://test \
  multi-uni-merge
```

### 3. Deploy to Render
1. Push code to GitHub
2. Connect repository to Render
3. Set environment variables in Render dashboard
4. Deploy using the existing `render.yaml` configuration

## Post-Deployment Testing

### 1. Basic Health Check
```bash
curl https://your-app.onrender.com/api/health
```

### 2. Run Test Suite
```bash
# Update BASE_URL in test_deployment.py to your deployment URL
python test_deployment.py
```

### 3. Test Individual Features

#### MCP Filesystem Test
```bash
# List files
curl https://your-app.onrender.com/api/test/mcp-filesystem

# Create test file
curl -X POST https://your-app.onrender.com/api/test/mcp-filesystem \
  -H "Content-Type: application/json" \
  -d '{"filename": "test.txt", "content": "Hello MCP!"}'
```

#### Supermemory Test
```bash
# Store memory
curl -X POST https://your-app.onrender.com/api/test/supermemory \
  -H "Content-Type: application/json" \
  -d '{"action": "store", "content": "Test memory"}'

# Search memories
curl -X POST https://your-app.onrender.com/api/test/supermemory \
  -H "Content-Type: application/json" \
  -d '{"action": "search", "query": "test"}'
```

#### OpenRouter Test
```bash
curl -X POST https://your-app.onrender.com/api/test/openrouter \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello!", "model": "openai/gpt-3.5-turbo"}'
```

#### Collaboration Test
```bash
curl -X POST https://your-app.onrender.com/api/test/collaboration \
  -H "Content-Type: application/json" \
  -d '{"message": "@research analyze this @coding implement it"}'
```

#### All Systems Test
```bash
curl https://your-app.onrender.com/api/test/all
```

## Troubleshooting

### Frontend Not Loading
1. Check if `frontend/dist/` exists
2. Verify Flask static folder configuration
3. Check browser console for errors

### Services Not Initialized
1. Check environment variables are set correctly
2. Review application logs for initialization errors
3. Verify API keys are valid

### WebSocket Connection Issues
1. Ensure CORS is properly configured
2. Check if deployment platform supports WebSockets
3. Verify SocketIO configuration

### Database Connection Failed
1. Verify DATABASE_URL format
2. Check database accessibility from deployment
3. Run migrations if needed: `python backend/main.py --migrate`

## API Endpoints Reference

### Core Endpoints
- `GET /` - Frontend application
- `GET /api/health` - Health check
- `GET /api/system/status` - Detailed system status
- `GET /api/models` - Available AI models
- `GET /api/agents` - Available agents

### Test Endpoints
- `GET/POST /api/test/mcp-filesystem` - Test MCP filesystem
- `POST /api/test/supermemory` - Test Supermemory
- `POST /api/test/openrouter` - Test OpenRouter
- `POST /api/test/collaboration` - Test collaboration
- `GET /api/test/all` - Run all tests

### WebSocket
- `/socket.io` - WebSocket connection endpoint
- Namespace: `/swarm` - Multi-agent collaboration

## Success Criteria

Your deployment is successful when:
1. ✅ Health check returns `{"status": "success"}`
2. ✅ Frontend loads and displays React app
3. ✅ All test endpoints return successful responses
4. ✅ WebSocket connections can be established
5. ✅ No critical errors in application logs

## Next Steps

After successful deployment:
1. Monitor application logs for any errors
2. Set up monitoring/alerting
3. Configure backup strategies
4. Document any deployment-specific configurations
5. Create user documentation for the frontend interface