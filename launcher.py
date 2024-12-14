import os
import sys
import webbrowser
from subprocess import Popen, PIPE, STDOUT
import time
import traceback
import signal
import psutil
import socket
import shutil

def get_base_path():
    """Get base path for resources"""
    if getattr(sys, '_MEIPASS', None):
        return sys._MEIPASS
    return os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

def get_resource_path(relative_path):
    """Get absolute path to resource"""
    base_path = get_base_path()
    full_path = os.path.join(base_path, relative_path)
    print(f"Looking for resource: {relative_path} at {full_path}")
    return full_path

def verify_environment():
    base_path = get_base_path()
    print(f"Base path: {base_path}")
    print(f"Directory contents: {os.listdir(base_path)}")
    
    required_files = ['run.py', 'config.py']
    required_dirs = ['app', 'instance', 'migrations']
    
    missing = []
    for file in required_files:
        path = os.path.join(base_path, file)
        if not os.path.isfile(path):
            missing.append(f"File not found: {file} (looked in {path})")
    
    for dir in required_dirs:
        path = os.path.join(base_path, dir)
        if not os.path.isdir(path):
            missing.append(f"Directory not found: {dir} (looked in {path})")
    
    if missing:
        raise Exception("\n".join(missing))

def start_app():
    flask_process = None
    try:
        print(f"Starting directory: {os.getcwd()}")
        base_path = get_base_path()
        os.chdir(base_path)
        print(f"Changed to: {os.getcwd()}")
        
        verify_environment()
        
        run_py_path = get_resource_path('run.py')
        print(f"Using run.py from: {run_py_path}")
        
        flask_process = Popen([sys.executable, run_py_path],
                            stdout=PIPE,
                            stderr=STDOUT,
                            universal_newlines=True,
                            bufsize=1,
                            cwd=base_path)
        
        print("Waiting for server to start...")
        server_started = False
        start_time = time.time()
        
        while time.time() - start_time < 30:
            output = flask_process.stdout.readline()
            if output:
                print(output.strip())
                if "Running on" in output:
                    server_started = True
                    break
            
            if flask_process.poll() is not None:
                break
            
            time.sleep(0.1)
        
        if not server_started:
            raise Exception("Flask server failed to start within 30 seconds")
        
        print("Opening browser...")
        webbrowser.open('http://127.0.0.1:5000', new=0, autoraise=True)
        
        while flask_process.poll() is None:
            output = flask_process.stdout.readline()
            if output:
                print(output.strip())
            
    except Exception as e:
        print("\nError occurred:")
        print(str(e))
        print("\nFull traceback:")
        traceback.print_exc()
    finally:
        if flask_process:
            try:
                flask_process.terminate()
            except:
                pass
        input("\nPress Enter to exit...")

if __name__ == '__main__':
    print("Starting Clinic Management System...")
    print(f"Python executable: {sys.executable}")
    print(f"Script location: {__file__}")
    print(f"Working directory: {os.getcwd()}")
    start_app() 