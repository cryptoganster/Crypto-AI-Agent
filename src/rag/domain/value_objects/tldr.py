"""Value Object para TLDR (Too Long; Didn't Read) de un artículo."""

from dataclasses import dataclass
from typing import List

# Constantes para validación
MIN_BULLETS = 3
"""Número mínimo de bullets en un TLDR."""

MAX_BULLETS = 5
"""Número máximo de bullets en un TLDR."""

MIN_BULLET_LENGTH = 10
"""Longitud mínima de cada bullet."""

MAX_BULLET_LENGTH = 500
"""Longitud máxima de cada bullet."""


@dataclass(frozen=True)
class TLDR:
    """
    Value Object para TLDR (Too Long; Didn't Read).

    Representa un resumen ultra-conciso en formato de bullets (3-5 puntos)
    que captura la información más crítica de un artículo. Debe incluir:
    - Qué pasó (evento principal)
    - Impacto en el mercado cripto
    - Tokens afectados
    - Actores involucrados
    - Riesgos regulatorios o técnicos

    Attributes:
        bullets: Lista de bullets (3-5 elementos)

    Examples:
        >>> tldr = TLDR(bullets=[
        ...     "Bitcoin ETF aprobado por SEC",
        ...     "Impacto positivo en precio: +15% en 24h",
        ...     "Tokens afectados: BTC, ETH",
        ...     "BlackRock y Fidelity lideran solicitudes",
        ...     "Riesgo: Posible volatilidad a corto plazo"
        ... ])
        >>> tldr.bullet_count
        5
        >>> tldr.is_valid()
        True
    """

    bullets: List[str]

    def __post_init__(self):
        """Valida que el TLDR sea válido."""
        # Validar que bullets sea una lista
        if not isinstance(self.bullets, (list, tuple)):
            raise TypeError(
                f"Bullets debe ser lista o tupla, recibido: {type(self.bullets)}"
            )

        # Validar número de bullets
        bullet_count = len(self.bullets)
        if not MIN_BULLETS <= bullet_count <= MAX_BULLETS:
            raise ValueError(
                f"TLDR debe tener entre {MIN_BULLETS} y {MAX_BULLETS} bullets, "
                f"recibido: {bullet_count}"
            )

        # Validar cada bullet
        for i, bullet in enumerate(self.bullets):
            if not isinstance(bullet, str):
                raise TypeError(f"Bullet {i} debe ser string, recibido: {type(bullet)}")

            if not bullet or not bullet.strip():
                raise ValueError(f"Bullet {i} no puede estar vacío")

            bullet_length = len(bullet.strip())
            if bullet_length < MIN_BULLET_LENGTH:
                raise ValueError(
                    f"Bullet {i} muy corto: {bullet_length} caracteres, "
                    f"mínimo: {MIN_BULLET_LENGTH}"
                )

            if bullet_length > MAX_BULLET_LENGTH:
                raise ValueError(
                    f"Bullet {i} muy largo: {bullet_length} caracteres, "
                    f"máximo: {MAX_BULLET_LENGTH}"
                )

    @property
    def bullet_count(self) -> int:
        """
        Obtiene el número de bullets.

        Returns:
            Número de bullets
        """
        return len(self.bullets)

    @property
    def content(self) -> str:
        """
        Obtiene el TLDR formateado como string con bullets.

        Returns:
            TLDR formateado con "- " al inicio de cada bullet

        Examples:
            >>> tldr = TLDR(bullets=["Punto 1", "Punto 2", "Punto 3"])
            >>> print(tldr.content)
            - Punto 1
            - Punto 2
            - Punto 3
        """
        return "\n".join(f"- {bullet.strip()}" for bullet in self.bullets)

    def get_total_length(self) -> int:
        """
        Obtiene la longitud total del TLDR (suma de todos los bullets).

        Returns:
            Longitud total en caracteres
        """
        return sum(len(bullet) for bullet in self.bullets)

    def get_average_bullet_length(self) -> float:
        """
        Obtiene la longitud promedio de los bullets.

        Returns:
            Longitud promedio en caracteres
        """
        return self.get_total_length() / self.bullet_count

    def is_valid(self) -> bool:
        """
        Verifica si el TLDR es válido.

        Returns:
            True si cumple todas las validaciones
        """
        try:
            # Las validaciones ya se hacen en __post_init__
            # Este método es útil para verificaciones adicionales
            return MIN_BULLETS <= self.bullet_count <= MAX_BULLETS and all(
                MIN_BULLET_LENGTH <= len(b) <= MAX_BULLET_LENGTH for b in self.bullets
            )
        except Exception:
            return False

    def is_concise(self) -> bool:
        """
        Verifica si el TLDR es conciso (longitud total < 1000 caracteres).

        Returns:
            True si es conciso
        """
        return self.get_total_length() < 1000

    def contains_keywords(self, keywords: List[str]) -> bool:
        """
        Verifica si el TLDR contiene alguna de las keywords.

        Args:
            keywords: Lista de keywords a buscar (case-insensitive)

        Returns:
            True si contiene al menos una keyword

        Examples:
            >>> tldr = TLDR(bullets=["Bitcoin alcanzó $50,000"])
            >>> tldr.contains_keywords(["bitcoin", "ethereum"])
            True
        """
        content_lower = self.content.lower()
        return any(keyword.lower() in content_lower for keyword in keywords)

    def get_bullet(self, index: int) -> str:
        """
        Obtiene un bullet específico por índice.

        Args:
            index: Índice del bullet (0-based)

        Returns:
            Bullet en el índice especificado

        Raises:
            IndexError: Si el índice está fuera de rango
        """
        return self.bullets[index]

    def to_dict(self) -> dict:
        """
        Convierte el TLDR a diccionario para serialización.

        Returns:
            Diccionario con los bullets

        Examples:
            >>> tldr = TLDR(bullets=["A", "B", "C"])
            >>> tldr.to_dict()
            {'bullets': ['A', 'B', 'C'], 'count': 3}
        """
        return {"bullets": list(self.bullets), "count": self.bullet_count}

    @classmethod
    def from_dict(cls, data: dict) -> "TLDR":
        """
        Crea TLDR desde un diccionario.

        Args:
            data: Diccionario con key 'bullets'

        Returns:
            TLDR

        Raises:
            ValueError: Si el diccionario no tiene la estructura correcta
        """
        if not isinstance(data, dict):
            raise TypeError(f"Data debe ser dict, recibido: {type(data)}")

        if "bullets" not in data:
            raise ValueError("Data debe contener key 'bullets'")

        return cls(bullets=data["bullets"])

    @classmethod
    def from_text(cls, text: str, separator: str = "\n") -> "TLDR":
        """
        Crea TLDR desde texto con bullets separados.

        Args:
            text: Texto con bullets (uno por línea o separados por separator)
            separator: Separador de bullets (default: newline)

        Returns:
            TLDR

        Examples:
            >>> text = "- Punto 1\\n- Punto 2\\n- Punto 3"
            >>> tldr = TLDR.from_text(text)
            >>> tldr.bullet_count
            3
        """
        if not text or not text.strip():
            raise ValueError("Text no puede estar vacío")

        # Dividir por separator y limpiar
        lines = text.split(separator)

        # Limpiar bullets (remover "- ", "* ", números, etc.)
        bullets = []
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Remover prefijos comunes de bullets
            for prefix in ["- ", "* ", "• ", "→ "]:
                if line.startswith(prefix):
                    line = line[len(prefix) :].strip()
                    break

            # Remover numeración (ej: "1. ", "2) ")
            if line and line[0].isdigit():
                # Buscar el primer espacio después del número
                space_idx = line.find(" ")
                if space_idx > 0:
                    line = line[space_idx + 1 :].strip()

            if line:
                bullets.append(line)

        return cls(bullets=bullets)

    def __str__(self) -> str:
        """Representación en string del TLDR."""
        return self.content

    def __repr__(self) -> str:
        """Representación para debugging."""
        preview = (
            self.bullets[0][:50] + "..."
            if len(self.bullets[0]) > 50
            else self.bullets[0]
        )
        return (
            f"TLDR(bullets={self.bullet_count}, "
            f"total_length={self.get_total_length()}, "
            f"first='{preview}')"
        )

    def __len__(self) -> int:
        """Permite usar len() en TLDR (retorna número de bullets)."""
        return self.bullet_count

    def __iter__(self):
        """Permite iterar sobre los bullets."""
        return iter(self.bullets)

    def __getitem__(self, index: int) -> str:
        """Permite acceso por índice a los bullets."""
        return self.bullets[index]
