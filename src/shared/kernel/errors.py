"""Excepciones base para el shared kernel."""


class KernelException(Exception):
    """
    Excepción base para errores del shared kernel.

    Todas las excepciones del kernel deben heredar de esta clase
    para facilitar el manejo de errores.
    """

    pass


class DomainException(KernelException):
    """
    Excepción base para errores de dominio.

    Representa violaciones de reglas de negocio o invariantes del dominio.
    Estas excepciones indican que la operación no puede completarse
    debido a restricciones del modelo de dominio.

    Características:
    - Nombradas según la regla de negocio violada
    - Contienen mensaje descriptivo del problema
    - Pueden incluir detalles adicionales
    - Se lanzan desde aggregates y domain services

    Example:
        >>> class InsufficientQualityException(DomainException):
        ...     def __init__(self, quality_score: float, minimum: float):
        ...         super().__init__(
        ...             f"Quality score {quality_score} is below minimum {minimum}"
        ...         )
        ...         self.quality_score = quality_score
        ...         self.minimum = minimum
        >>>
        >>> # En un aggregate
        >>> def publish(self):
        ...     if self.quality_score < 0.5:
        ...         raise InsufficientQualityException(self.quality_score, 0.5)
    """

    pass


class ValidationException(KernelException):
    """
    Excepción para errores de validación.

    Se lanza cuando los datos de entrada no cumplen con las reglas
    de validación. Puede contener múltiples errores de validación.

    Características:
    - Contiene lista de errores de validación
    - Cada error tiene campo y mensaje
    - Se lanza en command handlers o validators
    - Mapea a HTTP 400 o 422 en API

    Example:
        >>> errors = [
        ...     {"field": "title", "message": "Title is required"},
        ...     {"field": "url", "message": "Invalid URL format"}
        ... ]
        >>> raise ValidationException("Validation failed", errors=errors)
    """

    def __init__(self, message: str, errors: list[dict] | None = None):
        """
        Inicializa la excepción de validación.

        Args:
            message: Mensaje general del error
            errors: Lista de errores de validación específicos
        """
        super().__init__(message)
        self.errors = errors or []


class NotFoundException(KernelException):
    """
    Excepción cuando un recurso no se encuentra.

    Se lanza cuando se intenta acceder a un aggregate o entidad
    que no existe en el sistema.

    Características:
    - Contiene tipo de recurso y ID
    - Mapea a HTTP 404 en API
    - Se lanza desde repositories o query handlers

    Example:
        >>> article = await repository.find_by_id("123")
        >>> if article is None:
        ...     raise NotFoundException("Article", "123")
    """

    def __init__(self, resource_type: str, resource_id: str):
        """
        Inicializa la excepción de recurso no encontrado.

        Args:
            resource_type: Tipo de recurso (Article, Source, etc.)
            resource_id: ID del recurso no encontrado
        """
        super().__init__(f"{resource_type} with ID '{resource_id}' not found")
        self.resource_type = resource_type
        self.resource_id = resource_id


class ConflictException(KernelException):
    """
    Excepción cuando hay un conflicto con el estado actual.

    Se lanza cuando una operación no puede completarse debido a
    un conflicto con el estado existente (ej: duplicados, versiones).

    Características:
    - Indica conflicto con estado existente
    - Mapea a HTTP 409 en API
    - Común en operaciones de creación con unicidad

    Example:
        >>> existing = await repository.find_by_url(article.url)
        >>> if existing:
        ...     raise ConflictException(
        ...         f"Article with URL '{article.url}' already exists"
        ...     )
    """

    pass


class InvalidOperationException(DomainException):
    """
    Excepción cuando una operación no es válida en el estado actual.

    Se lanza cuando se intenta ejecutar una operación que no está
    permitida dado el estado actual del aggregate.

    Características:
    - Indica violación de reglas de transición de estado
    - Se lanza desde métodos de aggregates
    - Contiene información del estado actual y operación intentada

    Example:
        >>> def publish(self):
        ...     if self.status != ArticleStatus.DRAFT:
        ...         raise InvalidOperationException(
        ...             f"Cannot publish article in {self.status} status"
        ...         )
        ...     self.status = ArticleStatus.PUBLISHED
    """

    pass


class HandlerNotFoundException(KernelException):
    """
    Excepción cuando no se encuentra un handler para un request.

    Se lanza desde el mediator cuando se intenta enviar un command
    o query sin handler registrado.

    Características:
    - Indica configuración incorrecta
    - Debe detectarse en startup/tests
    - No debería ocurrir en producción

    Example:
        >>> # En el mediator
        >>> handler = self._handlers.get(type(request))
        >>> if handler is None:
        ...     raise HandlerNotFoundException(
        ...         f"No handler registered for {type(request).__name__}"
        ...     )
    """

    def __init__(self, request_type: str):
        """
        Inicializa la excepción de handler no encontrado.

        Args:
            request_type: Tipo de request sin handler
        """
        super().__init__(f"No handler registered for {request_type}")
        self.request_type = request_type


class EventPublishException(KernelException):
    """
    Excepción cuando falla la publicación de un evento.

    Se lanza desde el event bus cuando no se puede publicar un evento.

    Características:
    - Indica fallo en infraestructura de eventos
    - Puede requerir retry
    - Debe loggearse para debugging

    Example:
        >>> try:
        ...     await self._message_queue.publish(event)
        ... except Exception as e:
        ...     raise EventPublishException(
        ...         f"Failed to publish {type(event).__name__}: {str(e)}"
        ...     ) from e
    """

    pass


class RepositoryException(KernelException):
    """
    Excepción base para errores de repositorio.

    Se lanza cuando hay errores en operaciones de persistencia.

    Características:
    - Indica fallo en capa de persistencia
    - Puede ser transient (retry) o permanent
    - Debe loggearse con detalles

    Example:
        >>> try:
        ...     await self._session.commit()
        ... except SQLAlchemyError as e:
        ...     raise RepositoryException(
        ...         f"Failed to save article: {str(e)}"
        ...     ) from e
    """

    pass


class ConcurrencyException(RepositoryException):
    """
    Excepción cuando hay conflicto de concurrencia.

    Se lanza cuando se detecta que el aggregate fue modificado
    por otra transacción (optimistic locking).

    Características:
    - Indica conflicto de versión
    - Requiere reload y retry
    - Común en sistemas con alta concurrencia

    Example:
        >>> if model.version != aggregate.version:
        ...     raise ConcurrencyException(
        ...         f"Article {aggregate.id} was modified by another transaction"
        ...     )
    """

    pass
