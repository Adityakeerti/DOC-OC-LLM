"""
DOC-OC v6 — Server Entry Point

Run with:
    python app.py
"""

import uvicorn
from api.app import app

if __name__ == "__main__":
    print("🚀 Starting DOC-OC v6 API on http://localhost:8000")
    print("📖 Interactive Swagger Docs: http://localhost:8000/docs")
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=True)
