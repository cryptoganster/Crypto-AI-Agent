# Implementation Plan: LangChain RAG Chat UI

## Overview

Este plan de implementación desglosa la construcción del sistema de chat RAG con LangChain, Ollama y Agent Chat UI en tareas incrementales y manejables.

## Tasks

- [ ] 1. Setup inicial y configuración
  - Configurar bounded context de Chat
  - Instalar dependencias de LangChain
  - Configurar Ollama localmente
  - Crear migraciones de base de datos
  - _Requirements: 1.1, 1.2, 7.1-7.6_

- [ ] 1.1 Crear estructura del bounded context Chat
  - Crear directorios: `src/chat/domain/`, `src/chat/app/`, `src/chat/infra/`
  - Crear subdirectorios para aggregates, services, interfaces, commands, queries
  - Crear archivos `__init__.py` en todos los directorios
  - _Requirements: Arquitectura general_

- [ ] 1.2 Instalar y configurar dependencias
  - Agregar a `requirements.txt`: langchain, langchain-core, langchain-ollama, pgvector
  - Instalar dependencias: `pip install -r requirements.txt`
  - Verificar instalación de Ollama: `ollama --version`
  - _Requirements: 1.1_

- [ ] 1.3 Configurar Ollama y descargar modelos
  - Iniciar servidor Ollama: `ollama serve`
  - Descargar modelo de chat: `ollama pull llama3.2-vision:latest`
  - Descargar modelo de embeddings: `ollama pull nomic-embed-text:latest`
  - Verificar modelos disponibles: `ollama list`
  - _Requirements: 1.1, 1.2_

- [ ] 1.4 Crear migraciones de base de datos
  - Crear migración para tabla `chat_sessions`
  - Crear migración para tabla `chat_messages`
  - Crear migración para tabla `chat_message_chunks`
  - Ejecutar migraciones: `alembic upgrade head`
  - _Requirements: 8.1-8.6_

- [ ] 1.5 Crear configuración de RAG
  - Crear `src/shared/config/rag_config.py` con RAGConfig dataclass
  - Agregar variables de entorno en `.env.example`
  - Documentar configuración en README
  - _Requirements: 7.1-7.6_

- [ ] 2. Implementar Domain Layer
  - Crear Value Objects (MessageRole, SessionStatus)
  - Crear Aggregates (ChatSession, ChatMessage)
  - Crear Domain Events
  - Crear Domain Service interfaces
  - _Requirements: 4.1-4.7_

- [ ] 2.1 Crear Value Objects
  - Crear `src/chat/domain/value_objects/message_role.py` (Enum: user, assistant, system)
  - Crear `src/chat/domain/value_objects/session_status.py` (Enum: active, archived)
  - Crear `src/chat/domain/value_objects/chat_session_id.py`
  - Crear `src/chat/domain/value_objects/chat_message_id.py`
  - _Requirements: 4.1_

- [ ] 2.2 Crear ChatSession aggregate
  - Crear `src/chat/domain/aggregates/chat_session.py`
  - Implementar métodos: `add_message()`, `get_recent_messages()`, `archive()`
  - Implementar IAggregateRoot interface
  - Agregar domain events: ChatSessionCreated
  - _Requirements: 4.1, 4.2, 4.3, 4.7_

- [ ] 2.3 Crear ChatMessage entity
  - Crear `src/chat/domain/aggregates/chat_message.py`
  - Implementar campos: id, session_id, content, role, timestamps
  - Implementar tracking de chunks: `add_retrieved_chunk()`
  - Agregar campos de token usage
  - _Requirements: 4.2, 4.3, 8.4_

- [ ] 2.4 Crear Domain Events
  - Crear `src/chat/domain/events/chat_session_created.py`
  - Crear `src/chat/domain/events/message_sent.py`
  - Crear `src/chat/domain/events/message_received.py`
  - Todos deben heredar de IDomainEvent
  - _Requirements: Event-driven architecture_

