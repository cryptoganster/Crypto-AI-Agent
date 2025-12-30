"""Value object para TLDR (Too Long; Didn't Read)."""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class TLDR:
    """
    Value object para TLDR (Too Long; Didn't Read).

    Representa un resumen ultra-conciso en bullets.
    """

    bullets: List[str]  # 3-5 bullets

    def __post_init__(self):
        """Valida TLDR."""
        if len(self.bullets) < 3 or len(self.bullets) > 5:
            raise ValueError(f"TLDR must have 3-5 bullets, got {len(self.bullets)}")

        for bullet in self.bullets:
            if not bullet or len(bullet) < 10:
                raise ValueError("Each bullet must be at least 10 characters")

    @property
    def content(self) -> str:
        """Retorna TLDR formateado."""
        return "\n".join(f"- {bullet}" for bullet in self.bullets)
