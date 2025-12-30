"""Value Object para score de relevancia de keyword."""

from dataclasses import dataclass

from src.shared.domain.value_objects.score import Score


@dataclass(frozen=True)
class KeywordScore:
    """
    Score normalizado de relevancia de keyword.

    Value Object inmutable que representa la relevancia de una keyword
    extraída de un artículo, con score normalizado entre 0.0-1.0.

    Específico del bounded context de Article para análisis de contenido.

    Note:
        No hereda de Score porque tiene campos adicionales (keyword, frequency).
        Usa Score internamente para validación del score.
    """

    keyword: str
    score: float  # 0.0-1.0 normalizado, validado por Score
    frequency: int

    def __post_init__(self):
        if not self.keyword or not self.keyword.strip():
            raise ValueError("keyword no puede estar vacío")

        # Usar Score para validar el score (reutiliza validación centralizada)
        try:
            Score(value=self.score)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Score inválido: {e}")

        if self.frequency < 1:
            raise ValueError(f"Frequency debe ser >= 1, recibido: {self.frequency}")

    def meets_threshold(self, min_score: float) -> bool:
        """Verifica si cumple umbral mínimo de relevancia."""
        return self.score >= min_score

    def is_highly_relevant(self) -> bool:
        """Keywords con score > 0.7 son altamente relevantes."""
        return self.score > 0.7

    def is_moderately_relevant(self) -> bool:
        """Keywords con score entre 0.4-0.7 son moderadamente relevantes."""
        return 0.4 <= self.score <= 0.7

    def is_low_relevance(self) -> bool:
        """Keywords con score < 0.4 tienen baja relevancia."""
        return self.score < 0.4

    def get_relevance_category(self) -> str:
        """Retorna categoría de relevancia como string."""
        if self.is_highly_relevant():
            return "high"
        elif self.is_moderately_relevant():
            return "moderate"
        else:
            return "low"

    @classmethod
    def from_frequency(
        cls, keyword: str, frequency: int, max_frequency: int
    ) -> "KeywordScore":
        """
        Factory method para crear score normalizado desde frecuencia.

        Args:
            keyword: Palabra clave
            frequency: Frecuencia de aparición
            max_frequency: Frecuencia máxima en el conjunto

        Returns:
            KeywordScore con score normalizado
        """
        if max_frequency == 0:
            raise ValueError("max_frequency no puede ser 0")

        score = frequency / max_frequency
        return cls(keyword=keyword, score=score, frequency=frequency)

    def __str__(self) -> str:
        return f"{self.keyword} (score={self.score:.2f}, freq={self.frequency})"

    def __repr__(self) -> str:
        return f"KeywordScore(keyword='{self.keyword}', score={self.score:.2f}, frequency={self.frequency})"
