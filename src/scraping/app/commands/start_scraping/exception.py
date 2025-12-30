"""Excepciones para StartScrapingCommand."""


class StartScrapingError(Exception):
    """Excepción base para errores de StartScraping."""

    pass


class StartScrapingValidationError(StartScrapingError):
    """Excepción cuando la validación falla."""

    pass


class NoSourcesAvailableError(StartScrapingError):
    """Excepción cuando no hay sources disponibles."""

    def __init__(self):
        super().__init__("No hay sources disponibles para scraping")


class ScrapingSessionCreationError(StartScrapingError):
    """Excepción cuando falla la creación de la sesión."""

    def __init__(self, message: str):
        super().__init__(f"Error creando sesión de scraping: {message}")