- [ ] 2.5 Crear Domain Service interfaces
  - Crear `src/chat/domain/interfaces/external/llm_service.py` (ILLMService)
  - Crear `src/chat/domain/interfaces/external/retriever_service.py` (IRetrieverService)
  - Crear `src/chat/domain/interfaces/external/tokenizer.py` (ITokenizer)
  - Definir métodos abstractos para cada interface
  - _Requirements: 1.3, 2.1-2.6_

- [ ] 2.6 Crear Repository interfaces
  - Crear `src/chat/domain/interfaces/repositories/chat_session_read_repository.py`
  - Crear `src/chat/domain/interfaces/repositories/chat_session_write_repository.py`
  - Crear `src/chat/domain/interfaces/repositories/chat_message_read_repository.py`
  - Crear `src/chat/domain/interfaces/repositories/chat_message_write_repository.py`
  - _Requirements: 4.4, 8.1-8.3_

- [ ] 3. Implementar Domain Services
  - Crear RAGChatService
  - Crear PromptBuilderService
  - Crear ContextWindowManager
  - _Requirements: 2.1-2.6, 3.1-3.6_

- [ ] 3.1 Implementar RAGChatService
  - Crear `src/chat/domain/services/rag_chat_service.py`
  - Implementar `generate_response()` con flujo RAG completo
  - Coordinar retrieval, prompt building, y LLM generation
  - Agregar logging detallado en cada paso
  - _Requirements: 2.1-2.6, 3.1-3.6_

- [ ] 3.2 Implementar PromptBuilderService
  - Crear `src/chat/domain/services/prompt_builder_service.py`
  - Implementar `build_messages()` para construir lista de mensajes
  - Implementar `_build_system_message()` con formateo de chunks
  - Incluir instrucciones de citación en system prompt
  - _Requirements: 3.1, 3.2, 3.5_

- [ ] 3.3 Implementar ContextWindowManager
  - Crear `src/chat/domain/services/context_window_manager.py`
  - Implementar `fit_to_window()` con estrategia de truncamiento
  - Preservar system message y último user message
  - Truncar historial desde mensajes más antiguos
  - _Requirements: 3.3, 4.5_

- [ ] 4. Implementar Infrastructure - LangChain Integration
  - Crear OllamaChatModel wrapper
  - Crear PgVectorRetriever
  - Crear OllamaEmbeddingService
  - Crear TiktokenTokenizer
  - _Requirements: 1.1-1.5, 2.1-2.6_

- [ ] 4.1 Implementar OllamaChatModel
  - Crear `src/chat/infra/langchain/ollama_chat_model.py`
  - Wrapper para ChatOllama de langchain-ollama
  - Implementar `generate_stream()` con async streaming
  - Implementar `_convert_messages()` para formato LangChain
  - Manejar errores de conexión con retry
  - _Requirements: 1.1, 1.3, 1.5, 5.1-5.4_

- [ ] 4.2 Write property test for OllamaChatModel streaming
  - **Property 18: Token Order Preservation**
  - **Validates: Requirements 5.2**

- [ ] 4.3 Implementar PgVectorRetriever
  - Crear `src/chat/infra/langchain/pgvector_retriever.py`
  - Heredar de BaseRetriever de LangChain
  - Implementar `retrieve()` con búsqueda por similitud
  - Usar IContentChunkReadRepository existente
  - Aplicar threshold y top-k filtering
  - _Requirements: 2.1-2.6_

- [ ] 4.4 Write property test for PgVectorRetriever
  - **Property 6: Top-K Results**
  - **Property 7: Similarity Threshold Filtering**
  - **Validates: Requirements 2.3, 2.4**

- [ ] 4.5 Implementar OllamaEmbeddingService
  - Crear `src/chat/infra/external/ollama_embedding_service.py`
  - Usar modelo nomic-embed-text vía Ollama
  - Implementar `generate_embedding()` para queries
  - Cachear embeddings de queries frecuentes (opcional)
  - _Requirements: 2.1_

