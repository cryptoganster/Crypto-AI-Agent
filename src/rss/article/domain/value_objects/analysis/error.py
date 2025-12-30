"""Value Object para información de errores del artículo."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class RssArticleError:
    """
    Value Object para información de errores.

    Encapsula el estado de error de un artículo, incluyendo tipo de error,
    mensaje, quién lo marcó y cuándo.

    Invariantes:
    - Si has_error es True, error_type, error_message y error_marked_by deben ser no vacíos
    - Los campos son inmutables (frozen dataclass)

    Attributes:
        has_error: Indica si el artículo tiene un error
        error_type: Tipo de error (ej: "validation_error", "processing_error")
        error_message: Mensaje descriptivo del error
        error_marked_by: Identificador de quién marcó el error (usuario, sistema, servicio)
        error_marked_at: Timestamp de cuándo se marcó el error
    """

    has_error: bool = False
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    error_marked_by: Optional[str] = None
    error_marked_at: Optional[datetime] = None

    def __post_init__(self):
        """
        Valida consistencia: si has_error es True, campos requeridos deben estar presentes.

        Raises:
            ValueError: Si has_error es True pero faltan campos requeridos o están vacíos
        """
        if self.has_error:
            if not self.error_type or not self.error_type.strip():
                raise ValueError(
                    "error_type es requerido cuando has_error es True. "
                    "Debe ser una cadena no vacía."
                )

            if not self.error_message or not self.error_message.strip():
                raise ValueError(
                    "error_message es requerido cuando has_error es True. "
                    "Debe ser una cadena no vacía."
                )

            if not self.error_marked_by or not self.error_marked_by.strip():
                raise ValueError(
                    "error_marked_by es requerido cuando has_error es True. "
                    "Debe ser una cadena no vacía."
                )

    @staticmethod
    def no_error() -> "RssArticleError":
        """
        Crea instancia sin error.

        Factory method para crear RssArticleError indicando que el artículo
        no tiene errores.

        Returns:
            RssArticleError con has_error=False y todos los campos de error None

        Example:
            >>> error = RssArticleError.no_error()
            >>> error.has_error
            False
            >>> error.error_type is None
            True
            >>> error.error_message is None
            True
        """
        return RssArticleError(has_error=False)

    @staticmethod
    def create_error(
        error_type: str,
        error_message: str,
        marked_by: str,
        marked_at: Optional[datetime] = None,
    ) -> "RssArticleError":
        """
        Factory method para crear error.

        Crea RssArticleError con todos los campos de error establecidos.
        Si marked_at no se proporciona, usa el timestamp actual UTC.

        Args:
            error_type: Tipo de error (no vacío)
            error_message: Mensaje descriptivo del error (no vacío)
            marked_by: Identificador de quién marcó el error (no vacío)
            marked_at: Timestamp del error (opcional, por defecto ahora UTC)

        Returns:
            RssArticleError con has_error=True y todos los campos establecidos

        Raises:
            ValueError: Si algún campo requerido es None o vacío

        Example:
            >>> error = RssArticleError.create_error(
            ...     error_type="validation_error",
            ...     error_message="Contenido inválido",
            ...     marked_by="validation_service"
            ... )
            >>> error.has_error
            True
            >>> error.error_type
            'validation_error'
        """
        # Validar que los campos no sean None o vacíos antes de crear
        if not error_type or not error_type.strip():
            raise ValueError("error_type no puede ser None o vacío")

        if not error_message or not error_message.strip():
            raise ValueError("error_message no puede ser None o vacío")

        if not marked_by or not marked_by.strip():
            raise ValueError("marked_by no puede ser None o vacío")

        # Usar timestamp actual si no se proporciona
        if marked_at is None:
            marked_at = datetime.now(timezone.utc)

        return RssArticleError(
            has_error=True,
            error_type=error_type,
            error_message=error_message,
            error_marked_by=marked_by,
            error_marked_at=marked_at,
        )

    @property
    def is_valid(self) -> bool:
        """
        Verifica si el artículo es válido (sin errores).

        Returns:
            True si has_error es False
        """
        return not self.has_error

    @property
    def has_timestamp(self) -> bool:
        """
        Verifica si tiene timestamp del error.

        Returns:
            True si error_marked_at no es None
        """
        return self.error_marked_at is not None

    def clear_error(self) -> "RssArticleError":
        """
        Retorna nueva instancia sin error.

        Útil para limpiar el estado de error de un artículo.

        Returns:
            Nueva instancia de RssArticleError con has_error=False

        Example:
            >>> error = RssArticleError.create_error(
            ...     error_type="test_error",
            ...     error_message="Test",
            ...     marked_by="test"
            ... )
            >>> cleared = error.clear_error()
            >>> cleared.has_error
            False
            >>> cleared.error_type is None
            True
        """
        return RssArticleError.no_error()

    def update_error(
        self,
        error_type: str,
        error_message: str,
        marked_by: str,
        marked_at: Optional[datetime] = None,
    ) -> "RssArticleError":
        """
        Retorna nueva instancia con error actualizado.

        Args:
            error_type: Nuevo tipo de error
            error_message: Nuevo mensaje de error
            marked_by: Quién marca el nuevo error
            marked_at: Timestamp del nuevo error (opcional)

        Returns:
            Nueva instancia de RssArticleError con error actualizado

        Raises:
            ValueError: Si algún campo requerido es None o vacío
        """
        return RssArticleError.create_error(
            error_type=error_type,
            error_message=error_message,
            marked_by=marked_by,
            marked_at=marked_at,
        )

    def get_error_summary(self) -> Optional[str]:
        """
        Obtiene resumen del error en formato legible.

        Returns:
            String con resumen del error, o None si no hay error

        Example:
            >>> error = RssArticleError.create_error(
            ...     error_type="validation_error",
            ...     error_message="Contenido inválido",
            ...     marked_by="validator"
            ... )
            >>> summary = error.get_error_summary()
            >>> "validation_error" in summary
            True
        """
        if not self.has_error:
            return None

        return f"[{self.error_type}] {self.error_message} (marcado por: {self.error_marked_by})"


# Alias para compatibilidad
ArticleError = RssArticleError
