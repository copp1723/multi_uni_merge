#!/usr/bin/env python3
"""
Quick local test for the production setup
Run this to verify the fix works before waiting for Render deployment
"""

import os
import sys
import time
import subprocess
import requests
from pathlib import Path

def test_local_server():
    """Test the production server locally"""
    print("🧪 Local Production Server Test")
    print("==============================\n")
    
    # Check if app_production.py exists
    if not Path("app_production.py").exists():
        print("❌ app_production.py not found!")
        return False
    
    # Start the server
    print("🚀 Starting production server...")
    server_process = subprocess.Popen(
        [sys.executable, "app_production.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give it time to start
    print("⏳ Waiting for server to start...")
    time.sleep(5)
    
    try:
        # Test 1: Health check
        print("\n📋 Running tests:\n")
        
        try:
            response = requests.get("http://localhost:5000/api/health", timeout=5)
            print(f"1. Health check: {'✅ PASS' if response.status_code == 200 else '❌ FAIL'} (Status: {response.status_code})")
        except Exception as e:
            print(f"1. Health check: ❌ FAIL ({e})")
        
        # Test 2: Index.html
        try:
            response = requests.get("http://localhost:5000/", timeout=5)
            has_html = "<!DOCTYPE html>" in response.text
            print(f"2. Index.html: {'✅ PASS' if response.status_code == 200 and has_html else '❌ FAIL'} (Status: {response.status_code}, HTML: {has_html})")
        except Exception as e:
            print(f"2. Index.html: ❌ FAIL ({e})")
        
        # Test 3: Static debug endpoint
        try:
            response = requests.get("http://localhost:5000/api/debug/static", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"3. Static files debug: ✅ PASS")
                print(f"   - Frontend exists: {data.get('exists')}")
                print(f"   - Index exists: {data.get('index_exists')}")
                print(f"   - Assets exist: {data.get('assets_exists')}")
                print(f"   - Asset count: {len(data.get('assets_files', []))}")
            else:
                print(f"3. Static files debug: ❌ FAIL (Status: {response.status_code})")
        except Exception as e:
            print(f"3. Static files debug: ❌ FAIL ({e})")
        
        # Test 4: Try to load a CSS/JS file
        try:
            # Get list of assets first
            response = requests.get("http://localhost:5000/api/debug/static", timeout=5)
            if response.status_code == 200:
                assets = response.json().get('assets_files', [])
                if assets:
                    # Try to load the first asset
                    asset_name = Path(assets[0]).name
                    asset_response = requests.get(f"http://localhost:5000/assets/{asset_name}", timeout=5)
                    print(f"4. Asset loading ({asset_name}): {'✅ PASS' if asset_response.status_code == 200 else '❌ FAIL'} (Status: {asset_response.status_code})")
                else:
                    print("4. Asset loading: ⚠️  No assets found to test")
            else:
                print("4. Asset loading: ❌ FAIL (Couldn't get asset list)")
        except Exception as e:
            print(f"4. Asset loading: ❌ FAIL ({e})")
        
        print("\n✅ Test complete!")
        print("\nIf all tests passed, the production setup is working correctly.")
        print("The same code will work on Render once deployed.")
        
    finally:
        # Stop the server
        print("\n🛑 Stopping server...")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    # Check if frontend is built
    if not Path("frontend/dist/index.html").exists():
        print("⚠️  Frontend not built! Run these commands first:")
        print("   cd frontend")
        print("   npm install")
        print("   npm run build")
        print("   cd ..")
        sys.exit(1)
    
    test_local_server()