"""Scraping application layer.

Estructura CQRS estricta:
- commands/: Command Handlers simples (1 agregado, 1 operación)
- queries/: Query Handlers puros
- process_managers/: Orquestación event-driven

Para orquestación compleja, usar Process Managers:
- ScrapingSourcesPipelineManager: Pipeline de scraping de múltiples sources
"""

# Los imports se hacen de forma lazy para evitar imports circulares
# y problemas con archivos deprecados.

__all__ = [
    # Los exports se definen pero no se importan automáticamente
    # para evitar problemas con archivos deprecados.
    # Importar directamente desde los módulos específicos:
    # from src.scraping.app.commands.scrape_source import ScrapeSourceCommand
    # from src.scraping.app.process_managers import ScrapingSourcesPipelineManager
]
