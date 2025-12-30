"""Handler validation utilities."""

from loguru import logger

from src.shared.config import AppConfig


def validate_critical_handlers(mediator, config: AppConfig) -> None:
    """
    Valida que los handlers críticos estén registrados.

    NOTA: Los pipelines antiguos (RunFetchPipeline, RunProcessingPipeline, RunScrapingPipeline)
    están siendo reemplazados por arquitectura event-driven en bounded contexts.
    Solo validamos los comandos event-driven nuevos.

    En modo development: Lanza RuntimeError si falta algún handler crítico.
    En modo production: Loggea warning y continúa (degradación graceful).

    Args:
        mediator: Instancia del Mediator con handlers registrados
        config: Configuración de la aplicación para determinar el entorno

    Raises:
        RuntimeError: Si faltan handlers críticos en modo development
    """
    from src.scraping.app.commands import ScrapeSourceCommand, StartScrapingCommand

    # Solo comandos event-driven críticos (los pipelines antiguos están deprecated)
    critical_commands = [
        StartScrapingCommand,  # Inicia scraping event-driven
        ScrapeSourceCommand,  # Scrapea source individual
    ]

    missing_handlers = []
    registered_critical = []

    for command_type in critical_commands:
        if command_type not in mediator._handler_registry:
            missing_handlers.append(command_type.__name__)
            logger.warning(
                "Handler crítico faltante",
                command=command_type.__name__,
            )
        else:
            registered_critical.append(command_type.__name__)
            logger.debug(
                "Handler crítico registrado",
                command=command_type.__name__,
            )

    # Log summary
    logger.info(
        "Validación de handlers críticos completada",
        total_critical=len(critical_commands),
        registered=len(registered_critical),
        missing=len(missing_handlers),
    )

    if missing_handlers:
        if config.is_development:
            # Development: Fallar rápido
            logger.error(
                "Handlers críticos faltantes detectados en development",
                missing_handlers=missing_handlers,
                registered_handlers=registered_critical,
            )
            raise RuntimeError(
                f"Critical handlers missing: {', '.join(missing_handlers)}. "
                f"Did you forget to call register_pipeline_handlers()?"
            )
        else:
            # Production: Loggear warning y continuar (degradación graceful)
            logger.warning(
                "Handlers críticos faltantes detectados en production",
                missing_handlers=missing_handlers,
                registered_handlers=registered_critical,
                message="Sistema continuará con degradación graceful",
            )


def verify_event_driven_handlers(mediator, logger_instance) -> None:
    """
    Verifica que los handlers event-driven estén registrados.

    Args:
        mediator: Instancia del Mediator
        logger_instance: Logger para logging

    Raises:
        RuntimeError: Si faltan handlers event-driven críticos
    """
    from src.scraping.app.commands import ScrapeSourceCommand, StartScrapingCommand

    registered_handlers = mediator._handler_registry

    required_commands = [
        StartScrapingCommand,
        ScrapeSourceCommand,
    ]

    missing_handlers = [
        cmd.__name__ for cmd in required_commands if cmd not in registered_handlers
    ]

    if missing_handlers:
        logger_instance.error(
            "❌ Handlers event-driven críticos faltantes en Mediator",
            missing_handlers=missing_handlers,
        )
        raise RuntimeError(f"Handlers event-driven no registrados: {missing_handlers}")

    logger_instance.info(
        "✅ Mediator verificado con arquitectura event-driven",
        event_driven_commands_registered=[
            "StartScrapingCommand",
            "ScrapeSourceCommand",
        ],
        note="Pipelines antiguos (RunFetch/Processing/Scraping) deprecated - usando event-driven",
    )
