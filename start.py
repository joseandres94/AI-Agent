#!/usr/bin/env python3
"""
Start script for the AI Agent Web Generator.
This script checks dependencies and starts the application.
"""

import sys
import os
import time
import signal
import subprocess
from pathlib import Path

import requests

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'streamlit',
        'requests', 
        'fastapi',
        'uvicorn'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing dependencies: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
        print("All dependencies are installed")
    else:
        print("All dependencies are installed")

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print(".env file not found")
        print("Creating .env file with template...")
        
        env_content = """# OpenAI API Configuration
        OPENAI_API_KEY=your_openai_api_key_here

        # Server Configuration
        HOST=localhost
        PORT=8000

        # Application Configuration
        DEBUG=True
        """
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("Please update your OpenAI API key in .env file")
    else:
        print("Environment configuration looks good")

def _wait_for_api(url: str, timeout_seconds: int = 40, request_timeout_seconds: float = 2.0) -> bool:
    """Wait until an API endpoint responds with HTTP 200 or timeout."""
    start = time.time()
    last_error = None
    while time.time() - start < timeout_seconds:
        try:
            resp = requests.get(url, timeout=request_timeout_seconds)
            if resp.status_code == 200:
                return True
        except Exception as e:
            last_error = e
        time.sleep(0.5)
    if last_error:
        print(f"API readiness check failed: {last_error}")
    return False


def main():
    """Main function to start API then UI, and clean up on exit."""
    print("AI Agent Web Generator")
    print("=" * 40)

    # Check dependencies and env
    check_dependencies()
    check_env_file()

    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = os.getenv("API_PORT", "8000")
    api_base = f"http://{api_host}:{api_port}"

    print("\nStarting backend API server...")
    api_cmd = [
        sys.executable, '-m', 'uvicorn', 'api.main:app',
        '--host', api_host, '--port', str(api_port)
    ]

    api_proc = None
    try:
        # Start API in background
        api_proc = subprocess.Popen(api_cmd)

        # Phase 1: wait for server to bind the port (fast, no external calls)
        if not _wait_for_api(f"{api_base}/", timeout_seconds=40, request_timeout_seconds=2.0):
            # If process died early, surface the return code
            if api_proc.poll() is not None:
                print(f"API process exited early with code {api_proc.returncode}.")
            raise RuntimeError(
                f"API did not become ready at {api_base}/. "
                "Please check for port conflicts, firewall, or missing dependencies."
            )
        print(f"API server is ready at {api_base}")

        # Phase 2: (optional) check health endpoint with a longer per-request timeout,
        # but do not block UI startup if AI provider is slow
        try:
            _ = requests.get(f"{api_base}/health", timeout=10)
        except Exception as e:
            print(f"Warning: /health check timed out or failed: {e}")

        # Start Streamlit UI (blocking)
        print("Starting Streamlit UI...")
        streamlit_cmd = [sys.executable, '-m', 'streamlit', 'run', 'app/main.py']
        subprocess.run(streamlit_cmd)

    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    except Exception as e:
        print(f"Error starting application: {e}")
    finally:
        # Ensure API process is terminated
        if api_proc and (api_proc.poll() is None):
            print("Shutting down API server...")
            try:
                # On Windows, terminate() sends CTRL-BREAK equivalent; fall back to kill
                api_proc.terminate()
                try:
                    api_proc.wait(timeout=5)
                except Exception:
                    api_proc.kill()
            except Exception as kill_err:
                print(f"Failed to terminate API process: {kill_err}")

if __name__ == "__main__":
    main()