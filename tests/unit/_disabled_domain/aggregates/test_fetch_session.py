"""Tests para FetchSession Aggregate - Multi-Source Support."""

from datetime import datetime, timezone
from typing import List

import pytest

from src.rss.feed.domain.value_objects import RssFeedId
from src.scraping.domain.aggregates import Scraping
from src.scraping.domain.events.completed import ScrapingCompleted
from src.scraping.domain.events.failed import ScrapingFailed
from src.scraping.domain.events.started import ScrapingStarted
from src.scraping.domain.factories import ScrapingFactory
from src.scraping.domain.value_objects import ScrapingConfig, ScrapingMetrics


class TestFetchSessionMultiSource:
    """Tests para funcionalidad multi-source de FetchSession."""

    @pytest.fixture
    def factory(self):
        """Factory para crear FetchSessions."""
        return ScrapingFactory()

    def test_create_multi_source_with_valid_sources(self, factory):
        """Debería crear FetchSession con múltiples sources válidos."""
        # Arrange
        sources = [
            RssFeedId("source-1"),
            RssFeedId("source-2"),
            RssFeedId("source-3"),
        ]
        config = ScrapingConfig(max_concurrent_scrapes=2, timeout_seconds=60)

        # Act
        session = factory.create_multi_source(sources=sources, config=config)

        # Assert
        assert session.id is not None
        assert len(session.sources_to_fetch) == 3
        assert session.sources_to_fetch == sources
        assert len(session.sources_in_progress) == 0
        assert len(session.sources_completed) == 0
        assert len(session.sources_failed) == 0
        assert session.config.max_concurrent_fetches == 2
        assert session.config.timeout_seconds == 60
        assert session.metrics.articles_discovered == 0
        assert session.metrics.sources_successful == 0
        assert session.metrics.sources_failed == 0

    def test_create_multi_source_with_empty_list_raises_error(self, factory):
        """Debería lanzar ValueError si la lista de sources está vacía."""
        # Arrange
        sources: List[RssFeedId] = []

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            factory.create_multi_source(sources=sources)

        assert "no puede estar vacía" in str(exc_info.value)

    def test_create_multi_source_emits_started_event(self, factory):
        """Debería emitir evento ScrapingStarted al crear."""
        # Arrange
        sources = [RssFeedId("source-1"), RssFeedId("source-2")]
        config = ScrapingConfig(max_concurrent_scrapes=3)

        # Act
        session = factory.create_multi_source(sources=sources, config=config)

        # Assert
        events = session.get_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], ScrapingStarted)
        assert events[0].sources_count == 2
        assert events[0].max_concurrent == 3

    def test_start_source_fetch_marks_as_in_progress(self, factory):
        """Debería marcar source como en progreso."""
        # Arrange
        sources = [RssFeedId("source-1"), RssFeedId("source-2")]
        session = factory.create_multi_source(sources=sources)
        source_to_start = sources[0]

        # Act
        session.start_source_fetch(source_to_start)

        # Assert
        assert source_to_start in session.sources_in_progress
        assert source_to_start not in session.sources_completed
        assert source_to_start not in session.sources_failed

    def test_start_source_fetch_with_invalid_source_raises_error(self, factory):
        """Debería lanzar ValueError si el source no está en la lista."""
        # Arrange
        sources = [RssFeedId("source-1")]
        session = factory.create_multi_source(sources=sources)
        invalid_source = RssFeedId("source-999")

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            session.start_source_fetch(invalid_source)

        assert "no está en la lista" in str(exc_info.value)

    def test_start_source_fetch_already_in_progress_raises_error(self, factory):
        """Debería lanzar ValueError si el source ya está en progreso."""
        # Arrange
        sources = [RssFeedId("source-1")]
        session = factory.create_multi_source(sources=sources)
        session.start_source_fetch(sources[0])

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            session.start_source_fetch(sources[0])

        assert "ya está en progreso" in str(exc_info.value)

    def test_complete_source_fetch_updates_metrics(self, factory):
        """Debería actualizar métricas al completar source."""
        # Arrange
        sources = [RssFeedId("source-1")]
        session = factory.create_multi_source(sources=sources)
        session.start_source_fetch(sources[0])

        # Act
        session.complete_source_fetch(
            source_id=sources[0],
            articles_discovered=10,
            articles_new=5,
            articles_updated=3,
            processing_time_seconds=2.5,
            response_time_ms=150.0,
        )

        # Assert
        assert sources[0] in session.sources_completed
        assert sources[0] not in session.sources_in_progress
        assert session.metrics.articles_discovered == 10
        assert session.metrics.articles_new == 5
        assert session.metrics.articles_updated == 3
        assert session.metrics.sources_successful == 1
        assert session.metrics.sources_failed == 0
        assert session.metrics.total_processing_time_seconds == 2.5
        assert session.metrics.average_response_time_ms == 150.0

    def test_complete_source_fetch_not_in_progress_raises_error(self, factory):
        """Debería lanzar ValueError si el source no está en progreso."""
        # Arrange
        sources = [RssFeedId("source-1")]
        session = factory.create_multi_source(sources=sources)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            session.complete_source_fetch(source_id=sources[0])

        assert "no está en progreso" in str(exc_info.value)

    def test_fail_source_fetch_registers_error(self, factory):
        """Debería registrar error al fallar source."""
        # Arrange
        sources = [RssFeedId("source-1")]
        session = factory.create_multi_source(sources=sources)
        session.start_source_fetch(sources[0])

        # Act
        session.fail_source_fetch(
            source_id=sources[0],
            error_type="TIMEOUT",
            error_message="Connection timeout",
            is_recoverable=True,
            http_status_code=504,
        )

        # Assert
        assert sources[0] in session.sources_failed
        assert sources[0] not in session.sources_in_progress
        assert session.metrics.sources_failed == 1
        assert session.metrics.sources_successful == 0
        assert len(session.errors) == 1
        assert session.errors[0].error_type == "TIMEOUT"
        assert session.errors[0].error_message == "Connection timeout"
        assert session.errors[0].http_status_code == 504

    def test_calculate_progress_percentage_correct(self, factory):
        """Debería calcular porcentaje de progreso correctamente."""
        # Arrange
        sources = [RssFeedId(f"source-{i}") for i in range(10)]
        session = factory.create_multi_source(sources=sources)

        # Completar 3 sources
        for i in range(3):
            session.start_source_fetch(sources[i])
            session.complete_source_fetch(sources[i])

        # Fallar 2 sources
        for i in range(3, 5):
            session.start_source_fetch(sources[i])
            session.fail_source_fetch(
                sources[i],
                error_type="ERROR",
                error_message="Test error",
            )

        # Act
        progress = session.calculate_progress_percentage()

        # Assert
        # 5 procesados de 10 = 50%
        assert progress == 50.0

    def test_calculate_progress_percentage_all_completed(self, factory):
        """Debería retornar 100% cuando todos están completados."""
        # Arrange
        sources = [RssFeedId("source-1"), RssFeedId("source-2")]
        session = factory.create_multi_source(sources=sources)

        # Completar todos
        for source in sources:
            session.start_source_fetch(source)
            session.complete_source_fetch(source)

        # Act
        progress = session.calculate_progress_percentage()

        # Assert
        assert progress == 100.0

    def test_estimate_completion_time_with_progress(self, factory):
        """Debería estimar tiempo de completado basado en progreso."""
        # Arrange
        sources = [RssFeedId(f"source-{i}") for i in range(4)]
        session = factory.create_multi_source(sources=sources)

        # Completar 2 sources (50%)
        for i in range(2):
            session.start_source_fetch(sources[i])
            session.complete_source_fetch(sources[i])

        # Act
        estimated = session.estimate_completion_time()

        # Assert
        assert estimated is not None
        assert estimated > datetime.now(timezone.utc)

    def test_estimate_completion_time_no_progress_returns_none(self, factory):
        """Debería retornar None si no hay progreso."""
        # Arrange
        sources = [RssFeedId("source-1")]
        session = factory.create_multi_source(sources=sources)

        # Act
        estimated = session.estimate_completion_time()

        # Assert
        assert estimated is None

    def test_estimate_completion_time_completed_returns_completed_at(self, factory):
        """Debería retornar completed_at si la sesión está completa."""
        # Arrange
        sources = [RssFeedId("source-1")]
        session = factory.create_multi_source(sources=sources)
        session.start_source_fetch(sources[0])
        session.complete_source_fetch(sources[0])

        # Act
        estimated = session.estimate_completion_time()

        # Assert
        assert estimated == session.completed_at

    def test_is_complete_when_all_processed(self, factory):
        """Debería retornar True cuando todos los sources fueron procesados."""
        # Arrange
        sources = [RssFeedId("source-1"), RssFeedId("source-2")]
        session = factory.create_multi_source(sources=sources)

        # Completar ambos
        session.start_source_fetch(sources[0])
        session.complete_source_fetch(sources[0])
        session.start_source_fetch(sources[1])
        session.complete_source_fetch(sources[1])

        # Act & Assert
        assert session.is_complete() is True

    def test_is_complete_when_not_all_processed(self, factory):
        """Debería retornar False cuando no todos fueron procesados."""
        # Arrange
        sources = [RssFeedId("source-1"), RssFeedId("source-2")]
        session = factory.create_multi_source(sources=sources)

        # Completar solo uno
        session.start_source_fetch(sources[0])
        session.complete_source_fetch(sources[0])

        # Act & Assert
        assert session.is_complete() is False

    def test_get_errors_by_type_groups_correctly(self, factory):
        """Debería agrupar errores por tipo correctamente."""
        # Arrange
        sources = [RssFeedId(f"source-{i}") for i in range(5)]
        session = factory.create_multi_source(sources=sources)

        # Fallar con diferentes tipos de error
        session.start_source_fetch(sources[0])
        session.fail_source_fetch(sources[0], "TIMEOUT", "Timeout 1")

        session.start_source_fetch(sources[1])
        session.fail_source_fetch(sources[1], "TIMEOUT", "Timeout 2")

        session.start_source_fetch(sources[2])
        session.fail_source_fetch(sources[2], "HTTP_ERROR", "404 Not Found")

        # Act
        errors_by_type = session.get_errors_by_type()

        # Assert
        assert "TIMEOUT" in errors_by_type
        assert "HTTP_ERROR" in errors_by_type
        assert len(errors_by_type["TIMEOUT"]) == 2
        assert len(errors_by_type["HTTP_ERROR"]) == 1

    def test_complete_session_emits_completed_event(self, factory):
        """Debería emitir evento ScrapingCompleted al completar todos."""
        # Arrange
        sources = [RssFeedId("source-1")]
        session = factory.create_multi_source(sources=sources)

        # Limpiar evento de inicio
        session.mark_events_as_committed()

        # Act
        session.start_source_fetch(sources[0])
        session.complete_source_fetch(sources[0], articles_discovered=5)

        # Assert
        events = session.get_uncommitted_events()
        completed_events = [e for e in events if isinstance(e, ScrapingCompleted)]
        assert len(completed_events) == 1
        assert completed_events[0].final_status == "completed"
        assert completed_events[0].sources_successful == 1

    def test_complete_session_with_failures_marks_as_partial(self, factory):
        """Debería marcar como 'partial' si hay éxitos y fallos."""
        # Arrange
        sources = [RssFeedId("source-1"), RssFeedId("source-2")]
        session = factory.create_multi_source(sources=sources)
        session.mark_events_as_committed()

        # Act
        session.start_source_fetch(sources[0])
        session.complete_source_fetch(sources[0])

        session.start_source_fetch(sources[1])
        session.fail_source_fetch(sources[1], "ERROR", "Test error")

        # Assert
        events = session.get_uncommitted_events()
        completed_events = [e for e in events if isinstance(e, ScrapingCompleted)]
        assert len(completed_events) == 1
        assert completed_events[0].final_status == "partial"

    def test_complete_session_all_failed_marks_as_failed(self, factory):
        """Debería marcar como 'failed' si todos fallaron."""
        # Arrange
        sources = [RssFeedId("source-1")]
        session = factory.create_multi_source(sources=sources)
        session.mark_events_as_committed()

        # Act
        session.start_source_fetch(sources[0])
        session.fail_source_fetch(sources[0], "ERROR", "Test error")

        # Assert
        events = session.get_uncommitted_events()
        completed_events = [e for e in events if isinstance(e, ScrapingCompleted)]
        assert len(completed_events) == 1
        assert completed_events[0].final_status == "failed"

    def test_cancel_session_moves_in_progress_to_failed(self, factory):
        """Debería mover sources en progreso a failed al cancelar."""
        # Arrange
        sources = [RssFeedId("source-1"), RssFeedId("source-2")]
        session = factory.create_multi_source(sources=sources)

        session.start_source_fetch(sources[0])
        session.start_source_fetch(sources[1])

        # Act
        session.cancel_session("User cancelled")

        # Assert
        assert len(session.sources_in_progress) == 0
        assert len(session.sources_failed) == 2
        assert session.cancelled_reason == "User cancelled"
        assert session.completed_at is not None

    def test_cancel_session_emits_failed_event(self, factory):
        """Debería emitir evento ScrapingFailed al cancelar."""
        # Arrange
        sources = [RssFeedId("source-1")]
        session = factory.create_multi_source(sources=sources)
        session.start_source_fetch(sources[0])
        session.mark_events_as_committed()

        # Act
        session.cancel_session("Test cancellation")

        # Assert
        events = session.get_uncommitted_events()
        failed_events = [e for e in events if isinstance(e, ScrapingFailed)]
        assert len(failed_events) >= 1
        assert any(e.error_type == "CANCELLED" for e in failed_events)

    def test_cancel_already_completed_session_raises_error(self, factory):
        """Debería lanzar ValueError si se intenta cancelar sesión completada."""
        # Arrange
        sources = [RssFeedId("source-1")]
        session = factory.create_multi_source(sources=sources)
        session.start_source_fetch(sources[0])
        session.complete_source_fetch(sources[0])

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            session.cancel_session("Too late")

        assert "ya completada" in str(exc_info.value)

    def test_average_response_time_calculated_correctly(self, factory):
        """Debería calcular tiempo de respuesta promedio correctamente."""
        # Arrange
        sources = [RssFeedId(f"source-{i}") for i in range(3)]
        session = factory.create_multi_source(sources=sources)

        # Act
        session.start_source_fetch(sources[0])
        session.complete_source_fetch(sources[0], response_time_ms=100.0)

        session.start_source_fetch(sources[1])
        session.complete_source_fetch(sources[1], response_time_ms=200.0)

        session.start_source_fetch(sources[2])
        session.complete_source_fetch(sources[2], response_time_ms=300.0)

        # Assert
        # Promedio: (100 + 200 + 300) / 3 = 200
        assert session.metrics.average_response_time_ms == 200.0
