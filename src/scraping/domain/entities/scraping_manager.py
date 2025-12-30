"""ScrapingManager Entity - Gestiona operaciones de scraping para fuentes RSS."""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from src.rss.feed.domain.value_objects.configuration import SourceConfiguration
from src.scraping.domain.entities.scraping_record import (
    ScrapingId,
    ScrapingRecord,
    ScrapingRecordStatus,
)
from src.scraping.domain.value_objects.status import ScrapingStatus


class ScrapingManager:
    """
    Entity que gestiona las operaciones de scraping para una fuente RSS.

    Responsabilidades:
    - Iniciar, completar, fallar, cancelar y hacer timeout de operaciones de scraping
    - Mantener historial de scraping como entidades internas
    - Gestionar estado actual de scraping con invariantes de negocio
    - Programar próximo scraping basado en configuración
    - Proporcionar métricas y análisis del historial de scraping
    """

    def __init__(self, source_id: str, configuration: SourceConfiguration):
        """
        Inicializa ScrapingManager.

        Args:
            source_id: ID de la fuente RSS propietaria
            configuration: Configuración de scraping
        """
        self._source_id = source_id
        self._configuration = configuration

        # Historial de scraping como entidades internas
        self._scraping_history: Dict[str, ScrapingRecord] = {}

        # Estado actual de scraping con invariantes de negocio
        self._scraping_state: ScrapingStatus = ScrapingStatus.idle()

        # Timestamps de control
        self._last_scraping_at: Optional[datetime] = None
        self._next_scraping_at: Optional[datetime] = None

    @property
    def scraping_state(self) -> ScrapingStatus:
        """Estado actual de scraping con invariantes de negocio."""
        return self._scraping_state

    @property
    def last_scraping_at(self) -> Optional[datetime]:
        """Timestamp del último scraping."""
        return self._last_scraping_at

    @property
    def next_scraping_at(self) -> Optional[datetime]:
        """Timestamp del próximo scraping programado."""
        return self._next_scraping_at

    @property
    def scraping_history(self) -> List[ScrapingRecord]:
        """Lista de registros de scraping (copia para inmutabilidad)."""
        return list(self._scraping_history.values())

    @property
    def can_start_scraping(self) -> bool:
        """True si se puede iniciar un nuevo scraping."""
        return self._scraping_state.can_start_new_scraping()

    @property
    def is_scraping_active(self) -> bool:
        """True si hay un scraping en progreso."""
        return self._scraping_state.is_active

    def start_scraping(
        self,
        scraping_type: str = "scheduled",
        timeout_seconds: int = 30,
        max_articles: Optional[int] = None,
        scraped_by: Optional[str] = None,
    ) -> ScrapingId:
        """
        Inicia una nueva operación de scraping con validaciones de negocio.

        Args:
            scraping_type: Tipo de scraping (scheduled, manual, retry)
            timeout_seconds: Timeout en segundos
            max_articles: Límite máximo de artículos
            scraped_by: Usuario o sistema que inicia el scraping

        Returns:
            ID del scraping record creado

        Raises:
            ValueError: Si no se puede iniciar el scraping
        """
        # Validar invariantes de negocio
        if not self.can_start_scraping:
            raise ValueError(
                f"No se puede iniciar scraping - estado actual: {self._scraping_state.phase}"
            )

        # Crear scraping record
        scraping_record = ScrapingRecord(scraped_by=scraped_by)
        scraping_id = str(scraping_record.id)
        self._scraping_history[scraping_id] = scraping_record

        # Actualizar estado de scraping
        self._scraping_state = ScrapingStatus.starting(
            scraping_id=scraping_id, timeout_seconds=timeout_seconds
        )

        return scraping_record.id

    def complete_scraping(
        self,
        scraping_id: ScrapingId,
        articles_found: int,
        articles_new: int = 0,
        response_time_ms: Optional[float] = None,
        bytes_processed: Optional[int] = None,
        http_status_code: Optional[int] = None,
    ) -> int:
        """
        Completa una operación de scraping exitosamente.

        Args:
            scraping_id: ID del scraping a completar
            articles_found: Total de artículos encontrados
            articles_new: Artículos nuevos
            response_time_ms: Tiempo de respuesta
            bytes_processed: Bytes procesados
            http_status_code: Código de estado HTTP

        Returns:
            Duración en millisegundos del scraping

        Raises:
            KeyError: Si el scraping_id no existe
            ValueError: Si el estado no permite completar el scraping
        """
        scraping_record = self._get_scraping_record(scraping_id)

        # Validar que el scraping puede ser completado
        if str(scraping_id) != self._scraping_state.current_scraping_id:
            raise ValueError(
                f"Scraping ID {scraping_id} no coincide con scraping activo {self._scraping_state.current_scraping_id}"
            )

        # Completar el scraping record
        scraping_record.complete(articles_found, articles_new, response_time_ms)

        # Calcular duración y actualizar estado
        duration_ms = int(self._scraping_state.duration_seconds * 1000)
        self._scraping_state = self._scraping_state.transition_to_idle()
        self._last_scraping_at = datetime.now(timezone.utc)

        # Programar próximo scraping
        self._schedule_next_scraping()

        return duration_ms

    def fail_scraping(
        self,
        scraping_id: ScrapingId,
        error_message: str,
        http_status_code: Optional[int] = None,
    ) -> tuple[int, bool]:
        """
        Marca una operación de scraping como fallida.

        Args:
            scraping_id: ID del scraping que falló
            error_message: Mensaje de error
            http_status_code: Código de estado HTTP si aplica

        Returns:
            Tupla con (duración_ms, should_suspend) - indica si debe suspenderse por errores consecutivos

        Raises:
            KeyError: Si el scraping_id no existe
            ValueError: Si el estado no permite fallar el scraping
        """
        scraping_record = self._get_scraping_record(scraping_id)

        # Validar que el scraping puede ser marcado como fallido
        if str(scraping_id) != self._scraping_state.current_scraping_id:
            raise ValueError(
                f"Scraping ID {scraping_id} no coincide con scraping activo {self._scraping_state.current_scraping_id}"
            )

        # Marcar scraping record como fallido
        scraping_record.fail(error_message)

        # Calcular duración y actualizar estado
        duration_ms = int(self._scraping_state.duration_seconds * 1000)
        self._scraping_state = self._scraping_state.transition_to_idle()

        # Verificar si suspender por errores consecutivos
        recent_failures = self._count_recent_failures()
        should_suspend = recent_failures >= 5  # Configurable

        return duration_ms, should_suspend

    def cancel_scraping(
        self, scraping_id: ScrapingId, reason: str = "Cancelado por usuario"
    ) -> int:
        """
        Cancela una operación de scraping en progreso.

        Args:
            scraping_id: ID del scraping a cancelar
            reason: Razón de cancelación

        Returns:
            Duración en millisegundos del scraping cancelado

        Raises:
            KeyError: Si el scraping_id no existe
            ValueError: Si el scraping no puede ser cancelado
        """
        scraping_record = self._get_scraping_record(scraping_id)

        # Validar que el scraping puede ser cancelado
        if str(scraping_id) != self._scraping_state.current_scraping_id:
            raise ValueError(
                f"Scraping ID {scraping_id} no coincide con scraping activo {self._scraping_state.current_scraping_id}"
            )

        if not self._scraping_state.can_be_cancelled():
            raise ValueError(
                f"No se puede cancelar scraping en estado {self._scraping_state.phase}"
            )

        # Marcar scraping record como fallido con razón de cancelación
        scraping_record.fail(f"Cancelado: {reason}")

        # Calcular duración y actualizar estado
        duration_ms = int(self._scraping_state.duration_seconds * 1000)
        self._scraping_state = self._scraping_state.transition_to_idle()

        return duration_ms

    def timeout_scraping(self, scraping_id: ScrapingId) -> int:
        """
        Marca un scraping como terminado por timeout.

        Args:
            scraping_id: ID del scraping que hizo timeout

        Returns:
            Duración en millisegundos del scraping

        Raises:
            KeyError: Si el scraping_id no existe
            ValueError: Si el estado no es consistente
        """
        scraping_record = self._get_scraping_record(scraping_id)

        # Validar que el scraping puede hacer timeout
        if str(scraping_id) != self._scraping_state.current_scraping_id:
            raise ValueError(
                f"Scraping ID {scraping_id} no coincide con scraping activo {self._scraping_state.current_scraping_id}"
            )

        # Marcar scraping record como fallido por timeout
        error_msg = (
            f"Timeout después de {self._scraping_state.timeout_seconds} segundos"
        )
        scraping_record.fail(error_msg)

        # Calcular duración y actualizar estado
        duration_ms = int(self._scraping_state.duration_seconds * 1000)
        self._scraping_state = self._scraping_state.transition_to_idle()

        return duration_ms

    def is_ready_for_scraping(self, is_source_active: bool) -> bool:
        """
        Verifica si está listo para ser scrapeado.

        Args:
            is_source_active: True si la fuente está activa

        Returns:
            True si está activa y es momento de hacer scraping
        """
        if not is_source_active:
            return False

        if self._next_scraping_at is None:
            return True

        return datetime.now(timezone.utc) >= self._next_scraping_at

    def get_recent_scraping_history(self, limit: int = 10) -> List[ScrapingRecord]:
        """
        Obtiene el historial de scraping reciente.

        Args:
            limit: Número máximo de registros

        Returns:
            Lista de ScrapingRecords ordenados por fecha (más recientes primero)
        """
        sorted_history = sorted(
            self._scraping_history.values(),
            key=lambda s: s.started_at,
            reverse=True,
        )
        return sorted_history[:limit]

    def update_configuration(self, new_config: SourceConfiguration) -> bool:
        """
        Actualiza la configuración de scraping.

        Args:
            new_config: Nueva configuración

        Returns:
            True si hubo cambios
        """
        if new_config != self._configuration:
            self._configuration = new_config
            return True
        return False

    def schedule_next_scraping(self, is_source_active: bool) -> None:
        """
        Programa el próximo scraping basado en la configuración y estado.

        Args:
            is_source_active: True si la fuente está activa
        """
        if is_source_active:
            self._schedule_next_scraping()
        else:
            self._next_scraping_at = None

    def get_scraping_statistics(self) -> dict:
        """
        Obtiene estadísticas del historial de scraping.

        Returns:
            Diccionario con estadísticas básicas
        """
        if not self._scraping_history:
            return {
                "total_scrapings": 0,
                "successful_scrapings": 0,
                "failed_scrapings": 0,
                "success_rate": 0.0,
                "recent_failures": 0,
            }

        total_scrapings = len(self._scraping_history)
        successful_scrapings = sum(
            1 for s in self._scraping_history.values() if s.is_successful()
        )
        failed_scrapings = total_scrapings - successful_scrapings
        success_rate = (
            successful_scrapings / total_scrapings if total_scrapings > 0 else 0.0
        )
        recent_failures = self._count_recent_failures()

        return {
            "total_scrapings": total_scrapings,
            "successful_scrapings": successful_scrapings,
            "failed_scrapings": failed_scrapings,
            "success_rate": success_rate,
            "recent_failures": recent_failures,
        }

    def _get_scraping_record(self, scraping_id: ScrapingId) -> ScrapingRecord:
        """Obtiene un scraping record por ID."""
        scraping_record = self._scraping_history.get(str(scraping_id))
        if scraping_record is None:
            raise KeyError(f"Scraping record {scraping_id} no encontrado")
        return scraping_record

    def _schedule_next_scraping(self) -> None:
        """Programa el próximo scraping basado en la configuración."""
        interval = timedelta(minutes=self._configuration.fetch_interval_minutes)
        self._next_scraping_at = datetime.now(timezone.utc) + interval

    def _count_recent_failures(self, hours: int = 24) -> int:
        """Cuenta los failures recientes en las últimas X horas."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        failures = []
        for s in self._scraping_history.values():
            # Manejar timezone-naive datetimes
            started_at = s.started_at
            if started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=timezone.utc)

            if started_at >= cutoff and s.status.is_failed():
                failures.append(s)

        return len(failures)
