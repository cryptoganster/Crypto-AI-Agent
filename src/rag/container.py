"""RAG Bounded Context Container.

Container de inversión de dependencias para el bounded context RAG.
Sigue Clean Architecture + DDD + CQRS.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.shared.container import SharedContainer


class RAGContainer:
    """
    Container del bounded context RAG.

    Responsabilidades:
    - Commands: GenerateContentWithRAGCommand
    - Services: RAGContextAssemblyService, SummarizationService
    - Repositories: ContextPackReadRepository, ContextPackWriteRepository
    - External: OpenAILLMAdapter

    Requirements: 10.5
    """

    def __init__(self, shared: "SharedContainer"):
        self._shared = shared

        # Command Handlers (Lazy)
        self._generate_content_with_rag_handler = None

        # Domain Services (Lazy)
        self._context_assembly_service = None
        self._summarization_service = None

        # Repositories (Lazy)
        self._context_pack_read_repository = None
        self._context_pack_write_repository = None

        # External Services (Lazy)
        self._llm_adapter = None

    # === DOMAIN SERVICES ===

    def get_context_assembly_service(self):
        """
        Factory para RAGContextAssemblyService.

        NOTA: Este servicio requiere IVectorStore del EmbeddingContainer.
        Debe ser inyectado desde el container principal.

        Requirements: 10.5.1
        """
        if self._context_assembly_service is None:
            from src.rag.domain.services.context_assembly import (
                RAGContextAssemblyService,
            )
            from src.shared.config.rag_config import RAGConfig

            # Obtener configuración de RAG desde environment
            rag_config = RAGConfig.from_env()

            self._context_assembly_service = RAGContextAssemblyService(
                vector_store=None,  # TODO: Inyectar desde EmbeddingContainer
                max_tokens=rag_config.max_context_tokens,
            )

        return self._context_assembly_service

    def get_summarization_service(self):
        """
        Factory para SummarizationService.

        Requirements: 10.5.1
        """
        if self._summarization_service is None:
            from src.rag.domain.services.summarization import SummarizationService

            self._summarization_service = SummarizationService(
                llm_service=self.get_llm_adapter(),
            )

        return self._summarization_service

    def get_llm_adapter(self):
        """
        Factory para OpenAILLMAdapter.

        Requirements: 10.5.1, 10.5.4
        """
        if self._llm_adapter is None:
            from src.rag.infra.external.openai_llm_adapter import OpenAILLMAdapter
            from src.shared.config.rag_config import RAGConfig

            # Obtener configuración de RAG desde environment
            rag_config = RAGConfig.from_env()

            self._llm_adapter = OpenAILLMAdapter(
                api_key=rag_config.llm_api_key,
                model=rag_config.llm_model,
            )

        return self._llm_adapter

    # === REPOSITORIES ===

    def get_context_pack_read_repository(self):
        """
        Factory para ContextPackReadRepository.

        Requirements: 10.5.1
        """
        if self._context_pack_read_repository is None:
            from src.rag.infra.persistence.repositories.context_pack_read_repository import (
                SqlAlchemyContextPackReadRepository,
            )

            # Crear nueva sesión para cada request
            session = self._shared.session_factory()

            self._context_pack_read_repository = SqlAlchemyContextPackReadRepository(
                session=session
            )

        return self._context_pack_read_repository

    def get_context_pack_write_repository(self):
        """
        Factory para ContextPackWriteRepository.

        Requirements: 10.5.1
        """
        if self._context_pack_write_repository is None:
            from src.rag.infra.persistence.repositories.context_pack_write_repository import (
                SqlAlchemyContextPackWriteRepository,
            )

            # Crear nueva sesión para cada request
            session = self._shared.session_factory()

            self._context_pack_write_repository = SqlAlchemyContextPackWriteRepository(
                session=session
            )

        return self._context_pack_write_repository

    # === COMMAND HANDLERS ===

    def get_generate_content_with_rag_handler(self):
        """
        Factory para GenerateContentWithRAGHandler.

        NOTA: Este handler requiere IEmbeddingService del EmbeddingContainer.
        Debe ser inyectado desde el container principal.

        Requirements: 10.5.2
        """
        if self._generate_content_with_rag_handler is None:
            from src.rag.app.commands.generate_content_with_rag.handler import (
                GenerateContentWithRAGHandler,
            )

            self._generate_content_with_rag_handler = GenerateContentWithRAGHandler(
                embedding_service=None,  # TODO: Inyectar desde EmbeddingContainer
                context_assembly_service=self.get_context_assembly_service(),
                llm_service=self.get_llm_adapter(),
                logger=self._shared.logger,
            )

        return self._generate_content_with_rag_handler

    # === HANDLER REGISTRATION ===

    def register_handlers(self) -> None:
        """
        Registra todos los handlers del bounded context RAG.

        Incluye:
        - Command handlers en Mediator

        Requirements: 10.5.2
        """
        self._register_command_handlers()

        self._shared.logger.info(
            "RAGContainer: handlers registrados",
        )

    def _register_command_handlers(self) -> None:
        """
        Registra command handlers en Mediator.

        Command Handlers:
        - GenerateContentWithRAGHandler: Genera contenido usando RAG

        Requirements: 10.5.2
        """
        from src.rag.app.commands.generate_content_with_rag.command import (
            GenerateContentWithRAGCommand,
        )

        handlers_registered = []

        # GenerateContentWithRAGHandler
        self._shared.register_handler(
            GenerateContentWithRAGCommand,
            self.get_generate_content_with_rag_handler(),
        )
        handlers_registered.append("GenerateContentWithRAGHandler")

        self._shared.logger.info(
            "Command handlers registrados en Mediator",
            handlers=handlers_registered,
            count=len(handlers_registered),
        )
