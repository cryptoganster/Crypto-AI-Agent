"""Excepciones para UpdateScrapingConfigCommand."""


class UpdateScrapingConfigError(Exception):
    """Excepción base para errores de UpdateScrapingConfig."""

    pass


class UpdateScrapingConfigValidationException(UpdateScrapingConfigError):
    """Excepción cuando la validación del comando falla."""

    pass


class ScrapingNotFoundError(UpdateScrapingConfigError):
    """Excepción cuando la sesión de scraping no existe."""

    def __init__(self, source_id: str):
        self.source_id = source_id
        super().__init__(
            f"No se encontró sesión de scraping para la fuente {source_id}"
        )


class InvalidScrapingConfigError(UpdateScrapingConfigError):
    """Excepción cuando la configuración de scraping es inválida."""

    pass
