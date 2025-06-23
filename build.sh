#!/bin/bash

# Render Build Script for Swarm Multi-Agent System
# This script builds the frontend and prepares for deployment

set -e  # Exit on any error

echo "🚀 Starting Render build process..."

# Install Node.js dependencies and build frontend
echo "📦 Installing frontend dependencies..."
cd frontend
npm install

echo "🔨 Building frontend for production..."
npm run build

echo "📁 Verifying build output..."
ls -la dist/

echo "🔄 Moving back to root directory..."
cd ..

echo "✅ Build completed successfully!"
echo "📋 Frontend built and ready for deployment"

# Verify the dist folder exists
if [ -d "frontend/dist" ]; then
    echo "✅ Frontend dist folder exists"
    echo "📊 Build size: $(du -sh frontend/dist)"
else
    echo "❌ Frontend dist folder not found!"
    exit 1
fi

echo "🎉 Ready for Flask to serve the frontend!"

