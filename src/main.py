"""FastAPI application entry point - Clean and minimal."""

import os

from dotenv import load_dotenv

from src.bootstrap.app_factory import create_app
from src.bootstrap.lifespan import AppContainer, get_container

# Load environment variables
load_dotenv()

# Create FastAPI app
app = create_app()

# Export for external use
__all__ = ["app", "get_container", "AppContainer"]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("API_RELOAD", "true").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
