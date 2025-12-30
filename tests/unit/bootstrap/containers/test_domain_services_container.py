"""Tests para DomainServicesContainer."""

from unittest.mock import Mock

import pytest

from src.bootstrap.containers.domain_services import DomainServicesContainer


class TestDomainServicesContainer:
    """Tests para DomainServicesContainer."""

    @pytest.fixture
    def mock_infra(self):
        """Mock de SharedInfrastructure."""
        infra = Mock()
        infra.logger = Mock()
        return infra

    @pytest.fixture
    def container(self, mock_infra):
        """Container de Domain Services para tests."""
        return DomainServicesContainer(infra=mock_infra)

    def test_container_initialization(self, container, mock_infra):
        """Debería inicializar el container correctamente."""
        assert container.infra == mock_infra
        assert container._article_hashing_service is None
        assert container._article_keyword_service is None
        assert container._article_readability_service is None
        assert container._article_quality_service is None
        assert container._article_deduplication_service is None

    def test_get_article_hashing_service_lazy_loads(self, container):
        """Debería cargar ArticleHashingService de forma lazy."""
        # Arrange - Verificar que no está inicializado
        assert container._article_hashing_service is None

        # Act
        service = container.get_article_hashing_service()

        # Assert
        assert service is not None
        assert container._article_hashing_service is service

        # Verificar que es Singleton
        service2 = container.get_article_hashing_service()
        assert service2 is service

    def test_get_article_keyword_service_lazy_loads(self, container):
        """Debería cargar ArticleKeywordService de forma lazy."""
        # Arrange
        assert container._article_keyword_service is None

        # Act
        service = container.get_article_keyword_service()

        # Assert
        assert service is not None
        assert container._article_keyword_service is service

        # Verificar Singleton
        service2 = container.get_article_keyword_service()
        assert service2 is service

    def test_get_article_readability_service_lazy_loads(self, container):
        """Debería cargar ArticleReadabilityService de forma lazy."""
        # Arrange
        assert container._article_readability_service is None

        # Act
        service = container.get_article_readability_service()

        # Assert
        assert service is not None
        assert container._article_readability_service is service

        # Verificar Singleton
        service2 = container.get_article_readability_service()
        assert service2 is service

    def test_get_article_quality_service_lazy_loads(self, container):
        """Debería cargar ArticleQualityService de forma lazy."""
        # Arrange
        assert container._article_quality_service is None

        # Act
        service = container.get_article_quality_service()

        # Assert
        assert service is not None
        assert container._article_quality_service is service

        # Verificar Singleton
        service2 = container.get_article_quality_service()
        assert service2 is service

    def test_get_article_quality_service_injects_readability_service(self, container):
        """Debería inyectar ArticleReadabilityService en ArticleQualityService."""
        # Act
        quality_service = container.get_article_quality_service()
        readability_service = container.get_article_readability_service()

        # Assert - Verificar que quality service tiene readability service
        assert quality_service is not None
        assert readability_service is not None
        assert quality_service._readability_service is readability_service

    def test_get_article_deduplication_service_lazy_loads(self, container):
        """Debería cargar ArticleDeduplicationService de forma lazy."""
        # Arrange
        assert container._article_deduplication_service is None

        # Act
        service = container.get_article_deduplication_service()

        # Assert
        assert service is not None
        assert container._article_deduplication_service is service

        # Verificar Singleton
        service2 = container.get_article_deduplication_service()
        assert service2 is service

    def test_get_article_deduplication_service_has_threshold(self, container):
        """Debería configurar ArticleDeduplicationService con threshold."""
        # Act
        dedup_service = container.get_article_deduplication_service()

        # Assert
        assert dedup_service is not None
        assert dedup_service._similarity_threshold == 0.85

    def test_get_service_status_returns_initialization_state(self, container):
        """Debería retornar el estado de inicialización de servicios."""
        # Arrange - Ningún servicio inicializado
        status = container.get_service_status()

        # Assert - Todos False
        assert status["article_hashing_service"] is False
        assert status["article_keyword_service"] is False
        assert status["article_readability_service"] is False
        assert status["article_quality_service"] is False
        assert status["article_deduplication_service"] is False

        # Act - Inicializar algunos servicios
        container.get_article_hashing_service()
        container.get_article_keyword_service()

        # Assert - Solo los inicializados son True
        status = container.get_service_status()
        assert status["article_hashing_service"] is True
        assert status["article_keyword_service"] is True
        assert status["article_readability_service"] is False
        assert status["article_quality_service"] is False
        assert status["article_deduplication_service"] is False

    def test_initialize_all_services_loads_all(self, container):
        """Debería inicializar todos los servicios de forma eager."""
        # Arrange - Verificar que ninguno está inicializado
        status_before = container.get_service_status()
        assert all(not initialized for initialized in status_before.values())

        # Act
        container.initialize_all_services()

        # Assert - Todos inicializados
        status_after = container.get_service_status()
        assert all(initialized for initialized in status_after.values())

        # Verificar que los servicios son accesibles
        assert container.get_article_hashing_service() is not None
        assert container.get_article_keyword_service() is not None
        assert container.get_article_readability_service() is not None
        assert container.get_article_quality_service() is not None
        assert container.get_article_deduplication_service() is not None

    def test_services_are_singletons(self, container):
        """Debería retornar la misma instancia en múltiples llamadas."""
        # Act - Obtener servicios múltiples veces
        hashing1 = container.get_article_hashing_service()
        hashing2 = container.get_article_hashing_service()

        keyword1 = container.get_article_keyword_service()
        keyword2 = container.get_article_keyword_service()

        readability1 = container.get_article_readability_service()
        readability2 = container.get_article_readability_service()

        quality1 = container.get_article_quality_service()
        quality2 = container.get_article_quality_service()

        dedup1 = container.get_article_deduplication_service()
        dedup2 = container.get_article_deduplication_service()

        # Assert - Mismas instancias
        assert hashing1 is hashing2
        assert keyword1 is keyword2
        assert readability1 is readability2
        assert quality1 is quality2
        assert dedup1 is dedup2

    def test_services_implement_correct_interfaces(self, container):
        """Debería retornar servicios que implementan las interfaces correctas."""
        from src.domain.interfaces.services.articles.article_deduplication_service import (
            IArticleDeduplicationService,
        )
        from src.domain.interfaces.services.articles.article_hashing_service import (
            IArticleHashingService,
        )
        from src.domain.interfaces.services.articles.article_keyword_service import (
            IArticleKeywordService,
        )
        from src.domain.interfaces.services.articles.article_quality_service import (
            IArticleQualityService,
        )
        from src.domain.interfaces.services.articles.article_readability_service import (
            IArticleReadabilityService,
        )

        # Act
        hashing = container.get_article_hashing_service()
        keyword = container.get_article_keyword_service()
        readability = container.get_article_readability_service()
        quality = container.get_article_quality_service()
        dedup = container.get_article_deduplication_service()

        # Assert - Verificar que implementan las interfaces
        # Nota: En Python con Protocol, verificamos que tienen los métodos requeridos
        assert hasattr(hashing, "generate_and_assign_content_hash")
        assert hasattr(keyword, "extract_keywords")
        assert hasattr(readability, "calculate_readability_score")
        assert hasattr(quality, "assess_quality")
        assert hasattr(dedup, "is_duplicate")
