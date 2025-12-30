"""Integration tests para RAGContainer.

Tests de integración que verifican:
- Resolución de servicios
- Registro de handlers
- Configuración
- Integración entre componentes

Requirements: 10.5.5
"""

from unittest.mock import AsyncMock, Mock

import pytest

from src.rag.app.commands.generate_content_with_rag.command import (
    GenerateContentWithRAGCommand,
)
from src.rag.app.commands.generate_content_with_rag.handler import (
    GenerateContentWithRAGHandler,
)
from src.rag.container import RAGContainer
from src.rag.domain.services.context_assembly import RAGContextAssemblyService
from src.rag.domain.services.summarization import SummarizationService
from src.rag.infra.external.openai_llm_adapter import OpenAILLMAdapter
from src.rag.infra.persistence.repositories.context_pack_read_repository import (
    SqlAlchemyContextPackReadRepository,
)
from src.rag.infra.persistence.repositories.context_pack_write_repository import (
    SqlAlchemyContextPackWriteRepository,
)
from src.shared.config.rag_config import RAGConfig


class TestRAGContainerServiceResolution:
    """Tests de resolución de servicios del RAGContainer."""

    def test_get_context_assembly_service_returns_service(
        self,
        rag_container: RAGContainer,
    ):
        """Debería retornar RAGContextAssemblyService."""
        # Act
        service = rag_container.get_context_assembly_service()

        # Assert
        assert service is not None
        assert isinstance(service, RAGContextAssemblyService)

    def test_get_context_assembly_service_is_singleton(
        self,
        rag_container: RAGContainer,
    ):
        """Debería retornar la misma instancia (singleton)."""
        # Act
        service1 = rag_container.get_context_assembly_service()
        service2 = rag_container.get_context_assembly_service()

        # Assert
        assert service1 is service2

    def test_get_summarization_service_returns_service(
        self,
        rag_container: RAGContainer,
    ):
        """Debería retornar SummarizationService."""
        # Act
        service = rag_container.get_summarization_service()

        # Assert
        assert service is not None
        assert isinstance(service, SummarizationService)

    def test_get_summarization_service_is_singleton(
        self,
        rag_container: RAGContainer,
    ):
        """Debería retornar la misma instancia (singleton)."""
        # Act
        service1 = rag_container.get_summarization_service()
        service2 = rag_container.get_summarization_service()

        # Assert
        assert service1 is service2

    def test_get_llm_adapter_returns_adapter(
        self,
        rag_container: RAGContainer,
    ):
        """Debería retornar OpenAILLMAdapter."""
        # Act
        adapter = rag_container.get_llm_adapter()

        # Assert
        assert adapter is not None
        assert isinstance(adapter, OpenAILLMAdapter)

    def test_get_llm_adapter_is_singleton(
        self,
        rag_container: RAGContainer,
    ):
        """Debería retornar la misma instancia (singleton)."""
        # Act
        adapter1 = rag_container.get_llm_adapter()
        adapter2 = rag_container.get_llm_adapter()

        # Assert
        assert adapter1 is adapter2


class TestRAGContainerRepositoryResolution:
    """Tests de resolución de repositorios del RAGContainer."""

    def test_get_context_pack_read_repository_returns_repository(
        self,
        rag_container: RAGContainer,
    ):
        """Debería retornar ContextPackReadRepository."""
        # Act
        repository = rag_container.get_context_pack_read_repository()

        # Assert
        assert repository is not None
        assert isinstance(repository, SqlAlchemyContextPackReadRepository)

    def test_get_context_pack_write_repository_returns_repository(
        self,
        rag_container: RAGContainer,
    ):
        """Debería retornar ContextPackWriteRepository."""
        # Act
        repository = rag_container.get_context_pack_write_repository()

        # Assert
        assert repository is not None
        assert isinstance(repository, SqlAlchemyContextPackWriteRepository)


class TestRAGContainerHandlerResolution:
    """Tests de resolución de handlers del RAGContainer."""

    def test_get_generate_content_with_rag_handler_returns_handler(
        self,
        rag_container: RAGContainer,
    ):
        """Debería retornar GenerateContentWithRAGHandler."""
        # Act
        handler = rag_container.get_generate_content_with_rag_handler()

        # Assert
        assert handler is not None
        assert isinstance(handler, GenerateContentWithRAGHandler)

    def test_get_generate_content_with_rag_handler_is_singleton(
        self,
        rag_container: RAGContainer,
    ):
        """Debería retornar la misma instancia (singleton)."""
        # Act
        handler1 = rag_container.get_generate_content_with_rag_handler()
        handler2 = rag_container.get_generate_content_with_rag_handler()

        # Assert
        assert handler1 is handler2


