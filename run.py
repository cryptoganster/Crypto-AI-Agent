#!/usr/bin/env python
"""Script de inicio para el servicio."""
import sys
from pathlib import Path

# Agregar el directorio raíz al PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    import os
    import uvicorn
    from dotenv import load_dotenv
    
    load_dotenv()
    
    uvicorn.run(
        "src.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8888")),
        reload=os.getenv("API_RELOAD", "true").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