- [ ] 4.6 Implementar TiktokenTokenizer
  - Crear `src/chat/infra/external/tiktoken_tokenizer.py`
  - Usar tiktoken para conteo de tokens
  - Implementar `count_tokens()` para strings
  - Configurar encoding apropiado para el modelo
  - _Requirements: 3.3, 4.5_

- [ ] 5. Implementar Persistence Layer
  - Crear ORM models
  - Crear Mappers
  - Crear Repository implementations
  - _Requirements: 8.1-8.6_

- [ ] 5.1 Crear ORM Models
  - Crear `src/chat/infra/persistence/models/chat_session_model.py`
  - Crear `src/chat/infra/persistence/models/chat_message_model.py`
  - Crear `src/chat/infra/persistence/models/chat_message_chunk_model.py`
  - Definir relationships entre modelos
  - _Requirements: 8.1-8.3_

- [ ] 5.2 Crear Mappers
  - Crear `src/chat/infra/persistence/mappers/chat_session_mapper.py`
  - Crear `src/chat/infra/persistence/mappers/chat_message_mapper.py`
  - Implementar `to_domain()` y `to_model()` para cada mapper
  - _Requirements: 8.1-8.3_

- [ ] 5.3 Implementar ChatSession repositories
  - Crear `src/chat/infra/persistence/repositories/chat_session_read_repository.py`
  - Crear `src/chat/infra/persistence/repositories/chat_session_write_repository.py`
  - Implementar métodos CRUD básicos
  - Implementar `find_by_user_id()`, `find_active()`, etc.
  - _Requirements: 4.1, 4.4, 4.6, 8.1_

- [ ] 5.4 Write property test for session persistence
  - **Property 15: Session Persistence Round-Trip**
  - **Validates: Requirements 4.4**

- [ ] 5.5 Implementar ChatMessage repositories
  - Crear `src/chat/infra/persistence/repositories/chat_message_read_repository.py`
  - Crear `src/chat/infra/persistence/repositories/chat_message_write_repository.py`
  - Implementar `find_by_session_id()` con paginación
  - Implementar tracking de chunks usados
  - _Requirements: 4.2, 4.3, 8.2, 8.3, 8.4_

- [ ] 5.6 Write property test for message persistence
  - **Property 22: Message Persistence**
  - **Property 23: Chunk Association Tracking**
  - **Validates: Requirements 8.2, 8.3, 8.4**

- [ ] 6. Implementar Application Layer - Commands
  - Crear CreateChatSessionCommand
  - Crear SendMessageCommand
  - Crear DeleteChatSessionCommand
  - _Requirements: 4.1, 4.2, 4.7, 6.1, 6.2, 6.5_

- [ ] 6.1 Implementar CreateChatSessionCommand
  - Crear `src/chat/app/commands/create_chat_session/command.py`
  - Crear `src/chat/app/commands/create_chat_session/handler.py`
  - Crear `src/chat/app/commands/create_chat_session/result.py`
  - Usar ChatSession aggregate para crear sesión
  - Persistir usando write repository
  - _Requirements: 4.1, 6.1_

- [ ] 6.2 Write property test for session creation
  - **Property 14: Unique Session IDs**
  - **Validates: Requirements 4.1**

- [ ] 6.3 Implementar SendMessageCommand
  - Crear `src/chat/app/commands/send_message/command.py`
  - Crear `src/chat/app/commands/send_message/handler.py`
  - Crear `src/chat/app/commands/send_message/result.py`
  - Crear `src/chat/app/commands/send_message/mapper.py`
  - Usar RAGChatService para generar respuesta
  - Persistir mensaje de usuario y respuesta del asistente
  - Trackear chunks usados
  - _Requirements: 4.2, 4.3, 6.2, 8.2, 8.3, 8.4_

- [ ] 6.4 Write property test for message sending
  - **Property 13: History Preservation**
  - **Validates: Requirements 3.6, 4.2, 4.3**

