#!/bin/bash

# Render Build Script for Swarm Multi-Agent System
# This script builds the frontend and prepares for deployment

set -e  # Exit on any error

echo "🚀 Starting Render build process..."

# Check if we're in the right directory
if [ ! -d "frontend" ]; then
    echo "❌ Frontend directory not found! Current directory: $(pwd)"
    ls -la
    exit 1
fi

# Install Node.js dependencies and build frontend
echo "📦 Installing frontend dependencies..."
cd frontend

# Ensure we have the right Node.js version
echo "📋 Node.js version: $(node --version)"
echo "📋 NPM version: $(npm --version)"

npm install

echo "🔨 Building frontend for production..."
npm run build

echo "📁 Verifying build output..."
if [ ! -d "dist" ]; then
    echo "❌ Build failed - dist directory not created!"
    exit 1
fi

ls -la dist/

echo "🔄 Moving back to root directory..."
cd ..

echo "✅ Build completed successfully!"
echo "📋 Frontend built and ready for deployment"

# Verify the dist folder exists
if [ -d "frontend/dist" ]; then
    echo "✅ Frontend dist folder exists"
    echo "📊 Build size: $(du -sh frontend/dist)"
    echo "📋 Files in dist:"
    find frontend/dist -type f | head -10
else
    echo "❌ Frontend dist folder not found!"
    exit 1
fi

echo "🎉 Ready for Flask to serve the frontend!"

