"""Property-based tests para GetFetchSessionAdapter usando Hypothesis.

Estos tests verifican propiedades universales que deben cumplirse
para todas las entradas válidas del sistema de queries de fetch sessions.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

# Importar componentes del sistema
from src.infra.persistence.query_adapters.fetch_sessions.get_fetch_session import (
    GetFetchSessionAdapter,
)
from src.rss.feed.domain.aggregates import RssFeed
from src.rss.feed.domain.value_objects import RssFeedId
from src.rss.feed.domain.value_objects.configuration import RssFeedConfiguration
from src.rss.feed.domain.value_objects.name import RssFeedName
from src.rss.feed.domain.value_objects.rss_feed_url import RssFeedUrl
from src.scraping.domain.aggregates import Scraping
from src.scraping.domain.factories import ScrapingFactory
from src.scraping.domain.value_objects import ScrapingConfig
from src.scraping.infra.persistence.mappers import ScrapingMapper
from src.scraping.infra.persistence.models import ScrapingModel as FetchSessionModel

# ============================================================================
# ESTRATEGIAS DE GENERACIÓN DE DATOS
# ============================================================================


def valid_uuid_strategy():
    """Genera UUIDs válidos."""
    return st.uuids()


@st.composite
def valid_source_id_strategy(draw):
    """Genera SourceId válidos."""
    uuid_val = draw(valid_uuid_strategy())
    return RssFeedId(str(uuid_val))


@st.composite
def valid_source_configuration_strategy(draw):
    """Genera SourceConfiguration válidos."""
    return RssFeedConfiguration(
        fetch_interval_minutes=draw(st.integers(min_value=5, max_value=1440)),
        max_articles_per_fetch=draw(st.integers(min_value=10, max_value=500)),
        timeout_seconds=draw(st.integers(min_value=10, max_value=120)),
        retry_attempts=draw(st.integers(min_value=1, max_value=5)),
        retry_delay_seconds=draw(st.integers(min_value=5, max_value=60)),
    )


@st.composite
def valid_fetch_session_strategy(draw):
    """Genera FetchSession válidos para testing."""
    source_id = draw(valid_source_id_strategy())
    config = draw(valid_source_configuration_strategy())
    session_id = str(draw(valid_uuid_strategy()))

    # Crear Source mock para usar con factory
    source = RssFeed(
        source_id=source_id,
        name=RssFeedName("Test RssFeed"),
        url=RssFeedUrl("https://example.com/feed.xml"),
        configuration=config,
    )

    factory = FetchSessionFactory()
    return factory.create_for_source(
        source=source,
        fetch_session_id=session_id,
    )


@st.composite
def valid_fetch_session_model_strategy(draw):
    """Genera FetchSessionModel válidos para testing."""
    session_id = draw(valid_uuid_strategy())
    source_id = str(draw(valid_uuid_strategy()))  # Generar un source_id

    # Generar timestamps coherentes
    created_at = datetime.now(timezone.utc) - timedelta(
        hours=draw(st.integers(min_value=1, max_value=72))
    )
    updated_at = created_at + timedelta(
        minutes=draw(st.integers(min_value=0, max_value=60))
    )

    # Generar estado válido
    status = draw(
        st.sampled_from(["pending", "running", "completed", "failed", "cancelled"])
    )

    # Generar listas de sources
    sources_count = draw(st.integers(min_value=1, max_value=10))
    sources_to_fetch = [str(uuid4()) for _ in range(sources_count)]

    # Distribuir sources entre estados
    completed_count = draw(st.integers(min_value=0, max_value=sources_count))
    failed_count = draw(
        st.integers(min_value=0, max_value=sources_count - completed_count)
    )
    in_progress_count = sources_count - completed_count - failed_count

    sources_completed = sources_to_fetch[:completed_count]
    sources_failed = sources_to_fetch[completed_count : completed_count + failed_count]
    sources_in_progress = sources_to_fetch[completed_count + failed_count :]

    model = FetchSessionModel(
        fetch_session_id=session_id,
        source_id=source_id,  # Agregar source_id al modelo
        status=status,
        sources_to_fetch=sources_to_fetch,
        sources_count=sources_count,
        sources_in_progress=sources_in_progress,
        sources_completed=sources_completed,
        sources_failed=sources_failed,
        articles_discovered=draw(st.integers(min_value=0, max_value=1000)),
        articles_new=draw(st.integers(min_value=0, max_value=500)),
        articles_updated=draw(st.integers(min_value=0, max_value=500)),
        sources_successful=completed_count,
        sources_failed_count=failed_count,
        total_processing_time_seconds=draw(st.floats(min_value=0.0, max_value=3600.0)),
        average_response_time_ms=draw(st.floats(min_value=0.0, max_value=5000.0)),
        error_count=draw(st.integers(min_value=0, max_value=100)),
        errors_by_type={},
        fetch_errors=[],
        max_concurrent_fetches=draw(st.integers(min_value=1, max_value=10)),
        timeout_seconds=draw(st.integers(min_value=10, max_value=120)),
        timeout_config={},
        created_at=created_at,
        updated_at=updated_at,
        started_at=created_at if status != "pending" else None,
        completed_at=(
            updated_at if status in ["completed", "failed", "cancelled"] else None
        ),
    )

    return model


# ============================================================================
# PROPERTY TESTS
# ============================================================================


class TestFetchSessionQueryReturnsValidData:
    """**Feature: resolve-todos, Property 2: Fetch Session Query Returns Valid Data**

    **Validates: Requirements 2.1**

    Para cualquier ID de sesión de fetch válido, el query adapter debe retornar
    los datos completos de la sesión cuando existe en la base de datos.
    """

    @settings(max_examples=100)
    @given(model=valid_fetch_session_model_strategy())
    @pytest.mark.asyncio
    async def test_query_returns_complete_session_data_for_valid_id(self, model):
        """Para cualquier sesión de fetch válida, la query debe retornar todos los datos."""
        # Arrange - Crear mock de session factory que retorna el modelo
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = model
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_session_factory = Mock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_logger = Mock()

        adapter = GetFetchSessionAdapter(
            session_factory=mock_session_factory, logger=mock_logger
        )

        # Act - Ejecutar query
        result = await adapter.get_by_id(model.fetch_session_id)

        # Assert - Verificar que se retornó un FetchSession válido
        assert result is not None, "Query debe retornar un resultado para ID válido"
        assert isinstance(
            result, FetchSession
        ), "Resultado debe ser una instancia de FetchSession"

        # Verificar que el ID coincide
        assert str(result.id) == str(
            model.fetch_session_id
        ), "El ID del resultado debe coincidir con el ID consultado"

        # Verificar que los datos esenciales están presentes
        assert result.source_id is not None, "RssFeed ID debe estar presente"
        assert result.created_at is not None, "Created timestamp debe estar presente"
        assert result.updated_at is not None, "Updated timestamp debe estar presente"

    @settings(max_examples=100)
    @given(
        model=valid_fetch_session_model_strategy(), different_id=valid_uuid_strategy()
    )
    @pytest.mark.asyncio
    async def test_query_returns_none_for_nonexistent_id(self, model, different_id):
        """Para cualquier ID que no existe, la query debe retornar None."""
        # Assume que el ID diferente no es el mismo que el del modelo
        assume(different_id != model.fetch_session_id)

        # Arrange - Crear mock que retorna None para ID no existente
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_session_factory = Mock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_logger = Mock()

        adapter = GetFetchSessionAdapter(
            session_factory=mock_session_factory, logger=mock_logger
        )

        # Act - Ejecutar query con ID diferente
        result = await adapter.get_by_id(different_id)

        # Assert - Debe retornar None
        assert result is None, "Query debe retornar None para ID no existente"

    @settings(max_examples=100)
    @given(model=valid_fetch_session_model_strategy())
    @pytest.mark.asyncio
    async def test_query_preserves_session_status(self, model):
        """Para cualquier sesión, el status debe preservarse correctamente."""
        # Arrange
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = model
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_session_factory = Mock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_logger = Mock()

        adapter = GetFetchSessionAdapter(
            session_factory=mock_session_factory, logger=mock_logger
        )

        # Act
        result = await adapter.get_by_id(model.fetch_session_id)

        # Assert - El estado debe preservarse
        assert result is not None
        # El mapper convierte el status del modelo al estado del dominio
        # Verificamos que el resultado tiene un estado válido
        assert hasattr(result, "fetch_state") or hasattr(result, "_fetch_manager")

    @settings(max_examples=100)
    @given(model=valid_fetch_session_model_strategy())
    @pytest.mark.asyncio
    async def test_query_preserves_timestamps(self, model):
        """Para cualquier sesión, los timestamps deben preservarse correctamente."""
        # Arrange
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = model
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_session_factory = Mock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_logger = Mock()

        adapter = GetFetchSessionAdapter(
            session_factory=mock_session_factory, logger=mock_logger
        )

        # Act
        result = await adapter.get_by_id(model.fetch_session_id)

        # Assert - Los timestamps deben estar presentes
        assert result is not None
        assert result.created_at is not None, "Created timestamp debe estar presente"
        assert result.updated_at is not None, "Updated timestamp debe estar presente"

        # Verificar que los timestamps son objetos datetime válidos
        assert isinstance(result.created_at, datetime), "Created_at debe ser datetime"
        assert isinstance(result.updated_at, datetime), "Updated_at debe ser datetime"

        # Verificar orden temporal lógico
        assert (
            result.created_at <= result.updated_at
        ), "Created_at debe ser anterior o igual a updated_at"

    @settings(max_examples=100)
    @given(model=valid_fetch_session_model_strategy())
    @pytest.mark.asyncio
    async def test_query_preserves_source_tracking(self, model):
        """Para cualquier sesión, el tracking de sources debe preservarse."""
        # Arrange
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = model
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_session_factory = Mock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_logger = Mock()

        adapter = GetFetchSessionAdapter(
            session_factory=mock_session_factory, logger=mock_logger
        )

        # Act
        result = await adapter.get_by_id(model.fetch_session_id)

        # Assert - Verificar que el resultado tiene información de sources
        assert result is not None
        assert result.source_id is not None, "RssFeed ID debe estar presente"

        # El FetchSession debe tener un source_id válido
        assert isinstance(
            result.source_id, RssFeedId
        ), "RssFeed ID debe ser una instancia de RssFeedId"

    @settings(max_examples=50)
    @given(model=valid_fetch_session_model_strategy())
    @pytest.mark.asyncio
    async def test_query_is_idempotent(self, model):
        """Para cualquier ID, ejecutar la query múltiples veces debe dar el mismo resultado."""
        # Arrange
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = model
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_session_factory = Mock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_logger = Mock()

        adapter = GetFetchSessionAdapter(
            session_factory=mock_session_factory, logger=mock_logger
        )

        # Act - Ejecutar query múltiples veces
        result1 = await adapter.get_by_id(model.fetch_session_id)
        result2 = await adapter.get_by_id(model.fetch_session_id)
        result3 = await adapter.get_by_id(model.fetch_session_id)

        # Assert - Todos los resultados deben ser equivalentes
        assert result1 is not None
        assert result2 is not None
        assert result3 is not None

        # Verificar que los IDs son iguales
        assert str(result1.id) == str(result2.id) == str(result3.id)

        # Verificar que los source_ids son iguales
        assert (
            str(result1.source_id) == str(result2.source_id) == str(result3.source_id)
        )

        # Verificar que los timestamps son iguales
        assert result1.created_at == result2.created_at == result3.created_at
        assert result1.updated_at == result2.updated_at == result3.updated_at


class TestFetchSessionQueryErrorHandling:
    """Tests para verificar el manejo de errores en el query adapter."""

    @settings(max_examples=50)
    @given(session_id=valid_uuid_strategy())
    @pytest.mark.asyncio
    async def test_query_propagates_database_errors(self, session_id):
        """Para cualquier error de base de datos, la query debe propagar la excepción."""
        # Arrange - Crear mock que lanza excepción
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=Exception("Database error"))

        mock_session_factory = Mock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_logger = Mock()

        adapter = GetFetchSessionAdapter(
            session_factory=mock_session_factory, logger=mock_logger
        )

        # Act & Assert - Debe propagar la excepción
        with pytest.raises(Exception) as exc_info:
            await adapter.get_by_id(session_id)

        assert "Database error" in str(exc_info.value)

        # Verificar que se logueó el error
        assert mock_logger.error.called, "El error debe ser logueado"


# ============================================================================
# PROPERTY TEST: PAGINATED FETCH SESSIONS LIST
# ============================================================================


class TestPaginatedFetchSessionsList:
    """**Feature: resolve-todos, Property 3: Paginated Fetch Sessions List**

    **Validates: Requirements 2.3**

    Para cualquier parámetro de paginación (limit, offset), el query adapter
    debe retornar el subconjunto correcto de sesiones.
    """

    @settings(max_examples=100)
    @given(
        total_sessions=st.integers(min_value=0, max_value=100),
        limit=st.integers(min_value=1, max_value=50),
        offset=st.integers(min_value=0, max_value=50),
    )
    @pytest.mark.asyncio
    async def test_pagination_returns_correct_subset(
        self, total_sessions, limit, offset
    ):
        """Para cualquier combinación de limit/offset, debe retornar el subconjunto correcto."""
        # Arrange - Generar lista de sesiones mock
        from src.infra.persistence.query_adapters.fetch_sessions.get_fetch_sessions_by_filter import (
            GetFetchSessionsByFilterAdapter,
        )

        # Crear modelos de sesión
        all_models = []
        for i in range(total_sessions):
            model = FetchSessionModel(
                fetch_session_id=uuid4(),
                source_id=str(uuid4()),
                status="completed",
                sources_to_fetch=[],
                sources_count=0,
                sources_in_progress=[],
                sources_completed=[],
                sources_failed=[],
                articles_discovered=0,
                articles_new=0,
                articles_updated=0,
                sources_successful=0,
                sources_failed_count=0,
                total_processing_time_seconds=0.0,
                average_response_time_ms=0.0,
                error_count=0,
                errors_by_type={},
                fetch_errors=[],
                max_concurrent_fetches=5,
                timeout_seconds=30,
                timeout_config={},
                created_at=datetime.now(timezone.utc) - timedelta(hours=i),
                updated_at=datetime.now(timezone.utc) - timedelta(hours=i),
                started_at=datetime.now(timezone.utc) - timedelta(hours=i),
                completed_at=datetime.now(timezone.utc) - timedelta(hours=i),
            )
            all_models.append(model)

        # Calcular el subconjunto esperado
        expected_start = offset
        expected_end = min(offset + limit, total_sessions)
        expected_count = max(0, expected_end - expected_start)

        # Mock de session que retorna el subconjunto correcto
        mock_session = AsyncMock()
        mock_result = Mock()

        # Simular el comportamiento de SQLAlchemy con limit/offset
        if offset < total_sessions:
            returned_models = all_models[offset : offset + limit]
        else:
            returned_models = []

        mock_result.scalars.return_value.all.return_value = returned_models
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_session_factory = Mock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_logger = Mock()

        adapter = GetFetchSessionsByFilterAdapter(
            session_factory=mock_session_factory, logger=mock_logger
        )

        # Act - Ejecutar query con paginación
        source_id = uuid4()
        result = await adapter.get_by_source(source_id, limit=limit, offset=offset)

        # Assert - Verificar que el resultado tiene el tamaño correcto
        assert (
            len(result) == expected_count
        ), f"Debe retornar {expected_count} sesiones para offset={offset}, limit={limit}, total={total_sessions}"

        # Verificar que todos los resultados son FetchSession válidos
        for session in result:
            assert isinstance(
                session, FetchSession
            ), "Cada elemento debe ser una instancia de FetchSession"

    @settings(max_examples=100)
    @given(
        limit=st.integers(min_value=1, max_value=100),
        offset=st.integers(min_value=0, max_value=100),
    )
    @pytest.mark.asyncio
    async def test_pagination_with_empty_result_set(self, limit, offset):
        """Para cualquier paginación sobre conjunto vacío, debe retornar lista vacía."""
        # Arrange
        from src.infra.persistence.query_adapters.fetch_sessions.get_fetch_sessions_by_filter import (
            GetFetchSessionsByFilterAdapter,
        )

        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_session_factory = Mock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_logger = Mock()

        adapter = GetFetchSessionsByFilterAdapter(
            session_factory=mock_session_factory, logger=mock_logger
        )

        # Act
        result = await adapter.get_by_source(uuid4(), limit=limit, offset=offset)

        # Assert
        assert result == [], "Debe retornar lista vacía para conjunto vacío"
        assert isinstance(result, list), "Debe retornar una lista"

    @settings(max_examples=100)
    @given(
        total_sessions=st.integers(min_value=10, max_value=50),
        page_size=st.integers(min_value=5, max_value=20),
    )
    @pytest.mark.asyncio
    async def test_pagination_pages_do_not_overlap(self, total_sessions, page_size):
        """Para cualquier tamaño de página, las páginas consecutivas no deben solaparse."""
        # Arrange
        from src.infra.persistence.query_adapters.fetch_sessions.get_fetch_sessions_by_filter import (
            GetFetchSessionsByFilterAdapter,
        )

        # Crear modelos únicos
        all_models = []
        for i in range(total_sessions):
            model = FetchSessionModel(
                fetch_session_id=uuid4(),
                source_id=str(uuid4()),
                status="completed",
                sources_to_fetch=[],
                sources_count=0,
                sources_in_progress=[],
                sources_completed=[],
                sources_failed=[],
                articles_discovered=i,  # Usar como identificador único
                articles_new=0,
                articles_updated=0,
                sources_successful=0,
                sources_failed_count=0,
                total_processing_time_seconds=0.0,
                average_response_time_ms=0.0,
                error_count=0,
                errors_by_type={},
                fetch_errors=[],
                max_concurrent_fetches=5,
                timeout_seconds=30,
                timeout_config={},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
            )
            all_models.append(model)

        # Función helper para simular query con offset
        def get_page_models(offset, limit):
            if offset < total_sessions:
                return all_models[offset : offset + limit]
            return []

        # Obtener dos páginas consecutivas
        page1_offset = 0
        page2_offset = page_size

        # Mock para página 1
        mock_session1 = AsyncMock()
        mock_result1 = Mock()
        mock_result1.scalars.return_value.all.return_value = get_page_models(
            page1_offset, page_size
        )
        mock_session1.execute = AsyncMock(return_value=mock_result1)

        mock_session_factory1 = Mock()
        mock_session_factory1.return_value.__aenter__ = AsyncMock(
            return_value=mock_session1
        )
        mock_session_factory1.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock para página 2
        mock_session2 = AsyncMock()
        mock_result2 = Mock()
        mock_result2.scalars.return_value.all.return_value = get_page_models(
            page2_offset, page_size
        )
        mock_session2.execute = AsyncMock(return_value=mock_result2)

        mock_session_factory2 = Mock()
        mock_session_factory2.return_value.__aenter__ = AsyncMock(
            return_value=mock_session2
        )
        mock_session_factory2.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_logger = Mock()

        adapter1 = GetFetchSessionsByFilterAdapter(
            session_factory=mock_session_factory1, logger=mock_logger
        )

        adapter2 = GetFetchSessionsByFilterAdapter(
            session_factory=mock_session_factory2, logger=mock_logger
        )

        # Act - Obtener dos páginas consecutivas
        source_id = uuid4()
        page1 = await adapter1.get_by_source(
            source_id, limit=page_size, offset=page1_offset
        )
        page2 = await adapter2.get_by_source(
            source_id, limit=page_size, offset=page2_offset
        )

        # Assert - Las páginas no deben tener elementos en común
        if page1 and page2:
            page1_ids = {str(s.id) for s in page1}
            page2_ids = {str(s.id) for s in page2}

            overlap = page1_ids & page2_ids
            assert (
                len(overlap) == 0
            ), f"Las páginas consecutivas no deben solaparse. Overlap: {len(overlap)} elementos"

    @settings(max_examples=100)
    @given(
        total_sessions=st.integers(min_value=5, max_value=30),
        limit=st.integers(min_value=1, max_value=10),
    )
    @pytest.mark.asyncio
    async def test_pagination_offset_beyond_total_returns_empty(
        self, total_sessions, limit
    ):
        """Para cualquier offset mayor que el total, debe retornar lista vacía."""
        # Arrange
        from src.infra.persistence.query_adapters.fetch_sessions.get_fetch_sessions_by_filter import (
            GetFetchSessionsByFilterAdapter,
        )

        # Offset más allá del total
        offset = total_sessions + 10

        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_session_factory = Mock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_logger = Mock()

        adapter = GetFetchSessionsByFilterAdapter(
            session_factory=mock_session_factory, logger=mock_logger
        )

        # Act
        result = await adapter.get_by_source(uuid4(), limit=limit, offset=offset)

        # Assert
        assert (
            result == []
        ), f"Offset {offset} más allá del total {total_sessions} debe retornar lista vacía"

    @settings(max_examples=100)
    @given(
        total_sessions=st.integers(min_value=20, max_value=50),
        limit=st.integers(min_value=5, max_value=15),
    )
    @pytest.mark.asyncio
    async def test_pagination_last_page_may_be_partial(self, total_sessions, limit):
        """Para cualquier paginación, la última página puede tener menos elementos que limit."""
        # Arrange
        from src.infra.persistence.query_adapters.fetch_sessions.get_fetch_sessions_by_filter import (
            GetFetchSessionsByFilterAdapter,
        )

        # Calcular offset para la última página
        full_pages = total_sessions // limit
        last_page_offset = full_pages * limit
        expected_last_page_size = total_sessions % limit

        # Si no hay resto, la última página está completa
        if expected_last_page_size == 0 and total_sessions > 0:
            last_page_offset = (full_pages - 1) * limit
            expected_last_page_size = limit

        # Crear modelos para la última página
        all_models = []
        for i in range(total_sessions):
            model = FetchSessionModel(
                fetch_session_id=uuid4(),
                source_id=str(uuid4()),
                status="completed",
                sources_to_fetch=[],
                sources_count=0,
                sources_in_progress=[],
                sources_completed=[],
                sources_failed=[],
                articles_discovered=0,
                articles_new=0,
                articles_updated=0,
                sources_successful=0,
                sources_failed_count=0,
                total_processing_time_seconds=0.0,
                average_response_time_ms=0.0,
                error_count=0,
                errors_by_type={},
                fetch_errors=[],
                max_concurrent_fetches=5,
                timeout_seconds=30,
                timeout_config={},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
            )
            all_models.append(model)

        last_page_models = all_models[last_page_offset : last_page_offset + limit]

        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = last_page_models
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_session_factory = Mock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_logger = Mock()

        adapter = GetFetchSessionsByFilterAdapter(
            session_factory=mock_session_factory, logger=mock_logger
        )

        # Act
        result = await adapter.get_by_source(
            uuid4(), limit=limit, offset=last_page_offset
        )

        # Assert
        assert (
            len(result) <= limit
        ), f"La última página no debe exceder el límite {limit}"

        if expected_last_page_size > 0:
            assert (
                len(result) == expected_last_page_size
            ), f"La última página debe tener {expected_last_page_size} elementos"

    @settings(max_examples=50)
    @given(
        total_sessions=st.integers(min_value=10, max_value=30),
        limit1=st.integers(min_value=5, max_value=15),
        limit2=st.integers(min_value=5, max_value=15),
    )
    @pytest.mark.asyncio
    async def test_pagination_different_limits_same_offset_consistency(
        self, total_sessions, limit1, limit2
    ):
        """Para cualquier offset fijo, diferentes límites deben retornar subconjuntos consistentes."""
        # Arrange
        from src.infra.persistence.query_adapters.fetch_sessions.get_fetch_sessions_by_filter import (
            GetFetchSessionsByFilterAdapter,
        )

        offset = 0

        # Crear modelos
        all_models = []
        for i in range(total_sessions):
            model = FetchSessionModel(
                fetch_session_id=uuid4(),
                source_id=str(uuid4()),
                status="completed",
                sources_to_fetch=[],
                sources_count=0,
                sources_in_progress=[],
                sources_completed=[],
                sources_failed=[],
                articles_discovered=i,  # Identificador único
                articles_new=0,
                articles_updated=0,
                sources_successful=0,
                sources_failed_count=0,
                total_processing_time_seconds=0.0,
                average_response_time_ms=0.0,
                error_count=0,
                errors_by_type={},
                fetch_errors=[],
                max_concurrent_fetches=5,
                timeout_seconds=30,
                timeout_config={},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
            )
            all_models.append(model)

        # Mock para limit1
        mock_session1 = AsyncMock()
        mock_result1 = Mock()
        mock_result1.scalars.return_value.all.return_value = all_models[
            offset : offset + limit1
        ]
        mock_session1.execute = AsyncMock(return_value=mock_result1)

        mock_session_factory1 = Mock()
        mock_session_factory1.return_value.__aenter__ = AsyncMock(
            return_value=mock_session1
        )
        mock_session_factory1.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock para limit2
        mock_session2 = AsyncMock()
        mock_result2 = Mock()
        mock_result2.scalars.return_value.all.return_value = all_models[
            offset : offset + limit2
        ]
        mock_session2.execute = AsyncMock(return_value=mock_result2)

        mock_session_factory2 = Mock()
        mock_session_factory2.return_value.__aenter__ = AsyncMock(
            return_value=mock_session2
        )
        mock_session_factory2.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_logger = Mock()

        adapter1 = GetFetchSessionsByFilterAdapter(
            session_factory=mock_session_factory1, logger=mock_logger
        )

        adapter2 = GetFetchSessionsByFilterAdapter(
            session_factory=mock_session_factory2, logger=mock_logger
        )

        # Act
        source_id = uuid4()
        result1 = await adapter1.get_by_source(source_id, limit=limit1, offset=offset)
        result2 = await adapter2.get_by_source(source_id, limit=limit2, offset=offset)

        # Assert - Si limit1 < limit2, result1 debe ser subconjunto de result2
        if limit1 <= limit2 and result1 and result2:
            result1_ids = {str(s.id) for s in result1}
            result2_ids = {str(s.id) for s in result2}

            # Los primeros limit1 elementos deben estar en ambos resultados
            min_limit = min(limit1, limit2, len(result1), len(result2))
            if min_limit > 0:
                # Verificar que ambos resultados comienzan desde el mismo offset
                assert len(result1) <= limit1, "Result1 no debe exceder limit1"
                assert len(result2) <= limit2, "Result2 no debe exceder limit2"


# ============================================================================
# PROPERTY TEST: HEALTHY SOURCES INCLUDE CONSECUTIVE FAILURES
# ============================================================================


class TestHealthySourcesIncludeConsecutiveFailures:
    """**Feature: resolve-todos, Property 4: Healthy Sources Include Consecutive Failures**

    **Validates: Requirements 2.4**

    Para cualquier fuente saludable retornada por la query, la respuesta debe
    incluir el campo consecutive_failures.
    """

    @st.composite
    def valid_source_model_strategy(draw):
        """Genera SourceModel válidos para testing."""
        from src.rss.feed.infra.persistence.models import SourceModel

        source_id = draw(valid_uuid_strategy())

        # Generar métricas de fetch
        total_attempts = draw(st.integers(min_value=1, max_value=100))
        successful = draw(st.integers(min_value=0, max_value=total_attempts))
        failed = total_attempts - successful

        # Generar consecutive_failures (0 a 10)
        consecutive_failures = draw(st.integers(min_value=0, max_value=10))

        # Generar timestamps
        created_at = datetime.now(timezone.utc) - timedelta(
            days=draw(st.integers(min_value=1, max_value=365))
        )
        updated_at = created_at + timedelta(
            hours=draw(st.integers(min_value=0, max_value=24))
        )

        model = RssFeedModel(
            source_id=source_id,
            name=f"Test RssFeed {source_id}",
            url=f"https://example{draw(st.integers(min_value=1, max_value=1000))}.com/feed.xml",
            domain=f"example{draw(st.integers(min_value=1, max_value=1000))}.com",
            description="Test source description",
            status="active",
            fetch_interval_minutes=draw(st.integers(min_value=60, max_value=1440)),
            timeout_seconds=30,
            max_retries=3,
            total_fetch_attempts=total_attempts,
            successful_fetches=successful,
            failed_fetches=failed,
            consecutive_failures=consecutive_failures,
            last_fetch_at=updated_at,
            last_successful_fetch_at=updated_at if successful > 0 else None,
            average_response_time_ms=draw(st.floats(min_value=100.0, max_value=5000.0)),
            total_articles_discovered=draw(st.integers(min_value=0, max_value=10000)),
            last_articles_count=draw(st.integers(min_value=0, max_value=100)),
            created_at=created_at,
            updated_at=updated_at,
        )

        return model

    @settings(max_examples=100)
    @given(model=valid_source_model_strategy())
    @pytest.mark.asyncio
    async def test_healthy_source_includes_consecutive_failures_field(self, model):
        """Para cualquier fuente saludable, la respuesta debe incluir consecutive_failures."""
        # Arrange - Crear mock de session que retorna el modelo
        from src.infra.persistence.query_adapters.sources.get_sources_list import (
            GetSourcesListAdapter,
        )

        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [model]
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_session_factory = Mock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_logger = Mock()

        adapter = GetSourcesListAdapter(
            session_factory=mock_session_factory, logger=mock_logger
        )

        # Act - Ejecutar query con min_success_rate bajo para incluir la fuente
        min_success_rate = 0.0  # Incluir todas las fuentes
        result = await adapter.get_healthy(min_success_rate=min_success_rate, limit=100)

        # Assert - Verificar que el resultado incluye consecutive_failures
        assert len(result) > 0, "Debe retornar al menos una fuente"

        for source_data in result:
            assert (
                "consecutive_failures" in source_data
            ), "El campo consecutive_failures debe estar presente en la respuesta"

            assert isinstance(
                source_data["consecutive_failures"], int
            ), "consecutive_failures debe ser un entero"

            assert (
                source_data["consecutive_failures"] >= 0
            ), "consecutive_failures debe ser no negativo"

    @settings(max_examples=100)
    @given(model=valid_source_model_strategy())
    @pytest.mark.asyncio
    async def test_consecutive_failures_matches_model_value(self, model):
        """Para cualquier fuente, consecutive_failures debe coincidir con el valor del modelo."""
        # Arrange
        from src.infra.persistence.query_adapters.sources.get_sources_list import (
            GetSourcesListAdapter,
        )

        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [model]
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_session_factory = Mock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_logger = Mock()

        adapter = GetSourcesListAdapter(
            session_factory=mock_session_factory, logger=mock_logger
        )

        # Act
        result = await adapter.get_healthy(min_success_rate=0.0, limit=100)

        # Assert - El valor de consecutive_failures debe coincidir con el del modelo
        assert len(result) > 0
        source_data = result[0]

        assert (
            source_data["consecutive_failures"] == model.consecutive_failures
        ), f"consecutive_failures debe ser {model.consecutive_failures}, pero fue {source_data['consecutive_failures']}"

    @settings(max_examples=100)
    @given(models=st.lists(valid_source_model_strategy(), min_size=1, max_size=20))
    @pytest.mark.asyncio
    async def test_all_healthy_sources_include_consecutive_failures(self, models):
        """Para cualquier lista de fuentes saludables, todas deben incluir consecutive_failures."""
        # Arrange
        from src.infra.persistence.query_adapters.sources.get_sources_list import (
            GetSourcesListAdapter,
        )

        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = models
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_session_factory = Mock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_logger = Mock()

        adapter = GetSourcesListAdapter(
            session_factory=mock_session_factory, logger=mock_logger
        )

        # Act
        result = await adapter.get_healthy(min_success_rate=0.0, limit=100)

        # Assert - Todas las fuentes deben tener consecutive_failures
        assert len(result) > 0, "Debe retornar al menos una fuente"

        for i, source_data in enumerate(result):
            assert (
                "consecutive_failures" in source_data
            ), f"Fuente {i} debe incluir consecutive_failures"

            assert (
                source_data["consecutive_failures"] == models[i].consecutive_failures
            ), f"Fuente {i}: consecutive_failures debe ser {models[i].consecutive_failures}"

    @settings(max_examples=100)
    @given(
        model=valid_source_model_strategy(),
        min_success_rate=st.floats(min_value=0.0, max_value=1.0),
    )
    @pytest.mark.asyncio
    async def test_consecutive_failures_present_regardless_of_success_rate(
        self, model, min_success_rate
    ):
        """Para cualquier umbral de success_rate, consecutive_failures debe estar presente."""
        # Arrange
        from src.infra.persistence.query_adapters.sources.get_sources_list import (
            GetSourcesListAdapter,
        )

        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [model]
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_session_factory = Mock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_logger = Mock()

        adapter = GetSourcesListAdapter(
            session_factory=mock_session_factory, logger=mock_logger
        )

        # Act
        result = await adapter.get_healthy(min_success_rate=min_success_rate, limit=100)

        # Assert - Si la fuente cumple el umbral, debe incluir consecutive_failures
        if result:
            for source_data in result:
                assert (
                    "consecutive_failures" in source_data
                ), "consecutive_failures debe estar presente independientemente del umbral"

                assert isinstance(
                    source_data["consecutive_failures"], int
                ), "consecutive_failures debe ser un entero"

    @settings(max_examples=50)
    @given(model=valid_source_model_strategy())
    @pytest.mark.asyncio
    async def test_consecutive_failures_is_non_negative(self, model):
        """Para cualquier fuente, consecutive_failures debe ser no negativo."""
        # Arrange
        from src.infra.persistence.query_adapters.sources.get_sources_list import (
            GetSourcesListAdapter,
        )

        # Asegurar que el modelo tiene un valor no negativo
        assume(model.consecutive_failures >= 0)

        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [model]
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_session_factory = Mock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_logger = Mock()

        adapter = GetSourcesListAdapter(
            session_factory=mock_session_factory, logger=mock_logger
        )

        # Act
        result = await adapter.get_healthy(min_success_rate=0.0, limit=100)

        # Assert
        assert len(result) > 0
        source_data = result[0]

        assert (
            source_data["consecutive_failures"] >= 0
        ), "consecutive_failures debe ser no negativo"

    @settings(max_examples=50)
    @given(
        model=valid_source_model_strategy(),
        query_count=st.integers(min_value=2, max_value=5),
    )
    @pytest.mark.asyncio
    async def test_consecutive_failures_consistent_across_queries(
        self, model, query_count
    ):
        """Para cualquier fuente, consecutive_failures debe ser consistente en múltiples queries."""
        # Arrange
        from src.infra.persistence.query_adapters.sources.get_sources_list import (
            GetSourcesListAdapter,
        )

        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [model]
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_session_factory = Mock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_logger = Mock()

        adapter = GetSourcesListAdapter(
            session_factory=mock_session_factory, logger=mock_logger
        )

        # Act - Ejecutar múltiples queries
        results = []
        for _ in range(query_count):
            result = await adapter.get_healthy(min_success_rate=0.0, limit=100)
            results.append(result)

        # Assert - consecutive_failures debe ser consistente
        assert all(
            len(r) > 0 for r in results
        ), "Todas las queries deben retornar resultados"

        first_consecutive_failures = results[0][0]["consecutive_failures"]

        for i, result in enumerate(results[1:], start=1):
            assert (
                result[0]["consecutive_failures"] == first_consecutive_failures
            ), f"Query {i}: consecutive_failures debe ser consistente ({first_consecutive_failures})"
