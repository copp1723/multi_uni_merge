# Environment Variables for Render Deployment

## Required Environment Variables

### Core Application
```
SECRET_KEY=your-secret-key-here-change-in-production
HOST=0.0.0.0
PORT=5000
DEBUG=false
```

### Database (Required)
```
DATABASE_URL=postgresql://username:password@hostname:port/database_name
```

### AI Services (Required)
```
OPENROUTER_API_KEY=your-openrouter-api-key
SUPERMEMORY_API_KEY=your-supermemory-api-key
SUPERMEMORY_BASE_URL=https://api.supermemory.ai
```

### Email Service (Optional)
```
MAILGUN_API_KEY=your-mailgun-api-key
MAILGUN_DOMAIN=your-mailgun-domain.com
MAILGUN_WEBHOOK_SIGNING_KEY=your-mailgun-webhook-signing-key
NOTIFICATION_EMAIL=your-email@example.com
```

### File System (Optional - has defaults)
```
MCP_WORKSPACE_PATH=/tmp/swarm_workspace
```

## Missing Environment Variables Found
Based on the current deployment logs, you need to add:
- `SUPERMEMORY_BASE_URL` (this was missing from your current setup)

## Production Notes
1. The application is currently using Werkzeug development server
2. For production, consider using Gunicorn (already in requirements.txt)
3. The frontend needs to be built and served separately or integrated into the Flask app

## Frontend Issue
The reason you're seeing JSON instead of a UI is that:
1. The Flask app only serves API endpoints
2. The frontend (React/Vite app) is not being served
3. You need to either:
   - Build the frontend and serve it from Flask
   - Deploy frontend separately on Render
   - Add static file serving to the Flask app

## Quick Fix for Frontend
The frontend exists but isn't being served by the Flask backend. The backend is API-only currently.

