#!/usr/bin/env python3
"""
Debug script to diagnose deployment issues
Run this on Render to see what's happening
"""

import os
import sys
from pathlib import Path

def debug_paths():
    """Debug file paths and locations"""
    print("=" * 60)
    print("🔍 DEPLOYMENT DEBUGGING")
    print("=" * 60)
    
    # Current working directory
    print(f"\n📂 Current Working Directory: {os.getcwd()}")
    print(f"📂 Script Location: {os.path.abspath(__file__)}")
    
    # Python path
    print(f"\n🐍 Python Path:")
    for p in sys.path[:5]:  # First 5 entries
        print(f"   - {p}")
    
    # Check for key directories
    print(f"\n📁 Directory Structure:")
    root = Path.cwd()
    
    directories_to_check = [
        ".",
        "frontend",
        "frontend/dist",
        "frontend/dist/assets",
        "backend",
        "dist",
        "static"
    ]
    
    for dir_path in directories_to_check:
        full_path = root / dir_path
        exists = "✅" if full_path.exists() else "❌"
        print(f"   {exists} {dir_path}: {full_path.exists()}")
        
        if full_path.exists() and full_path.is_dir():
            try:
                contents = list(full_path.iterdir())[:5]  # First 5 items
                if contents:
                    print(f"      Contents: {[f.name for f in contents]}")
            except:
                print(f"      (Cannot list contents)")
    
    # Check for specific files
    print(f"\n📄 Key Files:")
    files_to_check = [
        "app.py",
        "wsgi.py",
        "backend/main.py",
        "frontend/dist/index.html",
        "frontend/dist/assets/index-BymReueV.js",
        "requirements.txt",
        "package.json",
        "render.yaml"
    ]
    
    for file_path in files_to_check:
        full_path = root / file_path
        exists = "✅" if full_path.exists() else "❌"
        print(f"   {exists} {file_path}")
    
    # Environment variables (hide sensitive data)
    print(f"\n🔧 Environment Variables:")
    env_vars = [
        "PORT",
        "PYTHON_VERSION",
        "FLASK_ENV",
        "DEBUG",
        "NODE_ENV",
        "RENDER",
        "RENDER_SERVICE_NAME",
        "RENDER_SERVICE_TYPE"
    ]
    
    for var in env_vars:
        value = os.getenv(var, "(not set)")
        print(f"   {var}: {value}")
    
    # Check if API keys are configured (don't print values!)
    print(f"\n🔑 API Keys Configured:")
    api_keys = [
        "OPENROUTER_API_KEY",
        "SUPERMEMORY_API_KEY",
        "DATABASE_URL",
        "SECRET_KEY"
    ]
    
    for key in api_keys:
        configured = "✅" if os.getenv(key) else "❌"
        print(f"   {configured} {key}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    debug_paths()
