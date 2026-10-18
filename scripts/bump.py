#!/usr/bin/env python3
import os
import sys
import re

def bump_frontend():
    pubspec_path = "frontend/pubspec.yaml"
    with open(pubspec_path, "r") as f:
        content = f.read()
    
    match = re.search(r'^version:\s*(\d+)\.(\d+)\.(\d+)(?:\+(\d+))?', content, re.MULTILINE)
    if not match:
        print("Could not find version in pubspec.yaml")
        sys.exit(1)
        
    major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
    build = int(match.group(4)) if match.group(4) else 0
    
    new_patch = patch + 1
    new_build = build + 1
    new_version = f"{major}.{minor}.{new_patch}+{new_build}"
    
    new_content = content[:match.start()] + f"version: {new_version}" + content[match.end():]
    with open(pubspec_path, "w") as f:
        f.write(new_content)
        
    print(f"Bumped frontend version to {new_version}")

def bump_backend():
    main_path = "backend/app/main.py"
    with open(main_path, "r") as f:
        content = f.read()
        
    match = re.search(r'version="(\d+)\.(\d+)\.(\d+)"', content)
    if not match:
        print("Could not find version in backend/app/main.py")
        sys.exit(1)
        
    major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
    new_patch = patch + 1
    new_version = f'{major}.{minor}.{new_patch}'
    
    new_content = content[:match.start()] + f'version="{new_version}"' + content[match.end():]
    with open(main_path, "w") as f:
        f.write(new_content)
        
    print(f"Bumped backend version to {new_version}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./bump.sh [frontend|backend|all]")
        sys.exit(1)
        
    target = sys.argv[1].lower()
    if target in ["frontend", "all"]:
        bump_frontend()
    if target in ["backend", "all"]:
        bump_backend()
