"""Tests para FetchSessionModel - Mapeo entre aggregate y modelo ORM."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from src.rss.feed.domain.value_objects import RssFeedId
from src.scraping.domain.aggregates import Scraping
from src.scraping.domain.factories import ScrapingFactory
from src.scraping.domain.value_objects import (
    ScrapingConfig,
    ScrapingError,
    ScrapingIdentity,
    ScrapingMetrics,
    ScrapingStatus,
)
from src.scraping.infra.persistence.models import ScrapingModel as FetchSessionModel

# Alias para compatibilidad
ScrapingId = ScrapingIdentity
FetchSessionId = ScrapingIdentity


class TestFetchSessionModelMapping:
    """Tests para mapeo entre FetchSession aggregate y FetchSessionModel."""

    def test_update_from_fetch_session_domain_maps_all_core_fields(self):
        """Debería mapear todos los campos core del aggregate al modelo."""
        # Arrange
        scraping_id = ScrapingId.generate()
        sources = [SourceId.generate(), SourceId.generate(), SourceId.generate()]

        config = ScrapingConfig(max_concurrent_scrapes=10)
        fetch_session = ScrapingFactory().create_multi_source(
            sources=sources,
            config=config,
            id=str(fetch_session_id),
        )

        # Simular progreso
        fetch_session.start_source_fetch(sources[0])
        fetch_session.complete_source_fetch(
            sources[0],
            articles_discovered=5,
            articles_new=3,
            articles_updated=2,
            processing_time_seconds=10.5,
        )

        model = FetchSessionModel(id=fetch_session_id.value)

        # Act
        model.update_from_fetch_session_domain(fetch_session)

        # Assert - Core fields
        assert model.status == str(fetch_session.status)
        assert model.cancelled_reason == fetch_session._cancelled_reason

    def test_update_from_fetch_session_domain_maps_sources_tracking(self):
        """Debería mapear correctamente el tracking de sources."""
        # Arrange
        scraping_id = ScrapingId.generate()
        sources = [SourceId.generate() for _ in range(5)]

        fetch_session = ScrapingFactory().create_multi_source(
            sources=sources,
            id=fetch_session_id,
        )

        # Simular diferentes estados de sources
        fetch_session.start_source_fetch(sources[0])  # En progreso
        fetch_session.start_source_fetch(sources[1])
        fetch_session.complete_source_fetch(sources[1], 10, 5, 5, 15.0)  # Completado
        fetch_session.start_source_fetch(sources[2])
        fetch_session.fail_source_fetch(
            sources[2], "timeout", "Connection timeout"
        )  # Fallido

        model = FetchSessionModel(id=fetch_session_id.value)

        # Act
        model.update_from_fetch_session_domain(fetch_session)

        # Assert - Sources tracking
        assert len(model.sources_to_fetch) == 5
        assert model.sources_count == 5
        assert len(model.sources_in_progress) == 1  # Solo sources[0]
        assert str(sources[0]) in model.sources_in_progress
        assert len(model.sources_completed) == 1  # Solo sources[1]
        assert str(sources[1]) in model.sources_completed
        assert len(model.sources_failed) == 1  # Solo sources[2]
        assert str(sources[2]) in model.sources_failed

    def test_update_from_fetch_session_domain_maps_configuration(self):
        """Debería mapear correctamente la configuración."""
        # Arrange
        scraping_id = ScrapingId.generate()
        sources = [SourceId.generate()]
        timeout_config = {"connect": 5, "read": 30}

        config = ScrapingConfig(
            max_concurrent_scrapes=15,
            timeout_seconds=60,
            timeout_config=timeout_config,
        )
        fetch_session = ScrapingFactory().create_multi_source(
            sources=sources,
            config=config,
            id=str(fetch_session_id),
        )

        model = FetchSessionModel(id=fetch_session_id.value)

        # Act
        model.update_from_fetch_session_domain(fetch_session)

        # Assert - Configuration
        assert model.max_concurrent_fetches == 15
        assert model.timeout_seconds == 60
        assert model.timeout_config == timeout_config

    def test_update_from_fetch_session_domain_maps_metrics(self):
        """Debería mapear correctamente todas las métricas."""
        # Arrange
        scraping_id = ScrapingId.generate()
        sources = [SourceId.generate(), SourceId.generate()]

        fetch_session = ScrapingFactory().create_multi_source(
            sources=sources,
            id=fetch_session_id,
        )

        # Simular procesamiento con métricas
        fetch_session.start_source_fetch(sources[0])
        fetch_session.complete_source_fetch(
            sources[0],
            articles_discovered=20,
            articles_new=15,
            articles_updated=5,
            processing_time_seconds=25.5,
        )

        fetch_session.start_source_fetch(sources[1])
        fetch_session.complete_source_fetch(
            sources[1],
            articles_discovered=10,
            articles_new=8,
            articles_updated=2,
            processing_time_seconds=15.0,
        )

        model = FetchSessionModel(id=fetch_session_id.value)

        # Act
        model.update_from_fetch_session_domain(fetch_session)

        # Assert - Metrics
        assert model.articles_discovered == 30  # 20 + 10
        assert model.articles_new == 23  # 15 + 8
        assert model.articles_updated == 7  # 5 + 2
        assert model.sources_successful == 2
        assert model.sources_failed_count == 0
        assert model.total_processing_time_seconds == 40.5  # 25.5 + 15.0
        assert model.average_response_time_ms > 0

    def test_update_from_fetch_session_domain_maps_errors(self):
        """Debería mapear correctamente los errores."""
        # Arrange
        scraping_id = ScrapingId.generate()
        sources = [SourceId.generate(), SourceId.generate(), SourceId.generate()]

        fetch_session = ScrapingFactory().create_multi_source(
            sources=sources,
            id=fetch_session_id,
        )

        # Simular errores
        fetch_session.start_source_fetch(sources[0])
        fetch_session.fail_source_fetch(sources[0], "timeout", "Connection timeout")

        fetch_session.start_source_fetch(sources[1])
        fetch_session.fail_source_fetch(sources[1], "timeout", "Read timeout")

        fetch_session.start_source_fetch(sources[2])
        fetch_session.fail_source_fetch(
            sources[2], "http_error", "404 Not Found", http_status_code=404
        )

        model = FetchSessionModel(id=fetch_session_id.value)

        # Act
        model.update_from_fetch_session_domain(fetch_session)

        # Assert - Errors
        assert model.error_count == 3
        assert len(model.fetch_errors) == 3
        assert model.errors_by_type["timeout"] == 2
        assert model.errors_by_type["http_error"] == 1
        assert model.last_error_message == "404 Not Found"

        # Verificar estructura de errores
        error_dict = model.fetch_errors[0]
        assert "source_id" in error_dict
        assert "error_type" in error_dict
        assert "error_message" in error_dict
        assert "occurred_at" in error_dict
        assert "is_recoverable" in error_dict

    def test_update_from_fetch_session_domain_maps_timestamps(self):
        """Debería mapear correctamente los timestamps."""
        # Arrange
        scraping_id = ScrapingId.generate()
        sources = [SourceId.generate()]

        fetch_session = ScrapingFactory().create_multi_source(
            sources=sources,
            id=fetch_session_id,
        )

        # Simular inicio y completado
        fetch_session.start_source_fetch(sources[0])
        fetch_session.complete_source_fetch(sources[0], 5, 3, 2, 10.0)

        model = FetchSessionModel(id=fetch_session_id.value)

        # Act
        model.update_from_fetch_session_domain(fetch_session)

        # Assert - Timestamps
        assert model.started_at is not None
        assert model.completed_at is not None
        assert model.updated_at is not None
        assert model.completed_at >= model.started_at

    def test_update_from_fetch_session_domain_handles_empty_errors(self):
        """Debería manejar correctamente cuando no hay errores."""
        # Arrange
        scraping_id = ScrapingId.generate()
        sources = [SourceId.generate()]

        fetch_session = ScrapingFactory().create_multi_source(
            sources=sources,
            id=fetch_session_id,
        )

        # Completar sin errores
        fetch_session.start_source_fetch(sources[0])
        fetch_session.complete_source_fetch(sources[0], 10, 5, 5, 15.0)

        model = FetchSessionModel(id=fetch_session_id.value)

        # Act
        model.update_from_fetch_session_domain(fetch_session)

        # Assert - No errors
        assert model.error_count == 0
        assert model.fetch_errors == []
        assert model.errors_by_type == {}
        assert model.last_error_message is None

    def test_update_from_fetch_session_domain_updates_version(self):
        """Debería actualizar la versión del modelo."""
        # Arrange
        scraping_id = ScrapingId.generate()
        sources = [SourceId.generate()]

        fetch_session = ScrapingFactory().create_multi_source(
            sources=sources,
            id=fetch_session_id,
        )

        model = FetchSessionModel(id=fetch_session_id.value)
        initial_version = model.version

        # Act
        model.update_from_fetch_session_domain(fetch_session)

        # Assert - Version incremented
        assert model.version == initial_version + 1


class TestFetchSessionModelReconstruction:
    """Tests para reconstrucción del aggregate desde el modelo."""

    def test_to_fetch_session_domain_reconstructs_correctly(self):
        """Debería reconstruir el aggregate correctamente desde el modelo."""
        # Arrange
        from src.scraping.domain.factories import ScrapingFactory

        fetch_session_id = FetchSessionId.create_new()
        sources = [SourceId.generate(), SourceId.generate()]

        model = FetchSessionModel(
            id=fetch_session_id.value,
            status="running",
            max_concurrent_fetches=10,
            timeout_seconds=60,
            timeout_config={"connect": 5},
            sources_to_fetch=[str(s) for s in sources],
            sources_count=2,
            sources_in_progress=[str(sources[0])],
            sources_completed=[],
            sources_failed=[],
            articles_discovered=15,
            articles_new=10,
            articles_updated=5,
            sources_successful=0,
            sources_failed_count=0,
            total_processing_time_seconds=20.5,
            average_response_time_ms=150.0,
            error_count=0,
            errors_by_type={},
            fetch_errors=[],
            started_at=datetime.now(timezone.utc),
            completed_at=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        factory = ScrapingFactory()

        # Act
        fetch_session = model.to_fetch_session_domain(factory)

        # Assert - Core fields
        assert str(fetch_session.id) == str(fetch_session_id)
        assert str(fetch_session.status) == "running"

        # Assert - Sources tracking
        assert len(fetch_session.sources_to_fetch) == 2
        assert len(fetch_session._sources_in_progress) == 1
        assert len(fetch_session._sources_completed) == 0
        assert len(fetch_session._sources_failed) == 0

        # Assert - Configuration
        assert fetch_session._config.max_concurrent_fetches == 10
        assert fetch_session._config.timeout_seconds == 60

        # Assert - Metrics
        assert fetch_session._metrics.articles_discovered == 15
        assert fetch_session._metrics.articles_new == 10
        assert fetch_session._metrics.articles_updated == 5

    def test_to_fetch_session_domain_reconstructs_with_errors(self):
        """Debería reconstruir correctamente incluyendo errores."""
        # Arrange
        from src.scraping.domain.factories import ScrapingFactory

        fetch_session_id = FetchSessionId.create_new()
        source_id = SourceId.generate()

        error_data = {
            "source_id": str(source_id),
            "error_type": "timeout",
            "error_message": "Connection timeout",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "is_recoverable": True,
            "http_status_code": None,
        }

        model = FetchSessionModel(
            id=fetch_session_id.value,
            status="failed",
            sources_to_fetch=[str(source_id)],
            sources_count=1,
            sources_in_progress=[],
            sources_completed=[],
            sources_failed=[str(source_id)],
            error_count=1,
            errors_by_type={"timeout": 1},
            fetch_errors=[error_data],
            last_error_message="Connection timeout",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        factory = ScrapingFactory()

        # Act
        fetch_session = model.to_fetch_session_domain(factory)

        # Assert - Errors reconstructed
        assert len(fetch_session._errors) == 1
        error = fetch_session._errors[0]
        assert str(error.source_id) == str(source_id)
        assert error.error_type == "timeout"
        assert error.error_message == "Connection timeout"
        assert error.is_recoverable is True


class TestFetchSessionModelHelpers:
    """Tests para métodos helper del modelo."""

    def test_is_active_returns_true_for_pending(self):
        """Debería retornar True para sesiones pending."""
        model = FetchSessionModel(
            id=uuid4(),
            status="pending",
        )
        assert model.is_active() is True

    def test_is_active_returns_true_for_running(self):
        """Debería retornar True para sesiones running."""
        model = FetchSessionModel(
            id=uuid4(),
            status="running",
        )
        assert model.is_active() is True

    def test_is_active_returns_false_for_completed(self):
        """Debería retornar False para sesiones completed."""
        model = FetchSessionModel(
            id=uuid4(),
            status="completed",
        )
        assert model.is_active() is False

    def test_is_completed_returns_true_for_completed(self):
        """Debería retornar True para sesiones completed."""
        model = FetchSessionModel(
            id=uuid4(),
            status="completed",
        )
        assert model.is_completed() is True

    def test_is_completed_returns_true_for_failed(self):
        """Debería retornar True para sesiones failed."""
        model = FetchSessionModel(
            id=uuid4(),
            status="failed",
        )
        assert model.is_completed() is True

    def test_calculate_progress_percentage_returns_correct_value(self):
        """Debería calcular correctamente el porcentaje de progreso."""
        model = FetchSessionModel(
            id=uuid4(),
            sources_count=10,
            sources_completed=["s1", "s2", "s3"],
            sources_failed=["s4", "s5"],
        )

        # 5 completados (3 + 2) de 10 = 50%
        assert model.calculate_progress_percentage() == 50.0

    def test_calculate_progress_percentage_handles_zero_sources(self):
        """Debería manejar correctamente cuando no hay sources."""
        model = FetchSessionModel(
            id=uuid4(),
            sources_count=0,
        )
        assert model.calculate_progress_percentage() == 0.0

    def test_calculate_success_rate_returns_correct_value(self):
        """Debería calcular correctamente la tasa de éxito."""
        model = FetchSessionModel(
            id=uuid4(),
            sources_completed=["s1", "s2", "s3", "s4"],
            sources_failed=["s5"],
        )

        # 4 exitosos de 5 completados = 80%
        assert model.calculate_success_rate() == 80.0

    def test_calculate_success_rate_handles_no_completed(self):
        """Debería manejar correctamente cuando no hay sources completados."""
        model = FetchSessionModel(
            id=uuid4(),
            sources_completed=[],
            sources_failed=[],
        )
        assert model.calculate_success_rate() == 0.0

    def test_get_duration_seconds_returns_correct_value(self):
        """Debería calcular correctamente la duración."""
        started = datetime.now(timezone.utc)
        completed = started + timedelta(seconds=120)

        model = FetchSessionModel(
            id=uuid4(),
            started_at=started,
            completed_at=completed,
        )

        duration = model.get_duration_seconds()
        assert duration is not None
        assert 119 <= duration <= 121  # Permitir pequeña variación

    def test_get_duration_seconds_returns_none_when_not_started(self):
        """Debería retornar None cuando no ha iniciado."""
        model = FetchSessionModel(
            id=uuid4(),
            started_at=None,
        )
        assert model.get_duration_seconds() is None
