#!/usr/bin/env python3
"""
Cloudflare Tunnel Status and Management
Shows the status of your Cloudflare tunnels and provides management functions.
"""

import subprocess
import time
import requests
import os

def check_service_status(port, service_name):
    """Check if a local service is running."""
    try:
        response = requests.get(f"http://localhost:{port}", timeout=2)
        return True, f"✅ {service_name} (port {port}): Running"
    except requests.exceptions.RequestException:
        return False, f"❌ {service_name} (port {port}): Not running"

def get_tunnel_urls():
    """Get tunnel URLs from running cloudflared processes."""
    try:
        # This is a simplified approach - in practice, you'd need to parse the cloudflared output
        # For now, we'll provide instructions
        return {
            "ui": "Check the PowerShell window for Streamlit UI tunnel URL",
            "api": "Check the PowerShell window for API tunnel URL", 
            "preview": "Check the PowerShell window for Preview tunnel URL"
        }
    except Exception as e:
        return {"error": f"Could not get tunnel URLs: {e}"}

def main():
    print("=" * 80)
    print("🌐 Cloudflare Tunnel Status")
    print("=" * 80)
    print()
    
    # Check local services
    print("🔍 Checking local services...")
    print()
    
    services = [
        (8501, "Streamlit UI"),
        (8000, "API Backend"),
        (3000, "Preview Apps")
    ]
    
    all_running = True
    for port, name in services:
        running, status = check_service_status(port, name)
        print(status)
        if not running:
            all_running = False
    
    print()
    
    if all_running:
        print("✅ All local services are running!")
        print()
        print("🌐 Cloudflare Tunnels:")
        print("   📊 Streamlit UI:     Check PowerShell window for URL")
        print("   🔌 API Backend:      Check PowerShell window for URL")
        print("   👀 Preview Apps:     Check PowerShell window for URL")
        print()
        print("💡 Instructions:")
        print("   1. Look for the PowerShell windows that opened")
        print("   2. Each window will show a URL like: https://something-random.trycloudflare.com")
        print("   3. Copy those URLs - they're your public URLs!")
        print("   4. Share them with anyone, anywhere in the world")
        print()
        print("🔧 Management:")
        print("   • To stop tunnels: Close the PowerShell windows")
        print("   • To restart: Run this script again")
        print("   • URLs change each time you restart the tunnels")
    else:
        print("❌ Some services are not running")
        print("   Please make sure your application is started first")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
