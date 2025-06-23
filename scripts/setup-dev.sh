#!/bin/bash

# 🚀 Swarm Multi-Agent System - Development Setup Script
# This script sets up the development environment for the enhanced v3.0 system

set -e  # Exit on any error

echo "🤖 Setting up Swarm Multi-Agent System v3.0 Development Environment"
echo "=================================================================="

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "current" ]; then
    echo "❌ Error: Please run this script from the swarm-platform-v3 root directory"
    exit 1
fi

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python $PYTHON_VERSION found"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed"
    exit 1
fi

NODE_VERSION=$(node --version)
echo "✅ Node.js $NODE_VERSION found"

# Check npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm is required but not installed"
    exit 1
fi

NPM_VERSION=$(npm --version)
echo "✅ npm $NPM_VERSION found"

# Setup backend
echo ""
echo "🐍 Setting up Python backend..."
cd current/backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r ../config/requirements.txt

echo "✅ Backend setup complete"

# Setup frontend
echo ""
echo "⚛️ Setting up React frontend..."
cd ../frontend

# Install dependencies
echo "📥 Installing Node.js dependencies..."
npm install

echo "✅ Frontend setup complete"

# Create .env template if it doesn't exist
cd ..
if [ ! -f ".env" ]; then
    echo ""
    echo "📝 Creating .env template..."
    cat > .env << 'EOF'
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
DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production

# MCP Filesystem
MCP_WORKSPACE_PATH=/tmp/swarm_workspace

# Redis Caching (optional)
REDIS_URL=redis://localhost:6379/0
EOF
    echo "✅ Created .env template - please update with your configuration"
else
    echo "✅ .env file already exists"
fi

# Create workspace directory
echo ""
echo "📁 Creating workspace directory..."
mkdir -p /tmp/swarm_workspace
echo "✅ Workspace directory created at /tmp/swarm_workspace"

# Final instructions
echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Update the .env file with your configuration:"
echo "   - Add your DATABASE_URL (Render PostgreSQL recommended)"
echo "   - Add your OPENROUTER_API_KEY"
echo "   - Add your SUPERMEMORY_API_KEY and SUPERMEMORY_BASE_URL"
echo ""
echo "2. Start the development servers:"
echo "   Terminal 1 (Backend):"
echo "   cd current/backend"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "   Terminal 2 (Frontend):"
echo "   cd current/frontend"
echo "   npm run dev"
echo ""
echo "3. Access the application:"
echo "   - Backend API: http://localhost:5000"
echo "   - Frontend: http://localhost:5173"
echo "   - Health Check: http://localhost:5000/api/health"
echo ""
echo "📚 Documentation:"
echo "   - Development Guide: current/docs/DEVELOPMENT_GUIDE.md"
echo "   - Deployment Guide: current/docs/DEPLOYMENT_GUIDE.md"
echo ""
echo "🤖 Happy coding with Swarm Multi-Agent System v3.0!"

