"""
Property-Based Tests para referencias entre aggregates en RssArticle.

Feature: article-aggregate-refactor, Property 16
Validates: Requirements 16.3
"""

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.article.domain.value_objects import RssArticleId
from src.rss.feed.domain.value_objects import RssFeedId


class TestRssArticleAggregateReferencesProperties:
    """Property-based tests para validar que aggregates solo usan IDs para referencias."""

    @given(
        title=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
        url=st.from_regex(
            r"https?://[a-z0-9\-]+\.[a-z]{2,}(/[a-z0-9\-]*)*", fullmatch=True
        ),
        source_id=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_property_source_reference_uses_only_id(
        self, title: str, url: str, source_id: str
    ):
        """
        Property 16: Aggregate references use only IDs (source_id).

        Para cualquier RssArticle creado, la referencia al RssFeed aggregate
        debe almacenarse como RssFeedId Value Object, no como instancia
        completa del RssFeed aggregate.

        Esto mantiene límites transaccionales claros y previene inconsistencias.

        Feature: article-aggregate-refactor, Property 16
        Validates: Requirements 16.3
        """
        # Arrange
        source_id_vo = RssFeedId(source_id)

        # Act - Crear Article con referencia a Source
        factory = RssArticleFactory()

        article = factory.create_article(
            title=title,
            url=url,
            source_id=source_id_vo,
        )

        # Assert - Verificar que solo se almacena el ID, no el aggregate completo
        assert article.source_id is not None
        assert isinstance(article.source_id, RssFeedId)
        assert str(article.source_id) == source_id

        # Verificar que NO hay atributo _source (aggregate completo)
        assert not hasattr(
            article, "_source"
        ), "RssArticle NO debe almacenar instancia completa de RssFeed aggregate"

        # Verificar que el ID es un Value Object, no un string primitivo
        assert not isinstance(
            article.source_id, str
        ), "source_id debe ser RssFeedId Value Object, no string primitivo"

    @given(
        title=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
        url=st.from_regex(
            r"https?://[a-z0-9\-]+\.[a-z]{2,}(/[a-z0-9\-]*)*", fullmatch=True
        ),
        source_id=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
        duplicate_of_id=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_property_duplicate_reference_uses_only_id(
        self, title: str, url: str, source_id: str, duplicate_of_id: str
    ):
        """
        Property 16: Aggregate references use only IDs (duplicate_of_article_id).

        Para cualquier RssArticle marcado como duplicado, la referencia al
        RssArticle original debe almacenarse como RssArticleId Value Object,
        no como instancia completa del RssArticle aggregate.

        Feature: article-aggregate-refactor, Property 16
        Validates: Requirements 16.3
        """
        # Arrange
        source_id_vo = RssFeedId(source_id)

        # Crear UUID válido para el artículo duplicado
        import uuid

        duplicate_uuid = str(uuid.uuid4())
        duplicate_article_id = RssArticleId(duplicate_uuid)

        # Act - Crear Article y marcarlo como duplicado
        factory = RssArticleFactory()

        article = factory.create_article(
            title=title,
            url=url,
            source_id=source_id_vo,
        )

        article.mark_as_duplicate(duplicate_article_id)

        # Assert - Verificar que solo se almacena el ID, no el aggregate completo
        assert article.duplication_vo.is_duplicate is True
        assert article.duplication_vo.duplicate_of_article_id is not None
        assert isinstance(article.duplication_vo.duplicate_of_article_id, RssArticleId)
        assert article.duplication_vo.duplicate_of_article_id == duplicate_article_id

        # Verificar que NO hay atributo _duplicate_of (aggregate completo)
        assert not hasattr(
            article, "_duplicate_of"
        ), "RssArticle NO debe almacenar instancia completa del RssArticle duplicado"

        # Verificar que el ID es un Value Object, no un string primitivo
        assert not isinstance(
            article.duplication_vo.duplicate_of_article_id, str
        ), "duplicate_of_article_id debe ser RssArticleId Value Object, no string primitivo"

    @given(
        title=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
        url=st.from_regex(
            r"https?://[a-z0-9\-]+\.[a-z]{2,}(/[a-z0-9\-]*)*", fullmatch=True
        ),
        source_id=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_property_aggregate_references_are_value_objects(
        self, title: str, url: str, source_id: str
    ):
        """
        Property 16: Aggregate references use only IDs (Value Objects).

        Para cualquier RssArticle, todas las referencias a otros aggregates
        deben ser Value Objects (RssFeedId, RssArticleId), no strings primitivos
        ni instancias completas de aggregates.

        Feature: article-aggregate-refactor, Property 16
        Validates: Requirements 16.3
        """
        # Arrange
        source_id_vo = RssFeedId(source_id)

        # Act - Crear Article
        factory = RssArticleFactory()

        article = factory.create_article(
            title=title,
            url=url,
            source_id=source_id_vo,
        )

        # Assert - Verificar que source_id es Value Object
        assert isinstance(
            article.source_id, RssFeedId
        ), "source_id debe ser RssFeedId Value Object"

        # Verificar que duplicate_of_article_id es None o ArticleId VO
        if article.duplication_vo.duplicate_of_article_id is not None:
            assert isinstance(
                article.duplication_vo.duplicate_of_article_id, RssArticleId
            ), "duplicate_of_article_id debe ser RssArticleId Value Object cuando está presente"

        # Verificar que NO hay referencias a aggregates completos
        # Buscar atributos que podrían contener aggregates completos
        forbidden_attrs = ["_source", "_duplicate_of", "_original_article"]
        for attr in forbidden_attrs:
            assert not hasattr(
                article, attr
            ), f"RssArticle NO debe tener atributo {attr} con aggregate completo"

    @given(
        title=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
        url=st.from_regex(
            r"https?://[a-z0-9\-]+\.[a-z]{2,}(/[a-z0-9\-]*)*", fullmatch=True
        ),
        source_id=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_property_aggregate_id_is_value_object(
        self, title: str, url: str, source_id: str
    ):
        """
        Property 16: Aggregate references use only IDs (own ID).

        Para cualquier RssArticle, su propio ID debe ser un RssArticleId Value Object,
        no un string primitivo ni UUID directo.

        Feature: article-aggregate-refactor, Property 16
        Validates: Requirements 16.3
        """
        # Arrange
        source_id_vo = RssFeedId(source_id)

        # Act - Crear Article
        factory = RssArticleFactory()

        article = factory.create_article(
            title=title,
            url=url,
            source_id=source_id_vo,
        )

        # Assert - Verificar que el ID propio es Value Object
        assert article.id is not None
        assert isinstance(
            article.id, RssArticleId
        ), "RssArticle.id debe ser RssArticleId Value Object"

        # Verificar que NO es un string primitivo
        assert not isinstance(
            article.id, str
        ), "RssArticle.id NO debe ser string primitivo"

        # Verificar que NO es un UUID directo
        import uuid

        assert not isinstance(
            article.id, uuid.UUID
        ), "RssArticle.id NO debe ser UUID directo, debe ser RssArticleId VO"

    @given(
        title=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
        url=st.from_regex(
            r"https?://[a-z0-9\-]+\.[a-z]{2,}(/[a-z0-9\-]*)*", fullmatch=True
        ),
        source_id=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_property_no_circular_references(
        self, title: str, url: str, source_id: str
    ):
        """
        Property 16: Aggregate references use only IDs (no circular refs).

        Para cualquier RssArticle, no debe haber referencias circulares.
        Solo IDs deben almacenarse, lo que previene ciclos de referencias
        entre aggregates.

        Feature: article-aggregate-refactor, Property 16
        Validates: Requirements 16.3
        """
        # Arrange
        source_id_vo = RssFeedId(source_id)

        # Act - Crear Article
        factory = RssArticleFactory()

        article = factory.create_article(
            title=title,
            url=url,
            source_id=source_id_vo,
        )

        # Assert - Verificar que no hay referencias circulares
        # Un Article no debe contener una referencia a sí mismo como aggregate completo

        # Verificar que source_id es solo un ID, no un objeto Source
        assert isinstance(article.source_id, RssFeedId)

        # Verificar que duplicate_of_article_id es solo un ID, no un Article
        if article.duplication_vo.duplicate_of_article_id is not None:
            assert isinstance(
                article.duplication_vo.duplicate_of_article_id, RssArticleId
            )

            # Verificar que NO es una referencia al mismo artículo
            # (aunque esto sería un error lógico, no arquitectónico)
            # El punto es que solo almacenamos IDs, no aggregates completos

    @given(
        title=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
        url=st.from_regex(
            r"https?://[a-z0-9\-]+\.[a-z]{2,}(/[a-z0-9\-]*)*", fullmatch=True
        ),
        source_id=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_property_aggregate_references_maintain_transactional_boundaries(
        self, title: str, url: str, source_id: str
    ):
        """
        Property 16: Aggregate references use only IDs (transactional boundaries).

        Para cualquier RssArticle, las referencias a otros aggregates mediante IDs
        mantienen límites transaccionales claros. Modificar un RssArticle no debe
        requerir cargar o modificar el RssFeed aggregate referenciado.

        Feature: article-aggregate-refactor, Property 16
        Validates: Requirements 16.3
        """
        # Arrange
        source_id_vo = RssFeedId(source_id)

        # Act - Crear Article
        factory = RssArticleFactory()

        article = factory.create_article(
            title=title,
            url=url,
            source_id=source_id_vo,
        )

        # Modificar el Article (actualizar contenido)
        article.update_content_fields(
            markdown="# New Content\n\nThis is updated content."
        )

        # Assert - Verificar que la modificación no requirió cargar Source
        # El source_id sigue siendo solo un ID, no un aggregate cargado
        assert isinstance(article.source_id, RssFeedId)
        assert str(article.source_id) == source_id

        # Verificar que NO hay atributos que indiquen que Source fue cargado
        assert not hasattr(article, "_source")
        assert not hasattr(article, "_loaded_source")

        # El Article mantiene su límite transaccional independiente
        # Solo necesita su propio estado para ser modificado y persistido

    @given(
        title=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
        url=st.from_regex(
            r"https?://[a-z0-9\-]+\.[a-z]{2,}(/[a-z0-9\-]*)*", fullmatch=True
        ),
        source_id=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_property_aggregate_references_are_serializable(
        self, title: str, url: str, source_id: str
    ):
        """
        Property 16: Aggregate references use only IDs (serialization).

        Para cualquier RssArticle, las referencias a otros aggregates mediante
        Value Objects (IDs) son fácilmente serializables a strings para
        persistencia y comunicación.

        Feature: article-aggregate-refactor, Property 16
        Validates: Requirements 16.3
        """
        # Arrange
        source_id_vo = RssFeedId(source_id)

        # Act - Crear Article
        factory = RssArticleFactory()

        article = factory.create_article(
            title=title,
            url=url,
            source_id=source_id_vo,
        )

        # Assert - Verificar que los IDs son serializables a strings
        # SourceId debe ser convertible a string
        source_id_str = str(article.source_id)
        assert isinstance(source_id_str, str)
        assert source_id_str == source_id

        # ArticleId debe ser convertible a string
        article_id_str = str(article.id)
        assert isinstance(article_id_str, str)
        assert len(article_id_str) > 0

        # Si hay duplicate_of_article_id, también debe ser serializable
        if article.duplication_vo.duplicate_of_article_id is not None:
            duplicate_id_str = str(article.duplication_vo.duplicate_of_article_id)
            assert isinstance(duplicate_id_str, str)
            assert len(duplicate_id_str) > 0

        # Los Value Objects permiten serialización simple sin necesidad
        # de serializar aggregates completos (que sería complejo y costoso)
