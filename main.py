# Import the Flask app for gunicorn compatibility
from flask_app import app

# For gunicorn, which looks for an 'app' variable in the main module
# This variable is specifically set for gunicorn
app = app

if __name__ == "__main__":
    # When running directly, you can use the FastAPI app for development
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)
