"""Value Object para información de validación de artículos."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from src.shared.domain.value_objects.score import Score


@dataclass(frozen=True)
class ValidationInfo:
    """
    Value Object que consolida información de validación de un artículo.

    Agrupa score de validación, quién validó y cuándo, en un único objeto inmutable.

    Note:
        Usa Score VO para el campo score, eliminando validación duplicada.
        Proporciona property score_value para backward compatibility con código
        que espera float.
    """

    score: Score  # Score VO en lugar de float
    validated_by: str
    validated_at: datetime

    def __post_init__(self):
        """Valida los campos de validación."""
        # Score ya está validado por Score.__post_init__
        # Solo validar validated_by y validated_at

        # Validar validated_by
        if not isinstance(self.validated_by, str):
            raise TypeError("validated_by debe ser un string")

        if not self.validated_by or not self.validated_by.strip():
            raise ValueError("validated_by no puede estar vacío")

        # Validar validated_at
        if not isinstance(self.validated_at, datetime):
            raise TypeError("validated_at debe ser un datetime")

        # Asegurar que tiene timezone
        if self.validated_at.tzinfo is None:
            # Convertir a UTC si no tiene timezone
            object.__setattr__(
                self, "validated_at", self.validated_at.replace(tzinfo=timezone.utc)
            )

    @classmethod
    def create(
        cls, score: float, validated_by: str, validated_at: Optional[datetime] = None
    ) -> "ValidationInfo":
        """
        Factory method para crear ValidationInfo.

        Args:
            score: Score de validación (0.0-1.0) como float
            validated_by: Identificador de quien validó
            validated_at: Timestamp de validación (default: ahora en UTC)

        Returns:
            ValidationInfo creado

        Note:
            Acepta float para backward compatibility, lo convierte a Score internamente.
        """
        if validated_at is None:
            validated_at = datetime.now(timezone.utc)

        # Convertir float a Score VO
        score_vo = Score(value=score) if not isinstance(score, Score) else score

        return cls(score=score_vo, validated_by=validated_by, validated_at=validated_at)

    # Backward compatibility: property para acceder al score como float
    @property
    def score_value(self) -> float:
        """
        Retorna el score como float para backward compatibility.

        Returns:
            Score value como float
        """
        return self.score.value

    def is_high_quality(self) -> bool:
        """
        Determina si la validación indica alta calidad.

        Returns:
            True si score >= 0.7
        """
        return self.score.is_high()

    def is_low_quality(self) -> bool:
        """
        Determina si la validación indica baja calidad.

        Returns:
            True si score < 0.4
        """
        return self.score.is_low()

    def is_medium_quality(self) -> bool:
        """
        Determina si la validación indica calidad media.

        Returns:
            True si score está entre 0.4 y 0.7
        """
        return self.score.is_medium()

    def get_quality_level(self) -> str:
        """
        Obtiene el nivel de calidad como string.

        Returns:
            Nivel: "high", "medium", "low"
        """
        return self.score.level

    def is_recent(self, hours: int = 24) -> bool:
        """
        Verifica si la validación es reciente.

        Args:
            hours: Número de horas para considerar reciente

        Returns:
            True si la validación fue hace menos de 'hours' horas
        """
        now = datetime.now(timezone.utc)
        validated_at_utc = self.validated_at

        # Asegurar que ambos tienen timezone
        if validated_at_utc.tzinfo is None:
            validated_at_utc = validated_at_utc.replace(tzinfo=timezone.utc)

        time_diff = now - validated_at_utc
        return time_diff.total_seconds() < (hours * 3600)

    def was_validated_by(self, validator: str) -> bool:
        """
        Verifica si fue validado por un validador específico.

        Args:
            validator: Identificador del validador

        Returns:
            True si coincide con validated_by
        """
        return self.validated_by.lower() == validator.lower()

    def __str__(self) -> str:
        """Representación en string."""
        return f"Validated by {self.validated_by} with score {self.score.value:.2f}"

    def __repr__(self) -> str:
        """Representación para debugging."""
        return (
            f"ValidationInfo(score={self.score.value:.2f}, "
            f"validated_by='{self.validated_by}', "
            f"validated_at={self.validated_at.isoformat()}, "
            f"quality={self.get_quality_level()})"
        )
