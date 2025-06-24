#!/bin/bash
# Debug script to verify frontend build

echo "🔍 Debugging Frontend Build..."

# Check if we're in the right directory
echo "Current directory: $(pwd)"
echo "Contents:"
ls -la

# Check frontend directory
echo -e "\n📁 Frontend directory:"
if [ -d "frontend" ]; then
    ls -la frontend/
    
    # Check if dist exists
    echo -e "\n📦 Frontend dist directory:"
    if [ -d "frontend/dist" ]; then
        ls -la frontend/dist/
        
        # Check assets
        if [ -d "frontend/dist/assets" ]; then
            echo -e "\n🎨 Assets directory:"
            ls -la frontend/dist/assets/
        else
            echo "❌ No assets directory found!"
        fi
        
        # Check for index.html
        if [ -f "frontend/dist/index.html" ]; then
            echo -e "\n✅ index.html found"
            head -20 frontend/dist/index.html
        else
            echo "❌ No index.html found!"
        fi
    else
        echo "❌ No dist directory found! Build may have failed."
    fi
else
    echo "❌ No frontend directory found!"
fi

# Check node and npm versions
echo -e "\n🔧 Build tools:"
echo "Node version: $(node --version 2>/dev/null || echo 'Not installed')"
echo "NPM version: $(npm --version 2>/dev/null || echo 'Not installed')"

# Try to build if dist doesn't exist
if [ ! -d "frontend/dist" ] && [ -d "frontend" ]; then
    echo -e "\n🔨 Attempting to build frontend..."
    cd frontend
    npm install
    npm run build
    cd ..
    
    # Check again
    if [ -d "frontend/dist" ]; then
        echo "✅ Build successful!"
        ls -la frontend/dist/
    else
        echo "❌ Build failed!"
    fi
fi