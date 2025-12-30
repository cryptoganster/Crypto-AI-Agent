"""Middleware setup."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.shared.api.middleware import error_handler_middleware, logging_middleware


def setup_middleware(app: FastAPI) -> None:
    """
    Configure application middleware.

    Args:
        app: FastAPI application instance
    """
    # CORS Middleware
    cors_origins = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:8501,http://127.0.0.1:8501,http://localhost:3000",
    ).split(",")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom Middleware
    app.middleware("http")(logging_middleware)
    app.middleware("http")(error_handler_middleware)
