#!/usr/bin/env python3
"""Test static file serving configuration"""

import os
from flask import Flask

# Simulate the same setup as main.py
backend_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(backend_dir)
frontend_dist_path = os.path.join(project_root, "frontend", "dist")

print(f"Backend dir: {backend_dir}")
print(f"Project root: {project_root}")
print(f"Frontend dist path: {frontend_dist_path}")
print(f"Frontend dist exists: {os.path.exists(frontend_dist_path)}")

if os.path.exists(frontend_dist_path):
    print("\nContents of frontend/dist:")
    for item in os.listdir(frontend_dist_path):
        item_path = os.path.join(frontend_dist_path, item)
        if os.path.isdir(item_path):
            print(f"  📁 {item}/")
            for subitem in os.listdir(item_path):
                print(f"     - {subitem}")
        else:
            print(f"  📄 {item}")

# Test Flask static file serving
app = Flask(__name__, static_folder=frontend_dist_path, static_url_path="")

print(f"\nFlask static folder: {app.static_folder}")
print(f"Flask static URL path: {app.static_url_path}")

# Test what Flask would serve
test_paths = ["index.html", "assets/index-DGrEp1Nt.css", "assets/index-snLIN02-.js"]
for path in test_paths:
    full_path = os.path.join(app.static_folder, path)
    print(f"\n{path}: {'✓ exists' if os.path.exists(full_path) else '✗ missing'}")