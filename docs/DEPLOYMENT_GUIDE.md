# 🚀 Deployment Guide - Swarm Multi-Agent System v3.0

## Overview

This guide covers deployment of the enhanced Swarm Multi-Agent System with all modern improvements including cross-agent memory, Communication Agent, and production monitoring.

## 📋 Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ / CentOS 8+ / macOS 12+
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 20GB available space
- **Network**: Internet access for AI model APIs

### Software Dependencies
- **Python**: 3.11 or higher
- **Node.js**: 20.x LTS
- **PostgreSQL**: 14+ (can use managed service like Render)
- **Redis**: 7+ (optional, for enhanced caching)
- **Docker**: 24+ (for containerized deployment)

## 🔧 Environment Configuration

### 1. Environment Variables

Create `.env` file in the `current/` directory:

```bash
# === REQUIRED CONFIGURATION ===

# Database Configuration (Render PostgreSQL example)
DATABASE_URL=postgresql://username:password@hostname:port/database_name

# OpenRouter AI Configuration
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here

# Supermemory Configuration
SUPERMEMORY_API_KEY=your-supermemory-api-key
SUPERMEMORY_BASE_URL=https://your-supermemory-instance.com

# === OPTIONAL CONFIGURATION ===

# Mailgun Email Service (optional)
MAILGUN_API_KEY=your-mailgun-api-key
MAILGUN_DOMAIN=your-domain.com
MAILGUN_WEBHOOK_SIGNING_KEY=your-webhook-signing-key

# Server Configuration
HOST=0.0.0.0
PORT=5000
DEBUG=false
SECRET_KEY=your-super-secret-key-change-this

# MCP Filesystem
MCP_WORKSPACE_PATH=/app/workspace

# Redis Caching (optional)
REDIS_URL=redis://localhost:6379/0
```

### 2. Database Setup

#### Option A: Render PostgreSQL (Recommended)
1. Create PostgreSQL database on Render
2. Copy the connection string to `DATABASE_URL`
3. Database tables will be created automatically

#### Option B: Self-hosted PostgreSQL
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE swarm_agents;
CREATE USER swarm_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE swarm_agents TO swarm_user;
\q
```

## 🐳 Docker Deployment (Recommended)

### 1. Build and Deploy

```bash
cd current
docker-compose -f config/docker-compose.yml up -d
```

### 2. Verify Deployment

```bash
# Check container status
docker-compose -f config/docker-compose.yml ps

# Check logs
docker-compose -f config/docker-compose.yml logs -f

# Test health endpoint
curl http://localhost:5000/api/health
```

### 3. Docker Compose Configuration

The `config/docker-compose.yml` includes:
- **Backend**: Python Flask application
- **Frontend**: React application with Nginx
- **Redis**: Caching layer (optional)
- **Nginx**: Reverse proxy and static file serving

## 🖥️ Manual Deployment

### 1. Backend Deployment

```bash
cd backend

# Install dependencies
pip install -r ../config/requirements.txt

# Run database migrations (if needed)
python -c "from main import create_app; app = create_app()"

# Start the application
python main.py
```

### 2. Frontend Deployment

```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Serve with nginx or your preferred web server
# Build files will be in dist/ directory
```

### 3. Process Management

Use PM2 for production process management:

```bash
# Install PM2
npm install -g pm2

# Start backend
pm2 start backend/main.py --name swarm-backend --interpreter python3

# Start frontend (if serving with Node.js)
pm2 start "npm run preview" --name swarm-frontend --cwd frontend

# Save PM2 configuration
pm2 save
pm2 startup
```

## ☁️ Cloud Platform Deployment

### Render Deployment

1. **Backend Deployment**:
   - Connect your GitHub repository
   - Set build command: `pip install -r config/requirements.txt`
   - Set start command: `cd backend && python main.py`
   - Add environment variables from `.env`

2. **Frontend Deployment**:
   - Create new static site
   - Set build command: `cd frontend && npm install && npm run build`
   - Set publish directory: `frontend/dist`

### Heroku Deployment

1. **Prepare Heroku files**:
```bash
# Create Procfile in root
echo "web: cd backend && python main.py" > Procfile

