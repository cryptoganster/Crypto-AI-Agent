"""Excepciones específicas para UpdateSource command."""


class UpdateSourceError(Exception):
    """Excepción base para errores de UpdateSource."""

    pass


class SourceNotFoundError(UpdateSourceError):
    """Source no encontrado."""

    pass


class InvalidSourceUpdateError(UpdateSourceError):
    """Actualización de source inválida."""

    pass


class SourceConfigurationError(UpdateSourceError):
    """Error en configuración de source."""

    pass
