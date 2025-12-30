"""SourceStatus Value Object - Estado de una fuente RSS individual."""

from dataclasses import dataclass
from typing import Any, Dict, Set

from src.shared.kernel import IValueObject

# Constantes de estado fuera del dataclass
ACTIVE = "active"
INACTIVE = "inactive"
SUSPENDED = "suspended"
ERROR = "error"

# Estados que permiten transiciones válidas
VALID_STATES = frozenset({ACTIVE, INACTIVE, SUSPENDED, ERROR})

# Matriz de transiciones válidas
VALID_TRANSITIONS = {
    INACTIVE: {ACTIVE, ERROR},  # Inactivo → Activo o Error
    ACTIVE: {
        INACTIVE,
        SUSPENDED,
        ERROR,
    },  # Activo → Inactivo, Suspendido o Error
    SUSPENDED: {
        ACTIVE,
        INACTIVE,
        ERROR,
    },  # Suspendido → Activo, Inactivo o Error
    ERROR: {INACTIVE},  # Error → Solo Inactivo (requiere intervención manual)
}


@dataclass(frozen=True)
class RssFeedStatus(IValueObject):
    """
    Value Object para el estado de un RssFeed aggregate.

    Estados válidos para fuentes RSS individuales:
    - ACTIVE: Fuente activa y programada para fetch
    - INACTIVE: Fuente desactivada por el usuario
    - SUSPENDED: Fuente suspendida por errores consecutivos
    - ERROR: Fuente en estado de error permanente
    """

    value: str

    def __post_init__(self):
        """Valida que el estado sea válido."""
        if self.value not in VALID_STATES:
            raise ValueError(
                f"Estado inválido: {self.value}. Estados válidos: {', '.join(VALID_STATES)}"
            )

    @classmethod
    def active(cls) -> "RssFeedStatus":
        """Crea estado activo."""
        return cls(value=ACTIVE)

    @classmethod
    def inactive(cls) -> "RssFeedStatus":
        """Crea estado inactivo."""
        return cls(value=INACTIVE)

    @classmethod
    def suspended(cls) -> "RssFeedStatus":
        """Crea estado suspendido."""
        return cls(value=SUSPENDED)

    @classmethod
    def error(cls) -> "RssFeedStatus":
        """Crea estado de error."""
        return cls(value=ERROR)

    def is_active(self) -> bool:
        """Verifica si está activo."""
        return self.value == ACTIVE

    def is_inactive(self) -> bool:
        """Verifica si está inactivo."""
        return self.value == INACTIVE

    def is_suspended(self) -> bool:
        """Verifica si está suspendido."""
        return self.value == SUSPENDED

    def is_error(self) -> bool:
        """Verifica si está en error."""
        return self.value == ERROR

    def can_transition_to(self, target_status: "RssFeedStatus") -> bool:
        """
        Verifica si es válida la transición al estado objetivo.

        Args:
            target_status: Estado objetivo

        Returns:
            True si la transición es válida según las reglas de negocio
        """
        if not isinstance(target_status, RssFeedStatus):
            return False

        valid_targets = VALID_TRANSITIONS.get(self.value, set())
        return target_status.value in valid_targets

    def get_valid_transitions(self) -> Set[str]:
        """
        Obtiene los estados válidos a los que puede transicionar.

        Returns:
            Set de estados válidos para transición
        """
        return VALID_TRANSITIONS.get(self.value, set()).copy()

    def requires_manual_intervention(self) -> bool:
        """
        Determina si el estado requiere intervención manual.

        Returns:
            True para estados ERROR que requieren acción del usuario
        """
        return self.is_error()

    def can_fetch(self) -> bool:
        """
        Determina si el source puede realizar fetch operations.

        Returns:
            True si está en estado ACTIVE
        """
        return self.is_active()

    def is_operational(self) -> bool:
        """
        Determina si el source está en estado operacional.

        Returns:
            True si puede participar en operaciones normales (ACTIVE o INACTIVE)
        """
        return self.is_active() or self.is_inactive()

    def get_display_name(self) -> str:
        """
        Obtiene nombre legible para UI.

        Returns:
            Nombre en español para mostrar en interfaces
        """
        display_names = {
            ACTIVE: "Activo",
            INACTIVE: "Inactivo",
            SUSPENDED: "Suspendido",
            ERROR: "Error",
        }
        return display_names.get(self.value, self.value)

    def get_css_class(self) -> str:
        """
        Obtiene clase CSS para representación visual.

        Returns:
            Nombre de clase CSS apropiada para el estado
        """
        css_classes = {
            ACTIVE: "status-active",
            INACTIVE: "status-inactive",
            SUSPENDED: "status-suspended",
            ERROR: "status-error",
        }
        return css_classes.get(self.value, "status-unknown")

    def to_dict(self) -> Dict[str, Any]:
        """Serializa el estado a diccionario."""
        return {
            "value": self.value,
            "display_name": self.get_display_name(),
            "can_fetch": self.can_fetch(),
            "requires_manual_intervention": self.requires_manual_intervention(),
            "is_operational": self.is_operational(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RssFeedStatus":
        """Crea instancia desde diccionario."""
        return cls(value=data["value"])

    @classmethod
    def from_string(cls, status_string: str) -> "RssFeedStatus":
        """
        Crea RssFeedStatus desde string.

        Args:
            status_string: String del estado

        Returns:
            RssFeedStatus correspondiente

        Raises:
            ValueError: Si el string no es un estado válido
        """
        normalized = status_string.lower().strip()
        return cls(value=normalized)

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RssFeedStatus):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)


# Alias para compatibilidad hacia atrás
SourceStatus = RssFeedStatus