- [ ] 6.5 Implementar DeleteChatSessionCommand
  - Crear `src/chat/app/commands/delete_chat_session/command.py`
  - Crear `src/chat/app/commands/delete_chat_session/handler.py`
  - Crear `src/chat/app/commands/delete_chat_session/result.py`
  - Usar write repository para eliminar
  - Verificar cascade delete de mensajes
  - _Requirements: 4.7, 6.5_

- [ ] 6.6 Write property test for cascade delete
  - **Property 17: Cascade Delete**
  - **Validates: Requirements 4.7**

- [ ] 7. Implementar Application Layer - Queries
  - Crear GetChatHistoryQuery
  - Crear ListChatSessionsQuery
  - Crear GetMessageContextQuery
  - _Requirements: 4.4, 4.6, 6.3, 6.4, 6.6_

- [ ] 7.1 Implementar GetChatHistoryQuery
  - Crear `src/chat/app/queries/get_chat_history/query.py`
  - Crear `src/chat/app/queries/get_chat_history/handler.py`
  - Crear `src/chat/app/queries/get_chat_history/dto.py`
  - Usar read repository para cargar mensajes
  - Incluir metadata de chunks usados
  - _Requirements: 4.4, 6.3_

- [ ] 7.2 Implementar ListChatSessionsQuery
  - Crear `src/chat/app/queries/list_chat_sessions/query.py`
  - Crear `src/chat/app/queries/list_chat_sessions/handler.py`
  - Crear `src/chat/app/queries/list_chat_sessions/dto.py`
  - Implementar paginación
  - Ordenar por updated_at DESC
  - _Requirements: 4.6, 6.4_

- [ ] 7.3 Write property test for session ordering
  - **Property 16: Session Ordering**
  - **Validates: Requirements 4.6**

- [ ] 7.4 Implementar GetMessageContextQuery
  - Crear `src/chat/app/queries/get_message_context/query.py`
  - Crear `src/chat/app/queries/get_message_context/handler.py`
  - Crear `src/chat/app/queries/get_message_context/dto.py`
  - Cargar chunks asociados al mensaje
  - Incluir metadata completa de cada chunk
  - _Requirements: 6.6_

- [ ] 8. Implementar Presentation Layer - REST API
  - Crear routers para chat
  - Implementar endpoints REST
  - Implementar streaming con SSE
  - Agregar error handling
  - _Requirements: 6.1-6.6, 5.1-5.5_

- [ ] 8.1 Crear Chat Router
  - Crear `src/chat/presentation/routers/chat.py`
  - Configurar prefix `/api/v1/chat`
  - Agregar tags para documentación
  - Registrar en FastAPI app
  - _Requirements: 6.1-6.6_

- [ ] 8.2 Implementar endpoint POST /sessions
  - Crear schema de request: CreateSessionRequest
  - Crear schema de response: SessionResponse
  - Enviar CreateChatSessionCommand
  - Retornar 201 Created con session_id
  - _Requirements: 6.1_

- [ ] 8.3 Implementar endpoint POST /sessions/{session_id}/messages con SSE
  - Crear schema de request: SendMessageRequest
  - Implementar streaming con StreamingResponse
  - Enviar SendMessageCommand
  - Transmitir tokens vía Server-Sent Events
  - Enviar evento "done" al finalizar
  - _Requirements: 6.2, 5.1-5.5_

- [ ]* 8.4 Write property test for streaming completion
  - **Property 19: Stream Completion Event**
  - **Validates: Requirements 5.3**

- [ ] 8.5 Implementar endpoint GET /sessions/{session_id}/messages
  - Crear schema de response: ChatHistoryResponse
  - Enviar GetChatHistoryQuery
  - Incluir chunks usados y token usage
  - _Requirements: 6.3_

- [ ] 8.6 Implementar endpoint GET /sessions
  - Crear schema de response: SessionListResponse
  - Enviar ListChatSessionsQuery
  - Implementar paginación con query params
  - _Requirements: 6.4_

