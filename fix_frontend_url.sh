#!/bin/bash

# This script ensures the frontend is built with the correct API URL

echo "🔧 Fixing frontend URL configuration..."

# Create a .env file for the frontend build if needed
cat > frontend/.env << EOF
# Dynamic API URL - the frontend will use window.location.origin in production
# This ensures it works with any deployment URL
VITE_API_URL=
EOF

echo "✅ Frontend will now use dynamic URL detection based on window.location.origin"
echo "📦 Please commit and push this change to trigger a new deployment"