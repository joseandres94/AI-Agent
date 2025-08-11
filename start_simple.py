#!/usr/bin/env python3
"""
AI Agent Web Generator - Simple Start Script
Direct approach to start everything.
"""

import subprocess
import sys
import time
from pathlib import Path

def print_banner():
    """Print a beautiful banner."""
    print("=" * 80)
    print("🚀 AI Agent Web Generator - Simple Start")
    print("=" * 80)
    print()

def main():
    """Main function to start everything."""
    print_banner()
    
    # Check if cloudflared is available
    try:
        subprocess.run(['cloudflared', '--version'], capture_output=True, check=True)
        print("✅ Cloudflare tunnel daemon found")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ cloudflared is not installed or not in PATH")
        print("Please install it first: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/")
        return 1
    
    # Start the main application
    print("🚀 Starting AI Agent application...")
    try:
        # Check if virtual environment exists
        venv_activate = Path(".venv/Scripts/Activate.ps1")
        if venv_activate.exists():
            print("📦 Using virtual environment...")
            # Start the application in a new PowerShell window
            subprocess.Popen([
                "powershell", "-Command",
                f"& '{venv_activate.absolute()}'; python start.py"
            ])
        else:
            print("📦 Using system Python...")
            subprocess.Popen([sys.executable, "start.py"])
        
        print("✅ Application started")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        return 1
    
    # Wait for application to start
    print("⏳ Waiting for application to start (45 seconds)...")
    time.sleep(45)
    
    # Start Cloudflare tunnels
    print("🌐 Starting Cloudflare tunnels...")
    services = [
        (8501, "Streamlit UI"),
        (8000, "API Backend"),
        (3000, "Preview Apps")
    ]
    
    for port, name in services:
        print(f"🚇 Starting tunnel for {name}...")
        try:
            # Start tunnel in a new PowerShell window
            subprocess.Popen([
                "powershell", "-Command",
                f"Write-Host 'Starting Cloudflare tunnel for {name}...'; cloudflared tunnel --url http://localhost:{port}"
            ])
            time.sleep(3)  # Small delay between tunnels
            print(f"✅ {name} tunnel started")
        except Exception as e:
            print(f"❌ Error starting {name} tunnel: {e}")
    
    print()
    print("🎉 Everything is starting!")
    print("=" * 80)
    print("📱 Your application is now accessible!")
    print()
    print("🌐 Public URLs:")
    print("   • Look for PowerShell windows that opened")
    print("   • Each window will show a URL like: https://something-random.trycloudflare.com")
    print("   • Copy those URLs - they're your public URLs!")
    print()
    print("💡 Tips:")
    print("   • Keep the PowerShell windows open to maintain tunnels")
    print("   • URLs change each time you restart")
    print("   • Share URLs with anyone, anywhere in the world")
    print("   • Press Ctrl+C to stop this script (tunnels will continue)")
    print("=" * 80)
    print()
    
    try:
        # Keep running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Script stopped (tunnels will continue running)")
        print("To stop everything, close the PowerShell windows or run:")
        print("taskkill /f /im python.exe && taskkill /f /im cloudflared.exe")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