- [ ] 8.7 Implementar endpoint DELETE /sessions/{session_id}
  - Enviar DeleteChatSessionCommand
  - Retornar 204 No Content
  - Manejar session not found (404)
  - _Requirements: 6.5_

- [ ] 8.8 Implementar endpoint GET /sessions/{session_id}/messages/{message_id}/context
  - Crear schema de response: MessageContextResponse
  - Enviar GetMessageContextQuery
  - Incluir chunks con metadata completa
  - _Requirements: 6.6_

- [ ] 8.9 Implementar error handling global
  - Crear exception handlers para ChatException
  - Manejar OllamaConnectionException (503)
  - Manejar ModelNotFoundException (400)
  - Manejar SessionNotFoundException (404)
  - Retornar responses estructurados con detalles
  - _Requirements: 9.1-9.6_

- [ ] 9. Implementar Dependency Injection
  - Crear ChatContainer
  - Registrar factories para todos los componentes
  - Registrar handlers en Mediator
  - _Requirements: Arquitectura general_

- [ ] 9.1 Crear ChatContainer
  - Crear `src/chat/container.py`
  - Heredar de DeclarativeContainer
  - Definir factories para repositories
  - Definir factories para services
  - Definir factories para handlers
  - _Requirements: DI pattern_

- [ ] 9.2 Registrar command handlers
  - Registrar CreateChatSessionHandler
  - Registrar SendMessageHandler
  - Registrar DeleteChatSessionHandler
  - Usar `register_handler()` del Mediator
  - _Requirements: Handler registration_

- [ ] 9.3 Registrar query handlers
  - Registrar GetChatHistoryHandler
  - Registrar ListChatSessionsHandler
  - Registrar GetMessageContextHandler
  - Usar `register_handler()` del Mediator
  - _Requirements: Handler registration_

- [ ] 9.4 Integrar ChatContainer en main.py
  - Importar ChatContainer en `src/main.py`
  - Inicializar container en startup
  - Llamar `register_pipeline_handlers()`
  - Verificar que handlers están registrados
  - _Requirements: Application startup_

- [ ] 10. Checkpoint - Verificar backend funcional
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Implementar Frontend - Agent Chat UI
  - Clonar Agent Chat UI
  - Configurar conexión con backend
  - Personalizar estilos
  - Agregar features custom
  - _Requirements: 13.1-13.6_

- [ ] 11.1 Setup Agent Chat UI
  - Clonar repositorio: `git clone https://github.com/langchain-ai/agent-chat-ui.git frontend/`
  - Instalar dependencias: `cd frontend && npm install`
  - Crear archivo `.env.local` con configuración
  - Configurar NEXT_PUBLIC_API_URL apuntando al backend
  - _Requirements: 13.1_

- [ ] 11.2 Crear adapter para Agent Chat UI
  - Crear `src/chat/presentation/adapters/agent_chat_ui_adapter.py`
  - Implementar `adapt_session_response()`
  - Implementar `adapt_message_response()`
  - Implementar `adapt_streaming_event()`
  - Actualizar endpoints para usar adapter
  - _Requirements: 13.2-13.5_

- [ ] 11.3 Configurar CORS
  - Agregar CORSMiddleware en `src/main.py`
  - Permitir origen de Agent Chat UI (localhost:3000)
  - Configurar allow_credentials, methods, headers
  - _Requirements: Frontend integration_

- [ ] 11.4 Personalizar Agent Chat UI
  - Actualizar branding (logo, colores)
  - Personalizar mensajes de bienvenida
  - Agregar visualización de chunks usados
  - Agregar indicadores de token usage
  - _Requirements: 13.3-13.5_

- [ ] 11.5 Implementar visualización de citaciones
  - Detectar patrón [Fuente N] en respuestas
  - Renderizar citaciones con estilo especial
  - Agregar tooltips con metadata de chunks
  - Hacer citaciones clickeables para ver chunk completo
  - _Requirements: 13.4_

- [ ] 12. Testing comprehensivo
  - Unit tests para domain services
  - Integration tests con Ollama
  - E2E tests del flujo completo
  - Property-based tests
  - _Requirements: 11.1-11.5_

