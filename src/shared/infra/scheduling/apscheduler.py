"""
APScheduler - Implementación de IAPScheduler usando APScheduler library.

Mantiene Clean Architecture encapsulando APScheduler detrás de la interface
IAPScheduler, permitiendo cambiar implementación sin afectar capas superiores.
"""

from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, Optional

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, EVENT_JOB_MISSED
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from redis import Redis

from src.shared.infra.scheduling.redis_jobstore import RedisJobStore
from src.shared.kernel.logger import ILogger
from src.shared.kernel.scheduler import IAPScheduler


class APScheduler(IAPScheduler):
    """
    Implementación de IAPScheduler usando APScheduler library.

    Responsabilidades:
    - Exponer API limpia (IAPScheduler) independiente de APScheduler
    - Configurar APScheduler con persistencia en BD
    - Gestionar lifecycle del scheduler
    - Proveer observabilidad via logging

    Beneficios:
    - Persistencia automática de jobs
    - Cron expressions support
    - Misfire handling automático
    - Event listeners para observabilidad
    - Clustering support (futuro)
    """

    def __init__(
        self,
        logger: ILogger,
        database_url: str,
        redis_url: Optional[str] = None,
        use_redis: bool = False,
        timezone: str = "UTC",
    ):
        """
        Inicializa APScheduler con configuración enterprise.

        Args:
            logger: Logger para observabilidad
            database_url: URL de conexión a BD para persistencia
            redis_url: URL de Redis (ej: redis://localhost:6380/0)
            use_redis: Si True, usa RedisJobStore para persistencia
            timezone: Zona horaria (default: UTC)
        """
        self._logger = logger
        self._timezone = timezone
        self._jobs_metadata: Dict[str, dict] = {}  # Metadata adicional
        self._redis_client = None

        # Configurar job stores
        jobstores = self._configure_jobstore(database_url, redis_url, use_redis)

        # Configurar executors
        executors = {
            "default": AsyncIOExecutor(),
        }

        # Job defaults
        job_defaults = {
            "coalesce": True,  # Combinar ejecuciones perdidas en una sola
            "max_instances": 3,  # Hasta 3 instancias concurrentes (para jobs de alta frecuencia)
            "misfire_grace_time": 60,  # 60s de gracia para ejecuciones perdidas
        }

        # Crear scheduler
        self._scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=timezone,
        )

        # Registrar event listeners para observabilidad
        self._scheduler.add_listener(self._on_job_executed, EVENT_JOB_EXECUTED)
        self._scheduler.add_listener(self._on_job_error, EVENT_JOB_ERROR)
        self._scheduler.add_listener(self._on_job_missed, EVENT_JOB_MISSED)

        self._is_started = False
        self._logger.info("🔧 APScheduler inicializado", timezone=timezone)

    def _configure_jobstore(
        self,
        database_url: str,
        redis_url: Optional[str],
        use_redis: bool,
    ) -> Dict[str, Any]:
        """
        Configura el jobstore apropiado.

        Args:
            database_url: URL de base de datos
            redis_url: URL de Redis
            use_redis: Si usar Redis

        Returns:
            Dict con configuración de jobstores
        """
        if use_redis and redis_url:
            return self._create_redis_jobstore(redis_url)
        else:
            return self._create_memory_jobstore()

    def _create_redis_jobstore(self, redis_url: str) -> Dict[str, Any]:
        """
        Crea RedisJobStore.

        Args:
            redis_url: URL de Redis

        Returns:
            Dict con RedisJobStore configurado
        """
        try:
            # Crear cliente Redis (sync para APScheduler)
            self._redis_client = Redis.from_url(
                redis_url,
                decode_responses=False,  # APScheduler necesita bytes
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )

            # Verificar conexión
            self._redis_client.ping()

            # Crear RedisJobStore
            jobstore = RedisJobStore(
                redis_client=self._redis_client,
                jobs_key="apscheduler:jobs",
                run_times_key="apscheduler:run_times",
            )

            self._logger.info(
                "💾 Usando RedisJobStore (jobs persisten entre reinicios)",
                redis_url=redis_url,
            )

            return {"default": jobstore}

        except Exception as e:
            self._logger.error(
                "❌ Error conectando a Redis, fallback a MemoryJobStore",
                error=str(e),
                redis_url=redis_url,
            )
            return self._create_memory_jobstore()

    def _create_memory_jobstore(self) -> Dict[str, Any]:
        """
        Crea MemoryJobStore.

        Returns:
            Dict con MemoryJobStore configurado
        """
        self._logger.info(
            "💾 Usando MemoryJobStore (jobs no persisten entre reinicios)"
        )
        return {"default": MemoryJobStore()}

    async def start(self) -> None:
        """Inicia el scheduler."""
        if not self._is_started:
            # AsyncIOScheduler.start() debe ejecutarse en el event loop principal
            # Es síncrono pero no bloqueante
            self._scheduler.start()
            self._is_started = True
            self._logger.info("🚀 APScheduler iniciado")

    async def stop(self, wait: bool = True) -> None:
        """
        Detiene el scheduler.

        Args:
            wait: Si esperar a que terminen jobs en ejecución
        """
        if self._is_started:
            self._scheduler.shutdown(wait=wait)
            self._is_started = False

            # Cerrar conexión Redis si existe
            if self._redis_client:
                try:
                    self._redis_client.close()
                    self._logger.info("🔌 Conexión Redis cerrada")
                except Exception as e:
                    self._logger.warning(
                        "⚠️ Error cerrando conexión Redis", error=str(e)
                    )

            self._logger.info("🛑 APScheduler detenido")

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
            name: Nombre único de la tarea (usado como job_id)
            coroutine: Función async a ejecutar
            interval_seconds: Intervalo entre ejecuciones en segundos
            description: Descripción legible de la tarea
            run_on_startup: Si True, ejecuta el job inmediatamente al registrarlo
        """
        # No usar next_run_time en add_job porque puede ser ignorado si ya pasó
        # En su lugar, se disparará manualmente después de start_task si run_on_startup=True
        trigger = IntervalTrigger(seconds=interval_seconds, timezone=self._timezone)

        # Agregar job a APScheduler
        self._scheduler.add_job(
            func=coroutine,
            trigger=trigger,
            id=name,
            name=description or name,
            replace_existing=True,
        )

        # Guardar metadata adicional
        self._jobs_metadata[name] = {
            "description": description,
            "type": "interval",
            "interval_seconds": interval_seconds,
            "registered_at": datetime.now(timezone.utc),
            "run_on_startup": run_on_startup,
        }

        startup_info = " (ejecutará al startup)" if run_on_startup else ""
        self._logger.info(
            f"📝 Job registrado: {name}{startup_info}",
            interval_seconds=interval_seconds,
            description=description,
            run_on_startup=run_on_startup,
        )

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
            cron_expression: Expresión cron (ej: "0 6 * * *" = 6am diario)
            description: Descripción legible
        """
        trigger = CronTrigger.from_crontab(cron_expression, timezone=self._timezone)

        self._scheduler.add_job(
            func=coroutine,
            trigger=trigger,
            id=name,
            name=description or name,
            replace_existing=True,
        )

        self._jobs_metadata[name] = {
            "description": description,
            "type": "cron",
            "cron_expression": cron_expression,
            "registered_at": datetime.now(timezone.utc),
        }

        self._logger.info(
            f"📝 Job cron registrado: {name}",
            cron=cron_expression,
            description=description,
        )

    def start_task(self, name: str) -> bool:
        """
        Inicia (reanuda) una tarea.
        Si el job tiene run_on_startup=True, lo dispara inmediatamente.

        Args:
            name: Nombre de la tarea

        Returns:
            True si se inició correctamente
        """
        try:
            self._scheduler.resume_job(name)
            self._logger.info(f"▶️ Job resumido: {name}")

            # Si el job tiene run_on_startup, dispararlo inmediatamente
            metadata = self._jobs_metadata.get(name, {})
            if metadata.get("run_on_startup", False):
                self._logger.info(f"🎯 Ejecutando job al startup: {name}")
                self.trigger_job(name)

            return True
        except Exception as e:
            self._logger.error(f"❌ Error iniciando job '{name}': {e}")
            return False

    def stop_task(self, name: str, force: bool = False) -> bool:
        """
        Detiene (pausa) una tarea.

        Args:
            name: Nombre de la tarea
            force: No usado (compatibilidad con interface)

        Returns:
            True si se detuvo correctamente
        """
        try:
            self._scheduler.pause_job(name)
            self._logger.info(f"⏸️ Job pausado: {name}")
            return True
        except Exception as e:
            self._logger.error(f"❌ Error deteniendo job '{name}': {e}")
            return False

    def remove_task(self, name: str) -> bool:
        """
        Elimina una tarea completamente.

        Args:
            name: Nombre de la tarea

        Returns:
            True si se eliminó correctamente
        """
        try:
            self._scheduler.remove_job(name)
            if name in self._jobs_metadata:
                del self._jobs_metadata[name]
            self._logger.info(f"🗑️ Job eliminado: {name}")
            return True
        except Exception as e:
            self._logger.warning(f"⚠️ Error eliminando job '{name}': {e}")
            return False

    def trigger_job(self, name: str) -> bool:
        """
        Ejecuta un job manualmente (fuera de schedule).

        Args:
            name: Nombre de la tarea

        Returns:
            True si se disparó correctamente
        """
        try:
            job = self._scheduler.get_job(name)
            if job:
                job.modify(next_run_time=datetime.now(self._scheduler.timezone))
                self._logger.info(f"🎯 Job disparado manualmente: {name}")
                return True
            return False
        except Exception as e:
            self._logger.warning(f"⚠️ Error disparando job '{name}': {e}")
            return False

    def is_task_running(self, name: str) -> bool:
        """
        Verifica si una tarea está activa (no pausada).

        Args:
            name: Nombre de la tarea

        Returns:
            True si la tarea existe y está activa
        """
        job = self._scheduler.get_job(name)
        if not job:
            return False
        return job.next_run_time is not None

    def get_task_info(self, name: str) -> Optional[dict]:
        """
        Obtiene información detallada de una tarea.

        Args:
            name: Nombre de la tarea

        Returns:
            Dict con información o None si no existe
        """
        job = self._scheduler.get_job(name)
        if not job:
            return None

        metadata = self._jobs_metadata.get(name, {})

        return {
            "id": job.id,
            "name": job.name,
            "next_run_time": (
                job.next_run_time.isoformat() if job.next_run_time else None
            ),
            "trigger": str(job.trigger),
            "is_paused": job.next_run_time is None,
            **metadata,
        }

    def update_task_interval(self, name: str, interval_seconds: int) -> bool:
        """
        Actualiza el intervalo de una tarea.

        Args:
            name: Nombre de la tarea
            interval_seconds: Nuevo intervalo en segundos

        Returns:
            True si se actualizó correctamente
        """
        try:
            new_trigger = IntervalTrigger(
                seconds=interval_seconds, timezone=self._timezone
            )
            self._scheduler.reschedule_job(job_id=name, trigger=new_trigger)

            # Actualizar metadata
            if name in self._jobs_metadata:
                self._jobs_metadata[name]["interval_seconds"] = interval_seconds

            self._logger.info(
                f"🔄 Intervalo actualizado para '{name}': {interval_seconds}s"
            )
            return True
        except Exception as e:
            self._logger.error(f"❌ Error actualizando intervalo de '{name}': {e}")
            return False

    def update_task_config(self, name: str, interval_seconds: int) -> None:
        """
        Actualiza configuración de tarea (alias de update_task_interval).

        Args:
            name: Nombre de la tarea
            interval_seconds: Nuevo intervalo en segundos
        """
        self.update_task_interval(name, interval_seconds)

    def is_healthy(self) -> bool:
        """
        Verifica si el scheduler está en estado saludable.

        Returns:
            True si está corriendo correctamente
        """
        return self._is_started and self._scheduler.running

    def list_jobs(self) -> list[dict]:
        """
        Lista todos los jobs registrados.

        Returns:
            Lista de dicts con información de cada job
        """
        jobs = []
        for job in self._scheduler.get_jobs():
            job_info = self.get_task_info(job.id)
            if job_info:
                jobs.append(job_info)
        return jobs

    def get_scheduler_status(self) -> dict:
        """
        Obtiene estado general del scheduler.

        Returns:
            Dict con métricas y estado
        """
        return {
            "running": self._is_started,
            "healthy": self.is_healthy(),
            "state": self._scheduler.state,
            "jobs_count": len(self._scheduler.get_jobs()),
            "timezone": self._timezone,
        }

    # Event listeners para observabilidad

    def _on_job_executed(self, event):
        """Listener para jobs ejecutados exitosamente."""
        # Jobs de alta frecuencia: log a nivel DEBUG
        if event.job_id == "crypto_multi_exchange_aggregation":
            self._logger.debug(
                f"✅ Job ejecutado: {event.job_id}",
                job_id=event.job_id,
                scheduled_run_time=event.scheduled_run_time,
            )
        else:
            # Otros jobs: SUCCESS (normal)
            self._logger.success(
                f"✅ Job ejecutado: {event.job_id}",
                job_id=event.job_id,
                scheduled_run_time=event.scheduled_run_time,
            )

    def _on_job_error(self, event):
        """Listener para jobs con error."""
        self._logger.error(
            f"❌ Job falló: {event.job_id}",
            job_id=event.job_id,
            exception=str(event.exception),
            traceback=event.traceback,
        )

    def _on_job_missed(self, event):
        """Listener para jobs que no se ejecutaron (misfire)."""
        self._logger.warning(
            f"⚠️ Job perdido (misfire): {event.job_id}",
            job_id=event.job_id,
            scheduled_run_time=event.scheduled_run_time,
        )
