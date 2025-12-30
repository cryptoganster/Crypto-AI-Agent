"""
Interface para Scheduler de tareas programadas (Shared Kernel).

Define el contrato para gestión de jobs programados siguiendo
el principio de Dependency Inversion de Clean Architecture.
"""

from typing import Any, Awaitable, Callable, Dict, List, Optional, Protocol


class IAPScheduler(Protocol):
    """
    Interface para scheduler de tareas programadas.

    Abstrae la implementación del scheduler (APScheduler, Celery, etc.)
    permitiendo cambiar implementación sin afectar capas superiores.

    Esta interface es parte del Shared Kernel y puede ser usada por
    todos los bounded contexts que necesiten scheduling.
    """

    async def start(self) -> None:
        """Inicia el scheduler."""
        ...

    async def stop(self, wait: bool = True) -> None:
        """
        Detiene el scheduler.

        Args:
            wait: Si esperar a que terminen jobs en ejecución
        """
        ...

    def register_task(
        self,
        name: str,
        coroutine: Callable[[], Awaitable[Any]],
        interval_seconds: int,
        description: str = "",
        run_on_startup: bool = False,
    ) -> None:
        """
        Registra una tarea con intervalo fijo.

        Args:
            name: Nombre único de la tarea
            coroutine: Función async a ejecutar
            interval_seconds: Intervalo entre ejecuciones
            description: Descripción de la tarea
            run_on_startup: Si ejecutar inmediatamente al iniciar
        """
        ...

    def register_cron_task(
        self,
        name: str,
        coroutine: Callable[[], Awaitable[Any]],
        cron_expression: str,
        description: str = "",
    ) -> None:
        """
        Registra una tarea con expresión cron.

        Args:
            name: Nombre único de la tarea
            coroutine: Función async a ejecutar
            cron_expression: Expresión cron (ej: "0 6 * * *")
            description: Descripción de la tarea
        """
        ...

    def start_task(self, name: str) -> bool:
        """
        Inicia (resume) una tarea pausada.

        Args:
            name: Nombre de la tarea

        Returns:
            True si se inició correctamente
        """
        ...

    def stop_task(self, name: str, force: bool = False) -> bool:
        """
        Detiene (pausa) una tarea.

        Args:
            name: Nombre de la tarea
            force: No usado (compatibilidad)

        Returns:
            True si se detuvo correctamente
        """
        ...

    def remove_task(self, name: str) -> bool:
        """
        Elimina una tarea completamente.

        Args:
            name: Nombre de la tarea

        Returns:
            True si se eliminó correctamente
        """
        ...

    def trigger_job(self, name: str) -> bool:
        """
        Ejecuta un job manualmente (fuera de schedule).

        Args:
            name: Nombre de la tarea

        Returns:
            True si se disparó correctamente
        """
        ...

    def is_task_running(self, name: str) -> bool:
        """
        Verifica si una tarea está activa.

        Args:
            name: Nombre de la tarea

        Returns:
            True si está activa
        """
        ...

    def get_task_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de una tarea.

        Args:
            name: Nombre de la tarea

        Returns:
            Dict con información o None si no existe
        """
        ...

    def update_task_interval(self, name: str, interval_seconds: int) -> bool:
        """
        Actualiza el intervalo de una tarea.

        Args:
            name: Nombre de la tarea
            interval_seconds: Nuevo intervalo

        Returns:
            True si se actualizó correctamente
        """
        ...

    def update_task_config(self, name: str, interval_seconds: int) -> None:
        """
        Actualiza configuración de tarea (alias de update_task_interval).

        Args:
            name: Nombre de la tarea
            interval_seconds: Nuevo intervalo en segundos
        """
        ...

    def is_healthy(self) -> bool:
        """
        Verifica si el scheduler está en estado saludable.

        Returns:
            True si está corriendo correctamente
        """
        ...

    def list_jobs(self) -> List[Dict[str, Any]]:
        """
        Lista todos los jobs registrados.

        Returns:
            Lista de dicts con información de cada job
        """
        ...

    def get_scheduler_status(self) -> Dict[str, Any]:
        """
        Obtiene estado general del scheduler.

        Returns:
            Dict con métricas y estado
        """
        ...