- [ ]* 12.1 Write unit tests for RAGChatService
  - Test generate_response con chunks
  - Test generate_response sin chunks
  - Test manejo de errores de retrieval
  - _Requirements: 2.1-2.6_

- [ ]* 12.2 Write unit tests for PromptBuilderService
  - Test build_messages con contexto
  - Test inclusión de historial
  - Test manejo de chunks vacíos
  - _Requirements: 3.1, 3.2, 3.5_

- [ ]* 12.3 Write unit tests for ContextWindowManager
  - Test truncamiento dentro de límite
  - Test preservación de system y user message
  - Test truncamiento de historial
  - _Requirements: 3.3, 4.5_

- [ ]* 12.4 Write integration tests con Ollama
  - Test conexión a Ollama
  - Test generación de embeddings
  - Test streaming de respuestas
  - Test manejo de Ollama unavailable
  - _Requirements: 1.1-1.5_

- [ ]* 12.5 Write integration tests con pgvector
  - Test retrieval de chunks
  - Test aplicación de threshold
  - Test aplicación de filtros
  - _Requirements: 2.1-2.6_

- [ ]* 12.6 Write E2E tests del flujo completo
  - Test crear sesión → enviar mensaje → recibir respuesta
  - Test conversación multi-turno
  - Test persistencia de historial
  - _Requirements: 4.1-4.7, 6.1-6.6_

- [ ] 13. Documentación
  - Actualizar README con instrucciones
  - Documentar API con OpenAPI/Swagger
  - Crear guía de configuración
  - Crear guía de troubleshooting
  - _Requirements: 12.1-12.5_

- [ ] 13.1 Actualizar README.md
  - Agregar sección de Chat RAG
  - Documentar prerequisitos (Ollama, modelos)
  - Agregar instrucciones de instalación
  - Agregar ejemplos de uso
  - _Requirements: 12.2_

- [ ] 13.2 Documentar API REST
  - Verificar que FastAPI genera OpenAPI automáticamente
  - Agregar descripciones detalladas a endpoints
  - Agregar ejemplos de request/response
  - Documentar códigos de error
  - _Requirements: 12.1_

- [ ] 13.3 Crear guía de configuración
  - Documentar variables de entorno
  - Documentar parámetros de RAG
  - Documentar feature flags
  - Agregar valores recomendados
  - _Requirements: 12.3_

- [ ] 13.4 Crear guía de troubleshooting
  - Documentar errores comunes
  - Agregar soluciones para Ollama issues
  - Agregar soluciones para connection issues
  - Agregar tips de performance
  - _Requirements: 12.4_

- [ ] 14. Deployment
  - Crear Dockerfile
  - Crear docker-compose.yml
  - Configurar environment variables
  - Documentar deployment
  - _Requirements: Deployment architecture_

- [ ] 14.1 Crear Dockerfile para backend
  - Crear `Dockerfile` en raíz del proyecto
  - Usar Python 3.11+ como base
  - Instalar dependencias
  - Configurar entrypoint
  - _Requirements: Deployment_

- [ ] 14.2 Crear Dockerfile para frontend
  - Crear `frontend/Dockerfile`
  - Usar Node 20+ como base
  - Build Next.js app
  - Configurar entrypoint
  - _Requirements: Deployment_

- [ ] 14.3 Crear docker-compose.yml
  - Definir service: backend (FastAPI)
  - Definir service: frontend (Next.js)
  - Definir service: ollama
  - Definir service: postgres (con pgvector)
  - Configurar networks y volumes
  - _Requirements: Deployment architecture_

- [ ] 14.4 Documentar deployment
  - Crear `docs/DEPLOYMENT.md`
  - Documentar comandos de Docker
  - Documentar configuración de producción
  - Agregar checklist de deployment
  - _Requirements: Deployment_

- [ ] 15. Final Checkpoint - Sistema completo funcionando
  - Ensure all tests pass, ask the user if questions arise.
