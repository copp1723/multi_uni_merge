#!/usr/bin/env python3
"""
Test if the Flask app is serving static files correctly
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
import requests
from pathlib import Path

def test_static_files():
    """Test static file serving"""
    print("🧪 Testing Static File Serving")
    print("=" * 60)
    
    # Start test server
    with app.test_client() as client:
        # Test root
        print("\n📄 Testing /")
        response = client.get('/')
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.content_type}")
        print(f"   Has 'Swarm Multi-Agent System': {'Swarm Multi-Agent System' in response.text}")
        
        # Test assets
        print("\n📦 Testing /assets/index-BymReueV.js")
        response = client.get('/assets/index-BymReueV.js')
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.content_type}")
        print(f"   Size: {len(response.data)} bytes")
        
        print("\n🎨 Testing /assets/index-DGrEp1Nt.css")
        response = client.get('/assets/index-DGrEp1Nt.css')
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.content_type}")
        print(f"   Size: {len(response.data)} bytes")
        
        # Test API
        print("\n🔌 Testing /api/health")
        response = client.get('/api/health')
        print(f"   Status: {response.status_code}")
        print(f"   Data: {response.json}")
        
        # Test diagnostics
        print("\n🔍 Testing /api/diagnostics")
        response = client.get('/api/diagnostics')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json
            print(f"   Current Dir: {data.get('current_working_dir')}")
            print(f"   Dist Exists: {data.get('dist_exists')}")
            print(f"   Static Folder: {data.get('static_folder')}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_static_files()
