"""Excepciones para ActivateSource command."""


class ActivateSourceError(Exception):
    """Error base para ActivateSource command."""

    pass


class SourceNotFoundError(ActivateSourceError):
    """Error cuando la fuente RSS no existe."""

    def __init__(self, source_id: str):
        self.source_id = source_id
        super().__init__(f"Fuente RSS con ID {source_id} no encontrada")


class SourceAlreadyActiveError(ActivateSourceError):
    """Error cuando la fuente RSS ya está activa."""

    def __init__(self, source_id: str):
        self.source_id = source_id
        super().__init__(f"Fuente RSS {source_id} ya está activa")


class ConnectionTestFailedError(ActivateSourceError):
    """Error cuando el test de conexión falla."""

    def __init__(self, source_id: str, connection_error: str):
        self.source_id = source_id
        self.connection_error = connection_error
        super().__init__(
            f"Test de conexión falló para fuente {source_id}: {connection_error}"
        )


class SourceHealthCheckError(ActivateSourceError):
    """Error durante verificación de salud de la fuente."""

    def __init__(self, source_id: str, health_error: str):
        self.source_id = source_id
        self.health_error = health_error
        super().__init__(
            f"Error verificando salud de fuente {source_id}: {health_error}"
        )


class SourceHealthCheckFailedError(ActivateSourceError):
    """Error cuando el health check de la fuente falla."""

    def __init__(self, source_id: str, health_error: str):
        self.source_id = source_id
        self.health_error = health_error
        super().__init__(f"Health check falló para fuente {source_id}: {health_error}")


class SourceActivationError(ActivateSourceError):
    """Error durante el proceso de activación de la fuente."""

    def __init__(self, source_id: str, activation_error: str):
        self.source_id = source_id
        self.activation_error = activation_error
        super().__init__(f"Error activando fuente {source_id}: {activation_error}")
