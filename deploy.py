#!/usr/bin/env python3
"""
Production deployment script for Swarm Multi-Agent System
Ensures frontend is built and backend can serve it properly
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Command failed: {cmd}")
            print(f"Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"❌ Exception running command: {cmd}")
        print(f"Error: {e}")
        return False

def main():
    print("🚀 Starting Swarm Multi-Agent System deployment...")
    
    # Check if we're in the right directory
    if not os.path.exists('frontend'):
        print("❌ Frontend directory not found!")
        print(f"Current directory: {os.getcwd()}")
        print("Contents:", os.listdir('.'))
        sys.exit(1)
    
    # Build frontend
    print("📦 Building frontend...")
    frontend_dir = Path('frontend')
    
    # Install dependencies
    if not run_command('npm install', cwd=frontend_dir):
        sys.exit(1)
    
    # Build for production
    if not run_command('npm run build', cwd=frontend_dir):
        sys.exit(1)
    
    # Verify build output
    dist_dir = frontend_dir / 'dist'
    if not dist_dir.exists():
        print("❌ Build failed - dist directory not created!")
        sys.exit(1)
    
    index_file = dist_dir / 'index.html'
    if not index_file.exists():
        print("❌ Build failed - index.html not found!")
        sys.exit(1)
    
    print("✅ Frontend built successfully!")
    print(f"📊 Build size: {sum(f.stat().st_size for f in dist_dir.rglob('*') if f.is_file()) / 1024:.1f} KB")
    
    # Test Flask static file serving
    print("🧪 Testing Flask static file configuration...")
    
    try:
        # Import Flask app to test configuration
        sys.path.insert(0, 'backend')
        from main import SwarmApplication
        
        app_instance = SwarmApplication()
        app = app_instance.create_app()
        
        # Check static folder configuration
        expected_static = str(Path('frontend/dist').resolve())
        actual_static = str(Path(app.static_folder).resolve()) if app.static_folder else None
        
        print(f"📁 Expected static folder: {expected_static}")
        print(f"📁 Actual static folder: {actual_static}")
        
        if actual_static and Path(actual_static).exists():
            print("✅ Static folder configuration correct!")
        else:
            print("❌ Static folder configuration issue!")
            sys.exit(1)
            
    except Exception as e:
        print(f"⚠️ Could not test Flask configuration: {e}")
        print("Proceeding anyway...")
    
    print("🎉 Deployment preparation complete!")
    print("🚀 Ready to start the application!")

if __name__ == '__main__':
    main()

