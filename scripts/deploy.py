#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys

# Configuration for VPS
VPS_USER = "mol_admin"
VPS_HOST = "masteroflaw.ge"
VPS_DIR = "/var/www/the_master_of_law"

DEPLOY_STATE_FILE = ".last_deployed_versions.json"

def get_frontend_version():
    with open("frontend/pubspec.yaml", "r") as f:
        match = re.search(r'^version:\s*(\d+\.\d+\.\d+(?:\+\d+)?)', f.read(), re.MULTILINE)
        return match.group(1) if match else "0.0.0"

def get_backend_version():
    with open("backend/app/main.py", "r") as f:
        match = re.search(r'version="(\d+\.\d+\.\d+)"', f.read())
        return match.group(1) if match else "0.0.0"

def load_deployed_state():
    if os.path.exists(DEPLOY_STATE_FILE):
        with open(DEPLOY_STATE_FILE, "r") as f:
            return json.load(f)
    return {"frontend": "0.0.0", "backend": "0.0.0"}

def save_deployed_state(state):
    with open(DEPLOY_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def run_command(cmd, cwd=None):
    print(f"🚀 Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
        sys.exit(result.returncode)

def deploy_frontend():
    print("🌐 Deploying Frontend to Firebase...")
    run_command("flutter build web --release", cwd="frontend")
    run_command("firebase deploy --only hosting", cwd="frontend")
    print("✅ Frontend deployed successfully!")

def deploy_backend():
    print("🖥️ Deploying Backend to Hetzner VPS...")
    # SSH into VPS, pull latest changes, and restart docker compose
    ssh_cmd = (
        f"ssh -o StrictHostKeyChecking=no {VPS_USER}@{VPS_HOST} "
        f"'cd {VPS_DIR} && git pull origin main && cd backend && docker compose build && docker compose up -d'"
    )
    run_command(ssh_cmd)
    print("✅ Backend deployed successfully!")

if __name__ == "__main__":
    current_frontend = get_frontend_version()
    current_backend = get_backend_version()
    
    state = load_deployed_state()
    last_frontend = state.get("frontend", "0.0.0")
    last_backend = state.get("backend", "0.0.0")
    
    print(f"Current Frontend: {current_frontend} | Last Deployed: {last_frontend}")
    print(f"Current Backend: {current_backend} | Last Deployed: {last_backend}")
    
    frontend_updated = current_frontend != last_frontend
    backend_updated = current_backend != last_backend
    
    if not frontend_updated and not backend_updated:
        print("⚡ No version bumps detected. Run ./bump.sh to update versions before deploying.")
        sys.exit(0)
        
    if frontend_updated:
        deploy_frontend()
        state["frontend"] = current_frontend
        
    if backend_updated:
        # Commit any pending changes if we are updating backend via git pull
        # (Assuming the user will push to git before running deploy, or we should remind them)
        print("⚠️ Make sure you have pushed your changes to GitHub before deploying the backend!")
        deploy_backend()
        state["backend"] = current_backend
        
    save_deployed_state(state)
    print("🎉 All done!")