# Create runtime.txt
echo "python-3.11.0" > runtime.txt
```

2. **Deploy**:
```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:mini
heroku config:set OPENROUTER_API_KEY=your-key
heroku config:set SUPERMEMORY_API_KEY=your-key
heroku config:set SUPERMEMORY_BASE_URL=your-url
git push heroku main
```

### AWS/GCP/Azure

Use the Docker containers with your preferred container orchestration:
- **AWS**: ECS, EKS, or Elastic Beanstalk
- **GCP**: Cloud Run, GKE, or App Engine
- **Azure**: Container Instances, AKS, or App Service

## 🔍 Health Monitoring

### Health Check Endpoints

```bash
# Basic health check
curl http://your-domain/api/health

# Detailed system status
curl http://your-domain/api/system/status

# Agent status
curl http://your-domain/api/agents
```

### Expected Health Response

```json
{
  "status": "success",
  "message": "Success",
  "data": {
    "system": {
      "overall_status": "healthy",
      "healthy_services": 6,
      "total_services": 6
    },
    "configuration": {
      "valid": true,
      "missing_configs": []
    },
    "services_initialized": true,
    "version": "3.0.0"
  }
}
```

## 🛠️ Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check DATABASE_URL format
   # Ensure database is accessible
   # Verify credentials
   ```

2. **OpenRouter API Errors**
   ```bash
   # Verify OPENROUTER_API_KEY
   # Check API quota and billing
   # Test with curl: curl -H "Authorization: Bearer $OPENROUTER_API_KEY" https://openrouter.ai/api/v1/models
   ```

3. **Supermemory Connection Issues**
   ```bash
   # Verify SUPERMEMORY_BASE_URL and API_KEY
   # Check network connectivity
   # Review Supermemory service logs
   ```

4. **WebSocket Connection Problems**
   ```bash
   # Check firewall settings
   # Verify WebSocket support in proxy/load balancer
   # Test direct connection to backend
   ```

### Log Analysis

```bash
# Docker logs
docker-compose -f config/docker-compose.yml logs -f backend

# Manual deployment logs
tail -f /var/log/swarm-agents/application.log

# Check specific service health
curl http://localhost:5000/api/system/status | jq '.data.services'
```

## 🔄 Updates and Maintenance

### Updating the Application

```bash
# Pull latest changes
git pull origin main

# Update dependencies
cd backend && pip install -r ../config/requirements.txt
cd frontend && npm install

# Restart services
docker-compose -f config/docker-compose.yml restart
```

### Database Migrations

```bash
# Backup database first
pg_dump $DATABASE_URL > backup.sql

# Run any new migrations
python backend/main.py --migrate
```

### Monitoring and Alerts

Set up monitoring for:
- Application health endpoints
- Database connectivity
- API response times
- Error rates
- Resource usage (CPU, memory, disk)

## 📊 Performance Optimization

### Backend Optimization
- Enable Redis caching
- Configure connection pooling
- Monitor database query performance
- Use async patterns for I/O operations

### Frontend Optimization
- Enable gzip compression
- Configure CDN for static assets
- Implement lazy loading
- Monitor bundle size

## 🔐 Security Considerations

1. **Environment Variables**: Never commit `.env` files
2. **API Keys**: Rotate regularly and use least privilege
3. **Database**: Use SSL connections and strong passwords
4. **Network**: Configure firewalls and use HTTPS
5. **Updates**: Keep dependencies updated for security patches

## 📞 Support

For deployment issues:
1. Check the health endpoints
2. Review application logs
3. Verify environment configuration
4. Test individual service connectivity
5. Consult the troubleshooting section

---

**Note**: This deployment guide is for the current v3.0 system located in the `current/` directory. Do not use archived deployment guides.

