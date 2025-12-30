"""Article Application Layer.

Este módulo contiene la capa de aplicación del bounded context de Article:
- commands/: Command Handlers simples (1 agregado, 1 operación)
- queries/: Query Handlers puros
- process_managers/: Orquestación event-driven

Uso:
    from src.rss.article.app.commands.scrape_content import ScrapeArticleContentCommand
    from src.rss.article.app.process_managers import ArticleContentPipelineManager

Para orquestación compleja, usar Process Managers:
- ArticleContentPipelineManager: Pipeline de procesamiento de contenido
"""

# No importar automáticamente para evitar problemas con archivos
# que tienen imports rotos. Importar directamente desde los módulos.

__all__ = []
