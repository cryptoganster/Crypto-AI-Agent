"""Process Managers para el bounded context Scraping.

Los Process Managers orquestan flujos de negocio complejos que involucran
múltiples comandos y eventos. Son event-driven: escuchan Domain Events
y emiten Commands al bus.

Según CQRS estricto (Greg Young, Vaughn Vernon, Udi Dahan):
- NO son Command Handlers (no se registran en el Mediator)
- NO hacen queries directamente (usan eventos para obtener datos)
- NO llaman handlers directamente (emiten comandos al bus)
- SÍ mantienen estado del proceso
- SÍ reaccionan a Domain Events
- SÍ emiten Commands

Ubicación correcta: src/<bounded-context>/app/process_managers/
"""

from src.scraping.app.process_managers.scraping_pipeline import ScrapingPipeline

__all__ = [
    "ScrapingPipeline",
]
