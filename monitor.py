import os
import sys
import time
import subprocess
import requests
import signal

# Configuration
APP_DIR = "/root/.openclaw/workspace/my-first"
APP_SCRIPT = "app.py"
LOG_FILE = "app.log"
VENV_PYTHON = "venv/bin/python3"
CHECK_INTERVAL = 10  # seconds
PID_FILE = "app.pid"

def start_app():
    """Starts the Flask application."""
    print("Starting Flask application...")
    # Start the app in the background using nohup
    with open(LOG_FILE, "a") as f:
        process = subprocess.Popen(
            [VENV_PYTHON, APP_SCRIPT],
            cwd=APP_DIR,
            stdout=f,
            stderr=subprocess.STDOUT,
            start_new_session=True
        )
    
    # Save PID
    with open(PID_FILE, "w") as f:
        f.write(str(process.pid))
    
    print(f"Application started with PID: {process.pid}")

def stop_app():
    """Stops the Flask application."""
    if os.path.exists(PID_FILE):
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        
        try:
            print(f"Stopping application with PID: {pid}...")
            os.kill(pid, signal.SIGTERM)
            time.sleep(2)
            # Force kill if still running
            try:
                os.kill(pid, 0)
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
        except ProcessLookupError:
            print(f"Process {pid} not found.")
        except Exception as e:
            print(f"Error stopping process: {e}")
        
        os.remove(PID_FILE)
    else:
        print("PID file not found.")

def is_app_running():
    """Checks if the application is running and responding."""
    if not os.path.exists(PID_FILE):
        return False
    
    with open(PID_FILE, "r") as f:
        pid = int(f.read().strip())
    
    # Check if process exists
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    
    # Check if it's responding via HTTP
    try:
        response = requests.get("http://localhost:5000", timeout=2)
        if response.status_code == 200:
            return True
    except requests.exceptions.RequestException:
        return False
    
    return False

def main():
    """Main monitoring loop."""
    print("Monitor script started.")
    
    # Initial start if not running
    if not is_app_running():
        start_app()
    
    while True:
        if not is_app_running():
            print("Application is not running. Restarting...")
            start_app()
        else:
            # print("Application is running.")
            pass
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Monitor script stopped.")
        sys.exit(0)
