"""ScrapingState Value Object - Estado de errores y cancelación."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.scraping.domain.value_objects.error import ScrapingError


@dataclass(frozen=True)
class ScrapingState:
    """
    Estado de errores y cancelación de Scraping.

    Mantiene información sobre:
    - Razón de cancelación (si aplica)
    - Lista de errores ocurridos durante el scraping

    Este VO es inmutable. Cada cambio retorna una nueva instancia.
    """

    cancelled_reason: Optional[str] = None
    errors: List[ScrapingError] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Valida el estado."""
        if self.cancelled_reason is not None and not self.cancelled_reason.strip():
            raise ValueError("cancelled_reason no puede estar vacío si se proporciona")

    @classmethod
    def create_new(cls) -> "ScrapingState":
        """
        Crea estado para una nueva sesión.

        Returns:
            ScrapingState sin errores ni cancelación
        """
        return cls(
            cancelled_reason=None,
            errors=[],
        )

    def with_error(self, error: ScrapingError) -> "ScrapingState":
        """
        Agrega un error al estado.

        Args:
            error: ScrapingError a agregar

        Returns:
            Nueva ScrapingState con el error agregado
        """
        if not isinstance(error, ScrapingError):
            raise ValueError("error debe ser un ScrapingError")

        new_errors = list(self.errors)
        new_errors.append(error)

        return ScrapingState(
            cancelled_reason=self.cancelled_reason,
            errors=new_errors,
        )

    def with_cancellation(self, reason: str) -> "ScrapingState":
        """
        Marca el estado como cancelado.

        Args:
            reason: Razón de la cancelación

        Returns:
            Nueva ScrapingState marcada como cancelada

        Raises:
            ValueError: Si ya está cancelada o reason está vacío
        """
        if not reason or not reason.strip():
            raise ValueError("reason no puede estar vacío")

        if self.is_cancelled():
            raise ValueError("La sesión ya está cancelada")

        return ScrapingState(
            cancelled_reason=reason,
            errors=self.errors,
        )

    def is_cancelled(self) -> bool:
        """
        Verifica si la sesión está cancelada.

        Returns:
            True si cancelled_reason no es None
        """
        return self.cancelled_reason is not None

    def has_errors(self) -> bool:
        """
        Verifica si hay errores registrados.

        Returns:
            True si hay al menos un error
        """
        return len(self.errors) > 0

    def get_error_count(self) -> int:
        """
        Obtiene el número total de errores.

        Returns:
            Cantidad de errores
        """
        return len(self.errors)

    def get_errors_by_type(self) -> Dict[str, List[ScrapingError]]:
        """
        Agrupa errores por tipo.

        Returns:
            Diccionario con errores agrupados por error_type
        """
        errors_by_type: Dict[str, List[ScrapingError]] = {}

        for error in self.errors:
            if error.error_type not in errors_by_type:
                errors_by_type[error.error_type] = []
            errors_by_type[error.error_type].append(error)

        return errors_by_type

    def get_recoverable_errors(self) -> List[ScrapingError]:
        """
        Obtiene lista de errores recuperables.

        Returns:
            Lista de ScrapingErrors donde is_recoverable=True
        """
        return [e for e in self.errors if e.is_recoverable]

    def get_non_recoverable_errors(self) -> List[ScrapingError]:
        """
        Obtiene lista de errores no recuperables.

        Returns:
            Lista de ScrapingErrors donde is_recoverable=False
        """
        return [e for e in self.errors if not e.is_recoverable]

    def has_non_recoverable_errors(self) -> bool:
        """
        Verifica si hay errores no recuperables.

        Returns:
            True si hay al menos un error no recuperable
        """
        return any(not e.is_recoverable for e in self.errors)

    def __str__(self) -> str:
        """Representación string."""
        if self.is_cancelled():
            return f"ScrapingState(cancelled: {self.cancelled_reason})"

        if self.has_errors():
            return f"ScrapingState({len(self.errors)} errors)"

        return "ScrapingState(ok)"