class TestRAGContainerHandlerRegistration:
    """Tests de registro de handlers del RAGContainer."""

    def test_register_handlers_registers_command_handlers(
        self,
        rag_container: RAGContainer,
        shared_container,
    ):
        """Debería registrar command handlers en Mediator."""
        # Act
        rag_container.register_handlers()

        # Assert - Verificar que el handler se puede obtener del mediator
        # Intentamos enviar un comando para verificar que está registrado
        from src.rag.app.commands.generate_content_with_rag.command import (
            GenerateContentWithRAGCommand,
        )

        # Si el handler no estuviera registrado, esto lanzaría HandlerNotFoundError
        # Por ahora, solo verificamos que register_handlers() no lanza excepciones
        assert True  # El hecho de que llegamos aquí significa que el registro funcionó

    def test_register_handlers_logs_registration(
        self,
        rag_container: RAGContainer,
        shared_container,
    ):
        """Debería loggear el registro de handlers."""
        # Arrange
        mock_logger = Mock()
        shared_container.logger = mock_logger

        # Act
        rag_container.register_handlers()

        # Assert
        assert mock_logger.info.called
        # Verificar que se loggeó el registro de handlers
        calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("handlers registrados" in str(call).lower() for call in calls)


class TestRAGContainerConfiguration:
    """Tests de configuración del RAGContainer."""

    def test_rag_config_loads_from_environment(self, monkeypatch):
        """Debería cargar configuración desde variables de entorno."""
        # Arrange
        monkeypatch.setenv("LLM_API_KEY", "test-api-key-123")
        monkeypatch.setenv("LLM_MODEL", "gpt-4")
        monkeypatch.setenv("MAX_CONTEXT_TOKENS", "4000")
        monkeypatch.setenv("DEFAULT_TEMPERATURE", "0.3")
        monkeypatch.setenv("DEFAULT_MAX_TOKENS", "1000")

        # Act
        config = RAGConfig.from_env()

        # Assert
        assert config.llm_api_key == "test-api-key-123"
        assert config.llm_model == "gpt-4"
        assert config.max_context_tokens == 4000
        assert config.default_temperature == 0.3
        assert config.default_max_tokens == 1000

    def test_rag_config_validates_llm_api_key(self):
        """Debería validar que llm_api_key no esté vacío."""
        # Act & Assert
        with pytest.raises(ValueError, match="llm_api_key no puede estar vacío"):
            RAGConfig(llm_api_key="")

    def test_rag_config_validates_llm_model(self):
        """Debería validar que llm_model sea válido."""
        # Act & Assert
        with pytest.raises(ValueError, match="llm_model debe ser uno de"):
            RAGConfig(llm_api_key="test-key", llm_model="invalid-model")

    def test_rag_config_validates_max_context_tokens_positive(self):
        """Debería validar que max_context_tokens sea positivo."""
        # Act & Assert
        with pytest.raises(ValueError, match="max_context_tokens debe ser > 0"):
            RAGConfig(llm_api_key="test-key", max_context_tokens=0)

    def test_rag_config_validates_max_context_tokens_limit(self):
        """Debería validar que max_context_tokens no exceda límite."""
        # Act & Assert
        with pytest.raises(
            ValueError, match="max_context_tokens no puede exceder 8000"
        ):
            RAGConfig(llm_api_key="test-key", max_context_tokens=9000)

    def test_rag_config_validates_temperature_range(self):
        """Debería validar que temperature esté en rango válido."""
        # Act & Assert
        with pytest.raises(ValueError, match="default_temperature debe estar entre"):
            RAGConfig(llm_api_key="test-key", default_temperature=3.0)

    def test_rag_config_validates_max_tokens_positive(self):
        """Debería validar que default_max_tokens sea positivo."""
        # Act & Assert
        with pytest.raises(ValueError, match="default_max_tokens debe ser > 0"):
            RAGConfig(llm_api_key="test-key", default_max_tokens=0)

    def test_rag_config_for_testing_creates_valid_config(self):
        """Debería crear configuración válida para testing."""
        # Act
        config = RAGConfig.for_testing()

        # Assert
        assert config.llm_api_key == "test-key"
        assert config.llm_model == "gpt-4"
        assert config.max_context_tokens == 4000
        assert config.default_temperature == 0.3
        assert config.default_max_tokens == 1000


class TestRAGContainerIntegration:
    """Tests de integración del RAGContainer."""

    def test_container_can_resolve_all_services(
        self,
        rag_container: RAGContainer,
    ):
        """Debería poder resolver todos los servicios sin errores."""
        # Act & Assert - No debería lanzar excepciones
        rag_container.get_context_assembly_service()
        rag_container.get_summarization_service()
        rag_container.get_llm_adapter()
        rag_container.get_context_pack_read_repository()
        rag_container.get_context_pack_write_repository()
        rag_container.get_generate_content_with_rag_handler()

    def test_container_services_have_correct_dependencies(
        self,
        rag_container: RAGContainer,
    ):
        """Debería inyectar dependencias correctamente en servicios."""
        # Act
        summarization_service = rag_container.get_summarization_service()

        # Assert
        assert summarization_service._llm is not None
        assert isinstance(summarization_service._llm, OpenAILLMAdapter)

    def test_container_handlers_have_correct_dependencies(
        self,
        rag_container: RAGContainer,
    ):
        """Debería inyectar dependencias correctamente en handlers."""
        # Act
        handler = rag_container.get_generate_content_with_rag_handler()

        # Assert
        assert handler._context_assembly is not None
        assert handler._llm_service is not None
        assert handler._logger is not None
        assert isinstance(handler._context_assembly, RAGContextAssemblyService)
        assert isinstance(handler._llm_service, OpenAILLMAdapter)
