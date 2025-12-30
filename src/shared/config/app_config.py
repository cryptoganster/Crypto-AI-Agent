"""Application configuration."""

import os
from dataclasses import dataclass, field

from src.shared.config.ai_processing_config import AIProcessingConfig
from src.shared.config.chunking_config import ChunkingConfig
from src.shared.config.database_config import DatabaseConfig
from src.shared.config.logging_config import LoggingConfig
from src.shared.config.rss_config import RssConfig


@dataclass
class AppConfig:
    """Configuración principal de la aplicación."""

    app_name: str = "Feeds AI"
    version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    environment: str = "development"

    database: DatabaseConfig = field(default_factory=lambda: DatabaseConfig.from_env())
    logging: LoggingConfig = field(default_factory=lambda: LoggingConfig.from_env())
    rss: RssConfig = field(default_factory=lambda: RssConfig.from_env())
    chunking: ChunkingConfig = field(default_factory=lambda: ChunkingConfig.from_env())
    ai_processing: AIProcessingConfig = field(
        default_factory=lambda: AIProcessingConfig.from_env()
    )

    scheduler_database_url: str = field(default="")

    # Redis configuration
    redis_url: str = field(default="")
    scheduler_use_redis: bool = field(default=False)

    def __post_init__(self):
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.scheduler_database_url = os.getenv(
            "SCHEDULER_DATABASE_URL",
            self.database.sync_connection_string,
        )

        # Redis configuration
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6380/0")
        self.scheduler_use_redis = (
            os.getenv("SCHEDULER_USE_REDIS", "false").lower() == "true"
        )

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"
