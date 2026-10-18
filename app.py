"""
DOC-OC v6 — Server Entry Point

Run with:
    python app.py
"""

import os
import uvicorn
from api.app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting DOC-OC v2 API on http://0.0.0.0:{port}")
    print(f"📖 Interactive Swagger Docs: http://localhost:{port}/docs")
    uvicorn.run("api.app:app", host="0.0.0.0", port=port, reload=False)
