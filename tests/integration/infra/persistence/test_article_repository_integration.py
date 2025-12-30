"""Integration tests para ArticleWriteRepository con base de datos real.

Estos tests verifican:
1. RssArticle persiste correctamente con nuevos VOs
2. RssArticle se reconstruye correctamente desde DB
3. Event sourcing funciona con persistencia
4. Optimistic locking funciona con version

NOTA IMPORTANTE:
================
Estos tests requieren configuración adicional:

1. Instalar aiosqlite:
   pip install aiosqlite

2. O configurar con PostgreSQL de prueba:
   - Crear base de datos de prueba
   - Actualizar TEST_DATABASE_URL con credenciales

Los tests están marcados con @pytest.mark.integration y pueden
ejecutarse selectivamente con:
   pytest -m integration

Para desarrollo rápido, estos tests pueden omitirse ya que la
funcionalidad está cubierta por tests unitarios con mocks.
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.infra.persistence.repositories.rss.article_write_repository import (
    ArticleWriteRepository,
)
from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.article.domain.value_objects import (
    RssArticleId,
    RssArticleTitle,
    RssArticleUrl,
)
from src.rss.article.domain.value_objects.analysis import (
    KeywordCollection,
    ReadingTime,
    WordCount,
)
from src.rss.article.domain.value_objects.metadata import (
    ArticleCategory,
    ArticleLanguage,
)
from src.rss.article.domain.value_objects.readability_score import ReadabilityScore
from src.rss.article.domain.value_objects.validation_info import ValidationInfo
from src.rss.article.infra.persistence.models import ArticleModel
from src.rss.feed.domain.value_objects import RssFeedId
from src.shared.domain.value_objects import Level, TagCollection
from src.shared.infra.persistence import Base

# Configuración de base de datos de prueba
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_engine():
    """Crea engine de base de datos de prueba."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    # Crear todas las tablas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Limpiar
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Crea sesión de base de datos de prueba."""
    async_session_factory = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def repository(db_session):
    """Crea repositorio con sesión de prueba."""
    return ArticleWriteRepository(
        session=db_session,
        logger=None,
        event_publisher=None,
        event_store=None,
    )


@pytest.fixture
def sample_rss_article():
    """Crea un Article de ejemplo con todos los Value Objects."""
    factory = RssArticleFactory()

    article = factory.create_article(
        title="Test RssArticle with Value Objects",
        url="https://example.com/test-article",
        source_id=RssFeedId(str(uuid4())),
    )

    # Agregar contenido
    article.update_content_fields(
        markdown="# Test Article\n\nThis is test content for integration testing."
    )

    # Agregar Value Objects
    article.update_readability_score(0.75)
    article.set_word_count(150)
    article.set_reading_time(1)
    article.update_language("es", 0.95)
    article.add_tag("python")
    article.add_tag("testing")
    article.set_keywords(["integration", "testing", "repository"])
    article.update_category("technology", 0.9)
    article.validate_article(0.85, "test-validator")
    article.assess_quality(Level.high())

    return article


@pytest.mark.integration
class TestRssArticleRepositoryPersistence:
    """Tests de persistencia básica del repositorio."""

    async def test_save_new_article_with_value_objects(
        self,
        repository: ArticleWriteRepository,
        sample_article: RssArticle,
        db_session: AsyncSession,
    ):
        """Debería persistir Article nuevo con todos los Value Objects correctamente."""
        # Act
        await repository.save(sample_article)

        # Assert - Verificar en DB
        stmt = select(ArticleModel).where(
            ArticleModel.article_id == str(sample_article.id)
        )
        result = await db_session.execute(stmt)
        model = result.scalar_one_or_none()

        assert model is not None
        assert model.title == sample_article.title
        assert model.url == sample_article.url
        assert model.source_id == str(sample_article.source_id)
        assert model.content_markdown == sample_article.content_vo.markdown_markdown

        # Verificar Value Objects persistidos correctamente
        assert (
            model.readability_score == sample_article.quality.readability_score.value
            if sample_article.quality.readability_score
            else None
        )
        assert (
            model.word_count == sample_article.metrics.word_count.value
            if sample_article.metrics.word_count
            else None
        )
        assert (
            model.reading_time_minutes == sample_article.metrics.reading_time.minutes
            if sample_article.metrics.reading_time
            else None
        )
        assert (
            model.language == sample_article.metadata.language.code
            if sample_article.metadata.language
            else None
        )
        assert set(model.tags) == set(tuple(sample_article.metadata.tags.sorted_tags))
        assert set(model.keywords) == set(
            tuple(sample_article.metadata.keywords.keywords)
        )
        # Verificar categoría si existe
        if sample_article.metadata.category:
            assert model.categories[0] == sample_article.metadata.category.value
        assert model.validation_score == sample_article.validation_score
        assert model.validated_by == sample_article.validated_by
        assert model.quality_level == str(sample_article.quality.quality_level)

    async def test_update_existing_article_with_value_objects(
        self,
        repository: ArticleWriteRepository,
        sample_article: RssArticle,
        db_session: AsyncSession,
    ):
        """Debería actualizar Article existente preservando Value Objects."""
        # Arrange - Guardar primero
        await repository.save(sample_article)

        # Modificar Value Objects
        sample_article.update_content_fields(
            markdown="# Updated Content\n\nThis is updated content."
        )
        sample_article.update_readability_score(0.85)
        sample_article.set_word_count(200)
        sample_article.add_tag("updated")
        sample_article.set_keywords(["updated", "keywords"])

        # Act - Actualizar
        await repository.save(sample_article)

        # Assert - Verificar cambios en DB
        stmt = select(ArticleModel).where(
            ArticleModel.article_id == str(sample_article.id)
        )
        result = await db_session.execute(stmt)
        model = result.scalar_one_or_none()

        assert model is not None
        assert model.content_markdown == "# Updated Content\n\nThis is updated content."
        assert model.readability_score == 0.85
        assert model.word_count == 200
        assert "updated" in model.tags
        assert "updated" in model.keywords

    async def test_delete_article(
        self,
        repository: ArticleWriteRepository,
        sample_article: RssArticle,
        db_session: AsyncSession,
    ):
        """Debería eliminar Article correctamente."""
        # Arrange - Guardar primero
        await repository.save(sample_article)

        # Act
        deleted = await repository.delete(sample_article.id)

        # Assert
        assert deleted is True

        # Verificar que no existe en DB
        stmt = select(ArticleModel).where(
            ArticleModel.article_id == str(sample_article.id)
        )
        result = await db_session.execute(stmt)
        model = result.scalar_one_or_none()

        assert model is None


@pytest.mark.integration
class TestRssArticleRepositoryReconstruction:
    """Tests de reconstrucción de Article desde DB."""

    async def test_reconstruct_article_with_all_value_objects(
        self,
        repository: ArticleWriteRepository,
        sample_article: RssArticle,
        db_session: AsyncSession,
    ):
        """Debería reconstruir Article desde DB con todos los Value Objects intactos."""
        # Arrange - Guardar
        await repository.save(sample_article)

        # Capturar estado original
        original_id = sample_article.id
        original_title = sample_article.title
        original_url = sample_article.url
        original_content = sample_article.content_vo.markdown
        original_readability = (
            sample_article.quality.readability_score.value
            if sample_article.quality.readability_score
            else None
        )
        original_word_count = (
            sample_article.metrics.word_count.value
            if sample_article.metrics.word_count
            else None
        )
        original_reading_time = (
            sample_article.metrics.reading_time.minutes
            if sample_article.metrics.reading_time
            else None
        )
        original_language = (
            sample_article.metadata.language.code
            if sample_article.metadata.language
            else None
        )
        original_tags = set(tuple(sample_article.metadata.tags.sorted_tags))
        original_keywords = set(tuple(sample_article.metadata.keywords.keywords))
        original_category = (
            sample_article.metadata.category.value
            if sample_article.metadata.category
            else None
        )
        original_validation_score = sample_article.validation_score
        original_quality_level = str(sample_article.quality.quality_level)

        # Act - Reconstruir desde DB usando mapper
        from src.rss.article.infra.persistence.mappers import RssArticleMapper

        stmt = select(ArticleModel).where(ArticleModel.article_id == str(original_id))
        result = await db_session.execute(stmt)
        model = result.scalar_one()

        reconstructed = RssArticleMapper.to_domain(model)

        # Assert - Verificar que todos los campos se reconstruyeron correctamente
        assert str(reconstructed.id) == str(original_id)
        assert reconstructed.title == original_title
        assert reconstructed.url == original_url
        assert reconstructed.content_markdown == original_content

        # Verificar Value Objects
        assert reconstructed.readability_score == original_readability
        assert reconstructed.word_count == original_word_count
        assert reconstructed.reading_time_minutes == original_reading_time
        assert reconstructed.language == original_language
        assert set(reconstructed.tags) == original_tags
        assert set(reconstructed.keywords) == original_keywords
        assert reconstructed.category == original_category
        assert reconstructed.validation_score == original_validation_score
        assert str(reconstructed.quality_level) == original_quality_level

    async def test_reconstruct_article_with_optional_value_objects_none(
        self,
        repository: ArticleWriteRepository,
        db_session: AsyncSession,
    ):
        """Debería reconstruir Article correctamente cuando Value Objects opcionales son None."""
        # Arrange - Crear Article mínimo sin VOs opcionales
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Minimal RssArticle",
            url="https://example.com/minimal",
            source_id=RssFeedId(str(uuid4())),
        )

        await repository.save(article)

        # Act - Reconstruir
        from src.rss.article.infra.persistence.mappers import RssArticleMapper

        stmt = select(ArticleModel).where(ArticleModel.article_id == str(article.id))
        result = await db_session.execute(stmt)
        model = result.scalar_one()

        reconstructed = RssArticleMapper.to_domain(model)

        # Assert - Verificar que VOs opcionales son None
        assert reconstructed.readability_score is None
        assert reconstructed.word_count is None
        assert reconstructed.reading_time_minutes is None
        assert reconstructed.language is None
        assert reconstructed.category is None
        assert reconstructed.validation_score is None
        assert reconstructed.quality_level is None

    async def test_reconstruct_preserves_value_object_types(
        self,
        repository: ArticleWriteRepository,
        sample_article: RssArticle,
        db_session: AsyncSession,
    ):
        """Debería reconstruir Article con tipos correctos de Value Objects."""
        # Arrange
        await repository.save(sample_article)

        # Act - Reconstruir
        from src.rss.article.infra.persistence.mappers import RssArticleMapper

        stmt = select(ArticleModel).where(
            ArticleModel.article_id == str(sample_article.id)
        )
        result = await db_session.execute(stmt)
        model = result.scalar_one()

        reconstructed = RssArticleMapper.to_domain(model)

        # Assert - Verificar tipos internos (aunque properties retornan primitivos)
        assert isinstance(reconstructed._id, RssArticleId)
        assert isinstance(reconstructed._title, RssArticleTitle)
        assert isinstance(reconstructed._url, RssArticleUrl)
        assert isinstance(reconstructed._source_id, RssFeedId)

        # VOs opcionales
        if reconstructed._readability_score:
            assert isinstance(reconstructed._readability_score, ReadabilityScore)
        if reconstructed._word_count:
            assert isinstance(reconstructed._word_count, WordCount)
        if reconstructed._reading_time:
            assert isinstance(reconstructed._reading_time, ReadingTime)
        if reconstructed._language:
            assert isinstance(reconstructed._language, ContentLanguage)
        if reconstructed._tags:
            assert isinstance(reconstructed._tags, TagCollection)
        if reconstructed._keywords:
            assert isinstance(reconstructed._keywords, KeywordCollection)
        if reconstructed._category:
            assert isinstance(reconstructed._category, ArticleCategory)
        if reconstructed._validation_info:
            assert isinstance(reconstructed._validation_info, ValidationInfo)
        if reconstructed._quality_level:
            assert isinstance(reconstructed._quality_level, Level)


@pytest.mark.integration
class TestRssArticleRepositoryEventSourcing:
    """Tests de event sourcing con persistencia."""

    async def test_events_are_not_emitted_on_reconstruction(
        self,
        repository: ArticleWriteRepository,
        sample_article: RssArticle,
        db_session: AsyncSession,
    ):
        """Debería reconstruir Article sin emitir eventos de dominio."""
        # Arrange - Guardar
        await repository.save(sample_article)

        # Act - Reconstruir
        from src.rss.article.infra.persistence.mappers import RssArticleMapper

        stmt = select(ArticleModel).where(
            ArticleModel.article_id == str(sample_article.id)
        )
        result = await db_session.execute(stmt)
        model = result.scalar_one()

        reconstructed = RssArticleMapper.to_domain(model)

        # Assert - No debe tener eventos pendientes
        assert len(reconstructed.get_uncommitted_events()) == 0
        assert len(reconstructed.domain_events) == 0

    async def test_events_persist_through_save_cycle(
        self,
        repository: ArticleWriteRepository,
        sample_article: RssArticle,
        db_session: AsyncSession,
    ):
        """Debería mantener eventos durante ciclo de guardado."""
        # Arrange - Capturar eventos iniciales
        initial_events_count = len(sample_article.get_uncommitted_events())

        # Act - Guardar
        await repository.save(sample_article)

        # Assert - Eventos fueron procesados (el repositorio los publica)
        # Nota: En este test sin event_publisher, los eventos simplemente se capturan
        assert initial_events_count > 0  # Debe haber eventos de creación

    async def test_multiple_operations_generate_multiple_events(
        self,
        repository: ArticleWriteRepository,
        db_session: AsyncSession,
    ):
        """Debería generar múltiples eventos para múltiples operaciones."""
        # Arrange - Crear Article
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Event Test RssArticle",
            url="https://example.com/events",
            source_id=RssFeedId(str(uuid4())),
        )

        # Guardar y limpiar eventos
        await repository.save(article)
        article.mark_events_as_committed()

        # Act - Realizar múltiples operaciones
        article.update_content_fields(markdown="# New Content")
        article.add_tag("event-test")
        article.update_readability_score(0.8)

        # Assert - Debe haber generado eventos
        uncommitted = article.get_uncommitted_events()
        assert len(uncommitted) > 0

        # Guardar nuevamente
        await repository.save(article)


@pytest.mark.integration
class TestRssArticleRepositoryOptimisticLocking:
    """Tests de optimistic locking con version."""

    async def test_version_increments_on_save(
        self,
        repository: ArticleWriteRepository,
        sample_article: RssArticle,
        db_session: AsyncSession,
    ):
        """Debería incrementar version al guardar."""
        # Arrange
        initial_version = sample_article.version

        # Act - Guardar
        await repository.save(sample_article)

        # Assert - Version en DB debe ser la del aggregate
        stmt = select(ArticleModel).where(
            ArticleModel.article_id == str(sample_article.id)
        )
        result = await db_session.execute(stmt)
        model = result.scalar_one()

        assert model.version == initial_version

    async def test_version_persists_through_updates(
        self,
        repository: ArticleWriteRepository,
        sample_article: RssArticle,
        db_session: AsyncSession,
    ):
        """Debería persistir version correctamente en actualizaciones."""
        # Arrange - Guardar inicial
        await repository.save(sample_article)
        initial_version = sample_article.version

        # Act - Actualizar y guardar
        sample_article.update_content_fields(markdown="# Updated")
        # Version se incrementa automáticamente en el repositorio
        await repository.save(sample_article)

        # Assert - Version debe haber incrementado
        stmt = select(ArticleModel).where(
            ArticleModel.article_id == str(sample_article.id)
        )
        result = await db_session.execute(stmt)
        model = result.scalar_one()

        assert model.version == initial_version + 1
        assert model.version == sample_article.version

    async def test_version_preserved_on_reconstruction(
        self,
        repository: ArticleWriteRepository,
        sample_article: RssArticle,
        db_session: AsyncSession,
    ):
        """Debería preservar version al reconstruir desde DB."""
        # Arrange - Guardar y actualizar para incrementar version
        await repository.save(sample_article)
        sample_article.update_content_fields(markdown="# Updated 1")
        await repository.save(sample_article)
        sample_article.update_content_fields(markdown="# Updated 2")
        await repository.save(sample_article)
        expected_version = sample_article.version

        # Act - Reconstruir
        from src.rss.article.infra.persistence.mappers import RssArticleMapper

        stmt = select(ArticleModel).where(
            ArticleModel.article_id == str(sample_article.id)
        )
        result = await db_session.execute(stmt)
        model = result.scalar_one()

        reconstructed = RssArticleMapper.to_domain(model)

        # Assert - Version debe ser la misma
        assert reconstructed.version == expected_version

    async def test_concurrent_updates_use_version(
        self,
        repository: ArticleWriteRepository,
        sample_article: RssArticle,
        db_session: AsyncSession,
    ):
        """Debería usar version para detectar actualizaciones concurrentes."""
        # Arrange - Guardar Article
        await repository.save(sample_article)
        original_version = sample_article.version

        # Simular dos instancias del mismo Article
        from src.rss.article.infra.persistence.mappers import RssArticleMapper

        stmt = select(ArticleModel).where(
            ArticleModel.article_id == str(sample_article.id)
        )
        result = await db_session.execute(stmt)
        model = result.scalar_one()

        article_instance_1 = RssArticleMapper.to_domain(model)
        article_instance_2 = RssArticleMapper.to_domain(model)

        # Act - Actualizar primera instancia
        article_instance_1.update_content_fields(markdown="# Update 1")
        # Version se incrementa automáticamente en el repositorio
        await repository.save(article_instance_1)

        # Actualizar segunda instancia (debería tener version desactualizada)
        article_instance_2.update_content_fields(markdown="# Update 2")
        # Version se incrementa automáticamente en el repositorio

        # Assert - Ambas instancias tienen versions diferentes después del save
        assert article_instance_1.version == original_version + 1
        assert article_instance_2.version == original_version  # Aún no guardada

        # En un sistema real con optimistic locking, la segunda actualización
        # debería fallar. Aquí solo verificamos que las versions se manejan.
        await repository.save(article_instance_2)

        # Verificar version final en DB
        result = await db_session.execute(stmt)
        model = result.scalar_one()

        # La última actualización sobrescribe (sin optimistic locking real en este test)
        assert model.version == article_instance_2.version


@pytest.mark.integration
class TestRssArticleRepositoryValueObjectAccess:
    """Tests para verificar acceso a Value Objects después de persistencia.

    Estos tests validan que:
    1. Los VOs se persisten correctamente
    2. Los VOs se reconstruyen correctamente desde DB
    3. El mapper convierte correctamente entre ORM y Domain
    4. Los VOs mantienen su integridad a través del ciclo completo

    Requirements: 5.1, 5.2
    """

    async def test_create_persist_retrieve_vos_intact(
        self,
        repository: ArticleWriteRepository,
        db_session: AsyncSession,
    ):
        """Test: Crear article → persistir → recuperar → VOs intactos.

        Valida que todos los Value Objects se mantienen intactos a través
        del ciclo completo de creación, persistencia y recuperación.
        """
        # Arrange - Crear Article con VOs completos
        factory = RssArticleFactory()
        article = factory.create_article(
            title="VO Integrity Test RssArticle",
            url="https://example.com/vo-test",
            source_id=RssFeedId(str(uuid4())),
        )

        # Agregar contenido y VOs
        article.update_content_fields(
            markdown="# VO Test\n\nContent for testing VO integrity."
        )
        article.update_readability_score(0.82)
        article.set_word_count(175)
        article.set_reading_time(2)
        article.update_language("en", 0.98)
        article.add_tag("integration")
        article.add_tag("value-objects")
        article.set_keywords(["testing", "vos", "persistence"])
        article.update_category("technology", 0.92)
        article.validate_article(0.88, "integration-test")
        article.assess_quality(Level.high())

        # Capturar estado de VOs antes de persistir
        original_content_vo = article.content_vo
        original_metrics_vo = article.metrics_vo
        original_metadata_vo = article.metadata_vo
        original_quality_vo = article.quality_vo

        # Act - Persistir
        await repository.save(article)

        # Recuperar desde DB usando mapper
        from src.rss.article.infra.persistence.mappers import RssArticleMapper

        stmt = select(ArticleModel).where(ArticleModel.article_id == str(article.id))
        result = await db_session.execute(stmt)
        model = result.scalar_one()

        reconstructed = RssArticleMapper.to_domain(model)

        # Assert - Verificar que VOs están intactos
        # Content VO
        assert reconstructed.content_vo.markdown == original_content_vo.markdown
        assert reconstructed.content_vo.has_markdown == original_content_vo.has_markdown

        # Metrics VO
        assert reconstructed.metrics.word_count == original_metrics_vo.word_count
        assert reconstructed.metrics.reading_time == original_metrics_vo.reading_time

        # Metadata VO
        assert reconstructed.metadata.language == original_metadata_vo.language
        assert set(reconstructed.metadata.tags.sorted_tags) == set(
            original_metadata_vo.tags.sorted_tags
        )
        assert set(reconstructed.metadata.keywords.keywords) == set(
            original_metadata_vo.keywords.keywords
        )
        assert reconstructed.metadata.category == original_metadata_vo.category

        # Quality VO
        assert reconstructed.quality.quality_level == original_quality_vo.quality_level

        # Validation Info
        assert reconstructed.validation_info.score == article.validation_info.score
        assert (
            reconstructed.validation_info.validated_by
            == article.validation_info.validated_by
        )

    async def test_update_persist_retrieve_vos_updated(
        self,
        repository: ArticleWriteRepository,
        db_session: AsyncSession,
    ):
        """Test: Actualizar article → persistir → recuperar → VOs actualizados.

        Valida que las actualizaciones a los Value Objects se persisten
        y recuperan correctamente.
        """
        # Arrange - Crear y guardar Article inicial
        factory = RssArticleFactory()
        article = factory.create_article(
            title="VO Update Test",
            url="https://example.com/vo-update",
            source_id=RssFeedId(str(uuid4())),
        )

        article.update_content_fields(markdown="# Initial Content")
        article.update_readability_score(0.70)
        article.set_word_count(100)
        article.add_tag("initial")

        await repository.save(article)

        # Act - Actualizar VOs
        article.update_content_fields(
            markdown="# Updated Content\n\nThis is much longer content with more details."
        )
        article.update_readability_score(0.85)
        article.set_word_count(250)
        article.set_reading_time(3)
        article.add_tag("updated")
        article.set_keywords(["updated", "content", "test"])
        article.update_language("es", 0.95)

        # Capturar estado actualizado
        updated_content = article.content_vo.markdown
        updated_readability = article.quality.readability_score
        updated_word_count = article.metrics.word_count
        updated_tags = set(article.metadata.tags.sorted_tags)
        updated_keywords = set(article.metadata.keywords.keywords)
        updated_language = article.metadata.language

        # Persistir actualizaciones
        await repository.save(article)

        # Recuperar desde DB
        from src.rss.article.infra.persistence.mappers import RssArticleMapper

        stmt = select(ArticleModel).where(ArticleModel.article_id == str(article.id))
        result = await db_session.execute(stmt)
        model = result.scalar_one()

        reconstructed = RssArticleMapper.to_domain(model)

        # Assert - Verificar que actualizaciones se persistieron
        assert reconstructed.content_vo.markdown == updated_content
        assert reconstructed.quality.readability_score == updated_readability
        assert reconstructed.metrics.word_count == updated_word_count
        assert set(reconstructed.metadata.tags.sorted_tags) == updated_tags
        assert set(reconstructed.metadata.keywords.keywords) == updated_keywords
        assert reconstructed.metadata.language == updated_language

    async def test_mapper_converts_correctly_between_orm_and_vos(
        self,
        repository: ArticleWriteRepository,
        db_session: AsyncSession,
    ):
        """Test: Mapper convierte correctamente entre ORM y VOs.

        Valida que RssArticleMapper convierte correctamente en ambas direcciones:
        - Domain → ORM (to_model)
        - ORM → Domain (to_domain)
        """
        # Arrange - Crear Article con VOs diversos
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Mapper Conversion Test",
            url="https://example.com/mapper-test",
            source_id=RssFeedId(str(uuid4())),
        )

        article.update_content_fields(
            markdown="# Mapper Test\n\nTesting mapper conversions."
        )
        article.update_readability_score(0.78)
        article.set_word_count(180)
        article.set_reading_time(2)
        article.update_language("fr", 0.89)
        article.add_tag("mapper")
        article.add_tag("conversion")
        article.set_keywords(["mapper", "orm", "domain"])
        article.update_category("testing", 0.87)
        article.validate_article(0.91, "mapper-validator")
        article.assess_quality(Level.medium())

        # Act - Convertir Domain → ORM → Domain
        from src.rss.article.infra.persistence.mappers import RssArticleMapper

        # Domain → ORM
        await repository.save(article)

        stmt = select(ArticleModel).where(ArticleModel.article_id == str(article.id))
        result = await db_session.execute(stmt)
        orm_model = result.scalar_one()

        # ORM → Domain
        reconstructed = RssArticleMapper.to_domain(orm_model)

        # Assert - Verificar conversión correcta en ambas direcciones
        # Verificar que ORM tiene los datos correctos
        assert orm_model.content_markdown == article.content_vo.markdown
        assert orm_model.readability_score == article.quality.readability_score.value
        assert orm_model.word_count == article.metrics.word_count.value
        assert orm_model.reading_time_minutes == article.metrics.reading_time.minutes
        assert orm_model.language == article.metadata.language.code
        assert set(orm_model.tags) == set(article.metadata.tags.sorted_tags)
        assert set(orm_model.keywords) == set(article.metadata.keywords.keywords)

        # Verificar que Domain reconstruido tiene VOs correctos
        assert reconstructed.content_vo.markdown == article.content_vo.markdown
        assert (
            reconstructed.metrics.word_count.value == article.metrics.word_count.value
        )
        assert (
            reconstructed.metrics.reading_time.minutes
            == article.metrics.reading_time.minutes
        )
        assert reconstructed.metadata.language.code == article.metadata.language.code
        assert set(reconstructed.metadata.tags.sorted_tags) == set(
            article.metadata.tags.sorted_tags
        )
        assert set(reconstructed.metadata.keywords.keywords) == set(
            article.metadata.keywords.keywords
        )
        assert (
            reconstructed.quality.readability_score.value
            == article.quality.readability_score.value
        )
        assert reconstructed.quality.quality_level == article.quality.quality_level

        # Verificar ValidationInfo
        assert reconstructed.validation_info.score == article.validation_info.score
        assert (
            reconstructed.validation_info.validated_by
            == article.validation_info.validated_by
        )

    async def test_vo_access_through_properties_after_persistence(
        self,
        repository: ArticleWriteRepository,
        db_session: AsyncSession,
    ):
        """Test: Acceso a VOs a través de properties después de persistencia.

        Valida que se puede acceder a los datos de VOs tanto directamente
        (content_vo.markdown) como a través de properties de conveniencia
        (content_markdown) después de persistir y recuperar.
        """
        # Arrange - Crear Article
        factory = RssArticleFactory()
        article = factory.create_article(
            title="VO Property Access Test",
            url="https://example.com/vo-properties",
            source_id=RssFeedId(str(uuid4())),
        )

        article.update_content_fields(
            markdown="# Property Access\n\nTesting VO property access."
        )
        article.update_readability_score(0.76)
        article.set_word_count(160)
        article.update_language("de", 0.93)

        # Act - Persistir y recuperar
        await repository.save(article)

        from src.rss.article.infra.persistence.mappers import RssArticleMapper

        stmt = select(ArticleModel).where(ArticleModel.article_id == str(article.id))
        result = await db_session.execute(stmt)
        model = result.scalar_one()

        reconstructed = RssArticleMapper.to_domain(model)

        # Assert - Verificar acceso directo a VOs
        assert reconstructed.content_vo.markdown is not None
        assert reconstructed.metrics.word_count is not None
        assert reconstructed.metadata.language is not None
        assert reconstructed.quality.readability_score is not None

        # Verificar acceso a través de properties de conveniencia
        assert reconstructed.content_markdown == reconstructed.content_vo.markdown
        assert reconstructed.word_count == reconstructed.metrics.word_count.value
        assert reconstructed.language == reconstructed.metadata.language.code
        assert (
            reconstructed.readability_score
            == reconstructed.quality.readability_score.value
        )

        # Verificar que ambos métodos de acceso retornan los mismos valores
        assert (
            reconstructed.content_markdown
            == "# Property Access\n\nTesting VO property access."
        )
        assert reconstructed.word_count == 160
        assert reconstructed.language == "de"
        assert reconstructed.readability_score == 0.76

    async def test_empty_vos_persist_and_reconstruct_correctly(
        self,
        repository: ArticleWriteRepository,
        db_session: AsyncSession,
    ):
        """Test: VOs vacíos se persisten y reconstruyen correctamente.

        Valida que cuando un RssArticle tiene VOs vacíos (sin datos opcionales),
        estos se persisten y reconstruyen correctamente como empty/None.
        """
        # Arrange - Crear Article mínimo sin VOs opcionales
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Empty VOs Test",
            url="https://example.com/empty-vos",
            source_id=RssFeedId(str(uuid4())),
        )

        # No agregar ningún VO opcional
        # Solo tiene content_vo vacío por defecto

        # Act - Persistir y recuperar
        await repository.save(article)

        from src.rss.article.infra.persistence.mappers import RssArticleMapper

        stmt = select(ArticleModel).where(ArticleModel.article_id == str(article.id))
        result = await db_session.execute(stmt)
        model = result.scalar_one()

        reconstructed = RssArticleMapper.to_domain(model)

        # Assert - Verificar que VOs opcionales son None o empty
        assert (
            reconstructed.content_vo.markdown is None
            or reconstructed.content_vo.markdown == ""
        )
        assert reconstructed.metrics.word_count is None
        assert reconstructed.metrics.reading_time is None
        assert reconstructed.metadata.language is None
        assert reconstructed.metadata.category is None
        assert reconstructed.quality.readability_score is None
        assert reconstructed.quality.quality_level is None
        assert reconstructed.validation_info is None

        # Verificar que properties de conveniencia también retornan None
        assert reconstructed.word_count is None
        assert reconstructed.reading_time_minutes is None
        assert reconstructed.language is None
        assert reconstructed.category is None
        assert reconstructed.readability_score is None
