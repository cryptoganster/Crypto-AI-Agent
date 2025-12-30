"""
Command para extraer keywords de un artículo RSS.
Sigue principios CQRS estrictos con DTO puro usando solo primitivos.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ExtractArticleKeywordsCommand:
    """
    Command para extraer keywords de un artículo - DTO puro CQRS.

    Usa solo primitivos para cumplir principio de separación Command/Query.
    Los Value Objects se construyen en el Handler desde estos primitivos.

    Event-Driven Architecture:
    - Recibe datos del evento ArticleSummaryGenerated
    - No requiere lectura del aggregate (CQRS puro)
    """

    article_id: str  # ArticleId como primitivo

    # Configuración de extracción
    max_keywords: int = 10  # Máximo de keywords a extraer
    min_keyword_score: float = 0.3  # Score mínimo para considerar keyword relevante
    include_ngrams: bool = True  # Incluir frases (bi-grams, tri-grams)
    language: str = "auto"  # Idioma: auto, es, en

    # Flags de persistencia
    save_to_article: bool = True  # Guardar keywords en el agregado Article
    override_existing: bool = False  # Sobrescribir keywords existentes

    # Trazabilidad
    correlation_id: Optional[str] = None
    triggered_by: str = "system"  # system, user, scheduler, api

    # Event-Driven: Datos del evento anterior
    plaintext: Optional[str] = None
    """Texto plano del evento ArticleSummaryGenerated."""

    summary: Optional[str] = None
    """Resumen del evento ArticleSummaryGenerated."""

    article_url: Optional[str] = None
    """URL para logging."""

    article_title: Optional[str] = None
    """Título para logging."""
