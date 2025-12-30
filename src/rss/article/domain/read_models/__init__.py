"""Read Models para el Read Side (CQRS Estricto).

Los Read Models son objetos de transferencia de datos sin comportamiento,
usados exclusivamente para queries de lectura.

NO confundir con Aggregates:
- Read Models: Solo datos (read side)
- Aggregates: Datos + comportamiento (write side)
"""

from .rss_article_read_model import ArticleReadModel

__all__ = ["ArticleReadModel"]
