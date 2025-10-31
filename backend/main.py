import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Import from backend.api when running as module, or api when running from backend dir
try:
    from backend.api import chat, calendly_integration
except ImportError:
    try:
        from api import chat, calendly_integration
    except ImportError:
        # Last resort: add parent to path
        import sys
        from pathlib import Path
        backend_dir = Path(__file__).parent
        project_root = backend_dir.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        from backend.api import chat, calendly_integration

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Appointment Scheduling Agent API",
    description="Conversational agent for appointment scheduling and FAQ answering",
    version="1.0.0"
)

# Configure CORS - allow all localhost ports (Vite may use different ports)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default port
        "http://localhost:5174",  # Vite fallback port
        "http://localhost:5175",  # Vite fallback port
        "http://localhost:3000",  # Alternative React port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(calendly_integration.router, prefix="/api/calendly", tags=["calendly"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Appointment Scheduling Agent API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
