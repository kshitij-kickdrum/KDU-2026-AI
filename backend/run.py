"""
Simple script to run the FastAPI server.

Usage:
    python run.py

This will start the server on http://localhost:8000
You can then:
- View API docs at http://localhost:8000/docs
- Test endpoints using the interactive docs
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload on code changes
    )
