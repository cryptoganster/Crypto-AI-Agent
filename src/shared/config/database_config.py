"""Database configuration."""

import os
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Configuración de base de datos."""

    host: str = "localhost"
    port: int = 5432
    database: str = "feeds_ai"
    username: str = "postgres"
    password: str = ""
    schema: str = "public"

    @property
    def connection_string(self) -> str:
        """URL de conexión PostgreSQL async."""
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def sync_connection_string(self) -> str:
        """URL de conexión PostgreSQL síncrona (para APScheduler)."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Crea configuración desde variables de entorno."""
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "feeds_ai"),
            username=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            schema=os.getenv("DB_SCHEMA", "public"),
        )
