#!/bin/bash

# Quick build script for frontend
cd /Users/copp1723/Desktop/multi_uni_merge-main/frontend

echo "Installing dependencies..."
npm install

echo "Building frontend..."
npm run build

echo "Checking build output..."
if [ -d "dist" ]; then
    echo "✅ Build successful!"
    ls -la dist/
else
    echo "❌ Build failed - no dist directory"
fi
