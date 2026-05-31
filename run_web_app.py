# The launcher script to run the browser-based Shape Analysis App
# Built by Abhinav (GitHub: https://github.com/sudoax0n | Email: ms24115@gmail.com), Soft Matter Biophysics Lab
# Simply run: python run_web_app.py

import sys
import subprocess
import webbrowser
import time
import threading

def check_and_install_dependencies():
    dependencies = ["fastapi", "uvicorn", "jinja2", "python-multipart"]
    print("Checking web app dependencies...")
    for dep in dependencies:
        import_name = "multipart" if dep == "python-multipart" else dep
        try:
            __import__(import_name)
        except ImportError:
            print(f"Installing missing dependency: {dep}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            except Exception as e:
                print(f"Error installing {dep}: {e}")
                sys.exit(1)
    print("[OK] All dependencies checked successfully!")

def open_browser():
    # Wait for uvicorn server to start up
    time.sleep(1.5)
    url = "http://127.0.0.1:8000"
    print(f"\n[INFO] Opening browser at {url}...")
    webbrowser.open(url)

if __name__ == "__main__":
    check_and_install_dependencies()
    
    # Start browser auto-opener in a separate background thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    print("\n[INFO] Booting Uvicorn Localhost Server...")
    try:
        import uvicorn
        # Import app object directly from server module
        from web_app.server import app
        uvicorn.run(app, host="127.0.0.1", port=8000)
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped by user.")
    except Exception as e:
        print(f"Error starting server: {e}")
