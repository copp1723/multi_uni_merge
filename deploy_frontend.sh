#!/bin/bash
# Quick script to build frontend and deploy

echo "🚀 Building frontend for deployment..."

# Navigate to frontend
cd frontend

# Clean previous build
rm -rf dist

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build the frontend
echo "🏗️ Building production bundle..."
npm run build

# Verify build
if [ -d "dist" ]; then
    echo "✅ Build successful!"
    echo "📁 Dist contents:"
    ls -la dist/
    
    # Go back to root
    cd ..
    
    # Temporarily modify .gitignore to allow dist
    echo "📝 Modifying .gitignore..."
    sed -i.bak 's/frontend\/dist\//# frontend\/dist\//' .gitignore
    
    # Add and commit
    echo "📤 Committing build files..."
    git add frontend/dist -f
    git commit -m "Deploy: Add pre-built frontend for Render"
    
    echo "🎯 Ready to push! Run: git push"
    echo "⚠️  Remember to revert .gitignore after deployment succeeds"
else
    echo "❌ Build failed - dist directory not created"
    exit 1
fi
