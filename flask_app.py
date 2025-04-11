"""
Flask application for gunicorn compatibility.
This file creates a Flask app that gunicorn can use directly.
"""
import os
import logging
import threading
import subprocess
import time
import requests
from flask import Flask, request, jsonify, redirect, render_template, Response

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
           static_folder="static",
           template_folder="templates")

# FastAPI server info
fastapi_host = "127.0.0.1"
fastapi_port = 8000
fastapi_url = f"http://{fastapi_host}:{fastapi_port}"

# Start FastAPI in a separate process
def start_fastapi_server():
    """Start FastAPI server in a separate process."""
    try:
        # Command to start FastAPI
        cmd = ["uvicorn", "app:app", "--host", fastapi_host, "--port", str(fastapi_port)]
        logger.info(f"Starting FastAPI with command: {' '.join(cmd)}")
        
        # Start the server process
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Non-blocking read for error logs
        def log_stderr():
            while True:
                line = process.stderr.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    logger.error(f"FastAPI stderr: {line.strip()}")
        
        # Start thread to log stderr
        stderr_thread = threading.Thread(target=log_stderr, daemon=True)
        stderr_thread.start()
        
        # Wait for server to start (simple polling)
        for i in range(10):
            try:
                logger.info(f"Attempt {i+1}/10 to connect to FastAPI server")
                response = requests.get(f"{fastapi_url}/healthcheck")
                logger.info(f"FastAPI server responded with status {response.status_code}")
                if response.status_code == 200:
                    logger.info("FastAPI server started successfully")
                    break
            except requests.RequestException as e:
                logger.info(f"Waiting for FastAPI server to start... ({str(e)})")
                time.sleep(1)
                
                # Check if process has terminated
                if process.poll() is not None:
                    stdout, stderr = process.communicate()
                    logger.error(f"FastAPI process terminated with exit code {process.returncode}")
                    logger.error(f"FastAPI stdout: {stdout}")
                    logger.error(f"FastAPI stderr: {stderr}")
                    return None
        
        return process
    except Exception as e:
        logger.error(f"Failed to start FastAPI server: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

# Start FastAPI server in a separate thread
fastapi_process = None
def start_fastapi_background():
    """Start FastAPI server in a background thread."""
    global fastapi_process
    fastapi_process = start_fastapi_server()

# Start background thread for FastAPI
threading.Thread(target=start_fastapi_background, daemon=True).start()

# Proxy routes to FastAPI
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    """
    Proxy all requests to FastAPI server.
    """
    try:
        # Build the target URL
        target_url = f"{fastapi_url}/{path}"
        
        # Forward the request
        if request.method == 'GET':
            logger.debug(f"Forwarding GET request to {target_url}")
            resp = requests.get(target_url, params=request.args)
        elif request.method == 'POST':
            logger.debug(f"Forwarding POST request to {target_url}")
            logger.debug(f"Content-Type: {request.content_type}")
            logger.debug(f"Has files: {bool(request.files)}")
            logger.debug(f"Form data: {request.form}")
            
            if request.is_json:
                logger.debug("Forwarding as JSON")
                resp = requests.post(target_url, json=request.get_json())
            elif request.files:
                logger.debug("Forwarding with files")
                files = {}
                for name, file_obj in request.files.items():
                    logger.debug(f"File: {name}, Filename: {file_obj.filename}")
                    if not file_obj.filename:
                        logger.warning(f"File object {name} has no filename, skipping")
                        continue
                        
                    # Get file content
                    content = file_obj.read()
                    logger.debug(f"Read {len(content)} bytes from file {file_obj.filename}")
                    
                    if len(content) == 0:
                        logger.warning(f"File {file_obj.filename} is empty (0 bytes)")
                    
                    content_type = file_obj.content_type or 'application/octet-stream'
                    logger.debug(f"Content type: {content_type}")
                    
                    # Add file to the files dictionary for requests
                    files[name] = (file_obj.filename, content, content_type)
                
                data = {}
                for key, value in request.form.items():
                    data[key] = value
                    logger.debug(f"Form data: {key}={value[:20] if isinstance(value, str) else value}")
                
                # Detailed logging for troubleshooting
                logger.debug(f"Sending {len(files)} files and {len(data)} form fields to {target_url}")
                for file_name, file_tuple in files.items():
                    file_info = file_tuple[0]  # Filename
                    file_size = len(file_tuple[1]) if file_tuple[1] else 0  # Content size
                    file_type = file_tuple[2]  # Content type
                    logger.debug(f"File details - Name: {file_name}, Filename: {file_info}, Size: {file_size} bytes, Type: {file_type}")
                
                try:
                    resp = requests.post(target_url, files=files, data=data)
                    logger.debug(f"POST response status: {resp.status_code}")
                    if resp.status_code != 200:
                        logger.error(f"Error response: {resp.text}")
                except Exception as e:
                    logger.error(f"Error sending request to FastAPI: {str(e)}")
                    raise
            elif request.form:
                logger.debug("Forwarding as form data")
                resp = requests.post(target_url, data=request.form)
            else:
                logger.debug("Forwarding as raw data")
                resp = requests.post(target_url, data=request.get_data(), 
                                     headers={'Content-Type': request.content_type})
        elif request.method == 'PUT':
            resp = requests.put(target_url, json=request.get_json())
        elif request.method == 'DELETE':
            resp = requests.delete(target_url)
        else:
            return jsonify({"error": "Method not supported"}), 405
        
        # Return the response
        return Response(
            resp.content,
            status=resp.status_code,
            content_type=resp.headers.get('Content-Type', 'text/html')
        )
    except requests.RequestException as e:
        logger.error(f"Error forwarding request: {str(e)}")
        return jsonify({"error": "Failed to connect to API server"}), 500