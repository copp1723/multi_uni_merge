#!/usr/bin/env python3
"""
Simple build test for Render deployment
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("🔍 RENDER BUILD DIAGNOSTIC")
    print(f"📁 Current directory: {os.getcwd()}")
    print(f"📋 Directory contents: {os.listdir('.')}")
    
    # Check if frontend directory exists
    if os.path.exists('frontend'):
        print("✅ Frontend directory found")
        print(f"📋 Frontend contents: {os.listdir('frontend')}")
        
        # Check if package.json exists
        package_json = Path('frontend/package.json')
        if package_json.exists():
            print("✅ package.json found")
        else:
            print("❌ package.json NOT found")
            
        # Check if dist exists
        dist_dir = Path('frontend/dist')
        if dist_dir.exists():
            print("✅ dist directory already exists")
            print(f"📋 Dist contents: {os.listdir(dist_dir)}")
        else:
            print("❌ dist directory does not exist - need to build")
            
    else:
        print("❌ Frontend directory NOT found!")
        return False
    
    # Try to build
    print("\n🔨 Attempting to build frontend...")
    try:
        os.chdir('frontend')
        
        # Install dependencies
        print("📦 Installing dependencies...")
        result = subprocess.run(['npm', 'install'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ npm install failed: {result.stderr}")
            return False
        print("✅ Dependencies installed")
        
        # Build
        print("🏗️ Building...")
        result = subprocess.run(['npm', 'run', 'build'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ npm run build failed: {result.stderr}")
            return False
        print("✅ Build completed")
        
        # Verify build output
        if Path('dist').exists():
            print("✅ dist directory created")
            if Path('dist/index.html').exists():
                print("✅ index.html created")
                return True
            else:
                print("❌ index.html not found in dist")
                return False
        else:
            print("❌ dist directory not created")
            return False
            
    except Exception as e:
        print(f"❌ Build failed with exception: {e}")
        return False

if __name__ == '__main__':
    success = main()
    if success:
        print("\n🎉 BUILD SUCCESS - Frontend ready!")
        sys.exit(0)
    else:
        print("\n💥 BUILD FAILED - Check errors above")
        sys.exit(1)

