# Design Document: LangChain RAG Chat UI con Ollama Multimodal

## Overview

Este documento describe el diseño técnico para implementar un sistema de chat conversacional con capacidades RAG (Retrieval-Augmented Generation) usando LangChain, Ollama y los embeddings existentes en el bounded context de Chunking.

El sistema permitirá a los usuarios hacer preguntas sobre los artículos procesados y recibir respuestas contextualizadas basadas en el contenido real de los artículos, con citación de fuentes.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Presentation Layer                      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Chat Router  │  │ SSE Endpoint │  │ WebSocket    │     │
│  │ (REST API)   │  │ (Streaming)  │  │ (Optional)   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│                    (Chat Bounded Context)                    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Commands & Queries                       │  │
│  │  • CreateChatSessionCommand                          │  │
│  │  • SendMessageCommand                                │  │
│  │  • GetChatHistoryQuery                               │  │
│  │  • ListChatSessionsQuery                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Domain Services                          │  │
│  │  • RAGChatService (orchestrates RAG flow)            │  │
│  │  • PromptBuilderService                              │  │
│  │  • ContextWindowManager                              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                       │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  LangChain   │  │   Ollama     │  │  pgvector    │     │
│  │  Integration │  │   Client     │  │  Retriever   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    External Services                         │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Ollama     │  │  PostgreSQL  │  │   Chunking   │     │
│  │   Server     │  │  + pgvector  │  │   BC (Read)  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### RAG Flow Architecture

```
User Query
    ↓
┌─────────────────────────────────────┐
│  1. Query Embedding Generation      │
│     (nomic-embed-text via Ollama)   │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  2. Vector Similarity Search        │
│     (pgvector retriever)            │
│     • Top-k chunks (default: 5)     │
│     • Similarity threshold: 0.7     │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  3. Context Assembly                │
│     • Format chunks with metadata   │
│     • Apply token limits            │
│     • Build structured prompt       │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  4. LLM Generation                  │
│     (llama3.2-vision via Ollama)    │
│     • Streaming response            │
│     • Citation of sources           │
└─────────────────────────────────────┘
    ↓
Response to User
```


## Components and Interfaces

### 1. Chat Bounded Context

Nuevo bounded context dedicado a funcionalidad de chat conversacional.

**Estructura:**
```
src/chat/
├── domain/
│   ├── aggregates/
│   │   ├── chat_session.py          # Aggregate root
│   │   └── chat_message.py          # Entity
│   ├── value_objects/
│   │   ├── message_role.py          # Enum: user, assistant, system
│   │   └── session_status.py        # Enum: active, archived
│   ├── services/
│   │   ├── rag_chat_service.py      # Orchestrates RAG flow
│   │   ├── prompt_builder_service.py # Builds prompts
│   │   └── context_window_manager.py # Manages token limits
│   ├── interfaces/
│   │   ├── repositories/
│   │   │   ├── chat_session_repository.py
│   │   │   └── chat_message_repository.py
│   │   └── external/
│   │       ├── llm_service.py       # Interface for LLM
│   │       └── retriever_service.py # Interface for retrieval
│   └── events/
│       ├── chat_session_created.py
│       ├── message_sent.py
│       └── message_received.py
├── app/
│   ├── commands/
│   │   ├── create_chat_session/
│   │   ├── send_message/
│   │   └── delete_chat_session/
│   └── queries/
│       ├── get_chat_history/
│       ├── list_chat_sessions/
│       └── get_message_context/
└── infra/
    ├── langchain/
    │   ├── ollama_chat_model.py     # ChatOllama wrapper
    │   ├── pgvector_retriever.py    # Custom retriever
    │   └── rag_chain.py             # RAG chain implementation
    ├── persistence/
    │   ├── models/
    │   │   ├── chat_session_model.py
    │   │   ├── chat_message_model.py
    │   │   └── message_chunk_model.py
    │   ├── repositories/
    │   │   ├── chat_session_repository.py
    │   │   └── chat_message_repository.py
    │   └── mappers/
    │       ├── chat_session_mapper.py
    │       └── chat_message_mapper.py
    └── external/
        └── ollama_client.py         # Ollama HTTP client
```

### 2. Domain Aggregates

#### ChatSession (Aggregate Root)

```python
@dataclass
class ChatSession(IAggregateRoot):
    """
    Chat session aggregate root.
    
    Representa una sesión de conversación con historial de mensajes.
    """
    id: ChatSessionId
    user_id: Optional[UserId]  # Optional for anonymous sessions
    title: str
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    
    # Aggregated entities
    _messages: List[ChatMessage] = field(default_factory=list)
    
    # Domain events
    _domain_events: List[IDomainEvent] = field(default_factory=list)
    
    def add_message(self, content: str, role: MessageRole) -> ChatMessage:
        """Add message to session."""
        message = ChatMessage(
            id=ChatMessageId.generate(),
            session_id=self.id,
            content=content,
            role=role,
            created_at=datetime.utcnow()
        )
        self._messages.append(message)
        self.updated_at = datetime.utcnow()
        
        # Emit event
        if role == MessageRole.USER:
            self._domain_events.append(MessageSent(
                session_id=str(self.id),
                message_id=str(message.id),
                content=content
            ))
        
        return message
    
    def get_recent_messages(self, limit: int = 10) -> List[ChatMessage]:
        """Get recent messages for context."""
        return self._messages[-limit:]
    
    def archive(self) -> None:
        """Archive session."""
        self.status = SessionStatus.ARCHIVED
        self.updated_at = datetime.utcnow()
```

#### ChatMessage (Entity)

```python
@dataclass
class ChatMessage:
    """
    Chat message entity.
    
    Representa un mensaje individual en una sesión de chat.
    """
    id: ChatMessageId
    session_id: ChatSessionId
    content: str
    role: MessageRole  # user, assistant, system
    created_at: datetime
    
    # RAG metadata
    retrieved_chunk_ids: List[str] = field(default_factory=list)
    similarity_scores: Dict[str, float] = field(default_factory=dict)
    
    # Token usage
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    
    def add_retrieved_chunk(self, chunk_id: str, score: float) -> None:
        """Record chunk used for RAG."""
        self.retrieved_chunk_ids.append(chunk_id)
        self.similarity_scores[chunk_id] = score
```


### 3. Domain Services

#### RAGChatService

```python
class RAGChatService:
    """
    Service for orchestrating RAG chat flow.
    
    Coordinates retrieval, prompt building, and LLM generation.
    """
    
    def __init__(
        self,
        retriever: IRetrieverService,
        llm: ILLMService,
        prompt_builder: PromptBuilderService,
        context_manager: ContextWindowManager,
        logger: ILogger,
    ):
        self._retriever = retriever
        self._llm = llm
        self._prompt_builder = prompt_builder
        self._context_manager = context_manager
        self._logger = logger
    
    async def generate_response(
        self,
        query: str,
        session: ChatSession,
        config: RAGConfig,
    ) -> AsyncIterator[str]:
        """
        Generate streaming response using RAG.
        
        Args:
            query: User query
            session: Chat session with history
            config: RAG configuration
            
        Yields:
            Response tokens
        """
        # 1. Retrieve relevant chunks
        chunks = await self._retriever.retrieve(
            query=query,
            top_k=config.top_k,
            threshold=config.similarity_threshold,
            filters=config.filters,
        )
        
        self._logger.info(
            "Retrieved chunks for RAG",
            query=query,
            num_chunks=len(chunks),
            scores=[c.score for c in chunks],
        )
        
        # 2. Build prompt with context
        messages = self._prompt_builder.build_messages(
            query=query,
            chunks=chunks,
            history=session.get_recent_messages(),
            system_prompt=config.system_prompt,
        )
        
        # 3. Apply context window limits
        messages = self._context_manager.fit_to_window(
            messages=messages,
            max_tokens=config.max_context_tokens,
        )
        
        # 4. Generate streaming response
        async for token in self._llm.generate_stream(messages):
            yield token
```

#### PromptBuilderService

```python
class PromptBuilderService:
    """
    Service for building structured prompts.
    
    Formats context, history, and query into LLM messages.
    """
    
    def build_messages(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        history: List[ChatMessage],
        system_prompt: str,
    ) -> List[Message]:
        """
        Build message list for LLM.
        
        Args:
            query: User query
            chunks: Retrieved chunks with metadata
            history: Recent chat history
            system_prompt: System instructions
            
        Returns:
            List of messages for LLM
        """
        messages = []
        
        # 1. System message with instructions
        system_content = self._build_system_message(
            system_prompt=system_prompt,
            chunks=chunks,
        )
        messages.append(Message(role="system", content=system_content))
        
        # 2. Chat history (for multi-turn context)
        for msg in history:
            messages.append(Message(
                role=msg.role.value,
                content=msg.content,
            ))
        
        # 3. Current user query
        messages.append(Message(role="user", content=query))
        
        return messages
    
    def _build_system_message(
        self,
        system_prompt: str,
        chunks: List[RetrievedChunk],
    ) -> str:
        """Build system message with context."""
        if not chunks:
            return system_prompt
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[Fuente {i}] {chunk.metadata['article_title']}\n"
                f"Fecha: {chunk.metadata['published_at']}\n"
                f"Contenido: {chunk.content}\n"
            )
        
        context = "\n---\n".join(context_parts)
        
        return f"""{system_prompt}

Contexto relevante de artículos:

{context}

Instrucciones:
- Usa SOLO la información del contexto proporcionado para responder
- Si la respuesta no está en el contexto, indica que no tienes esa información
- Cita las fuentes usando el formato [Fuente N]
- Sé conciso y preciso
"""
```


#### ContextWindowManager

```python
class ContextWindowManager:
    """
    Service for managing context window limits.
    
    Ensures messages fit within model's token limits.
    """
    
    def __init__(self, tokenizer: ITokenizer):
        self._tokenizer = tokenizer
    
    def fit_to_window(
        self,
        messages: List[Message],
        max_tokens: int,
    ) -> List[Message]:
        """
        Truncate messages to fit token limit.
        
        Strategy:
        1. Always keep system message (with context)
        2. Always keep latest user message
        3. Truncate older history if needed
        
        Args:
            messages: List of messages
            max_tokens: Maximum tokens allowed
            
        Returns:
            Truncated message list
        """
        # Count tokens for each message
        token_counts = [
            self._tokenizer.count_tokens(msg.content)
            for msg in messages
        ]
        
        total_tokens = sum(token_counts)
        
        if total_tokens <= max_tokens:
            return messages
        
        # Keep system (index 0) and latest user (index -1)
        system_msg = messages[0]
        user_msg = messages[-1]
        history = messages[1:-1]
        
        # Calculate available tokens for history
        reserved = token_counts[0] + token_counts[-1]
        available = max_tokens - reserved
        
        # Truncate history from oldest
        truncated_history = []
        history_tokens = 0
        
        for msg, tokens in zip(reversed(history), reversed(token_counts[1:-1])):
            if history_tokens + tokens <= available:
                truncated_history.insert(0, msg)
                history_tokens += tokens
            else:
                break
        
        return [system_msg] + truncated_history + [user_msg]
```

### 4. Infrastructure - LangChain Integration

#### OllamaChatModel

```python
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

class OllamaChatModel(ILLMService):
    """
    Wrapper for ChatOllama from langchain-ollama.
    
    Provides streaming chat completions using Ollama.
    """
    
    def __init__(
        self,
        model: str = "llama3.2-vision:latest",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.7,
        logger: ILogger = None,
    ):
        self._chat_model = ChatOllama(
            model=model,
            base_url=base_url,
            temperature=temperature,
        )
        self._logger = logger or get_logger(__name__)
    
    async def generate_stream(
        self,
        messages: List[Message],
    ) -> AsyncIterator[str]:
        """
        Generate streaming response.
        
        Args:
            messages: List of messages
            
        Yields:
            Response tokens
        """
        # Convert to LangChain message format
        lc_messages = self._convert_messages(messages)
        
        try:
            async for chunk in self._chat_model.astream(lc_messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            self._logger.error(
                "Error generating response",
                error=str(e),
                model=self._chat_model.model,
            )
            raise LLMGenerationException(f"Failed to generate response: {e}")
    
    def _convert_messages(self, messages: List[Message]) -> List:
        """Convert domain messages to LangChain format."""
        lc_messages = []
        for msg in messages:
            if msg.role == "system":
                lc_messages.append(SystemMessage(content=msg.content))
            elif msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                lc_messages.append(AIMessage(content=msg.content))
        return lc_messages
```

#### PgVectorRetriever

```python
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document

class PgVectorRetriever(IRetrieverService, BaseRetriever):
    """
    Custom retriever using existing pgvector embeddings.
    
    Retrieves chunks from content_chunks table using similarity search.
    """
    
    def __init__(
        self,
        chunk_repository: IContentChunkReadRepository,
        embedding_service: IEmbeddingService,
        logger: ILogger,
    ):
        self._chunk_repo = chunk_repository
        self._embedding_service = embedding_service
        self._logger = logger
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.7,
        filters: Optional[Dict] = None,
    ) -> List[RetrievedChunk]:
        """
        Retrieve relevant chunks.
        
        Args:
            query: Search query
            top_k: Number of chunks to retrieve
            threshold: Minimum similarity score
            filters: Optional filters (article_id, source_id, etc.)
            
        Returns:
            List of retrieved chunks with scores
        """
        # 1. Generate query embedding
        query_embedding = await self._embedding_service.generate_embedding(query)
        
        # 2. Search in pgvector
        results = await self._chunk_repo.search_by_similarity(
            embedding=query_embedding,
            limit=top_k,
            threshold=threshold,
            filters=filters,
        )
        
        # 3. Convert to domain objects
        chunks = []
        for result in results:
            chunk = RetrievedChunk(
                id=result.id,
                content=result.content,
                score=result.similarity_score,
                metadata={
                    "article_id": result.article_id,
                    "article_title": result.article_title,
                    "source_name": result.source_name,
                    "published_at": result.published_at.isoformat(),
                    "chunk_index": result.chunk_index,
                },
            )
            chunks.append(chunk)
        
        self._logger.info(
            "Retrieved chunks",
            query=query,
            num_results=len(chunks),
            avg_score=sum(c.score for c in chunks) / len(chunks) if chunks else 0,
        )
        
        return chunks
    
    # LangChain BaseRetriever interface
    def _get_relevant_documents(self, query: str) -> List[Document]:
        """LangChain interface for retrieval."""
        import asyncio
        chunks = asyncio.run(self.retrieve(query))
        return [
            Document(
                page_content=chunk.content,
                metadata=chunk.metadata,
            )
            for chunk in chunks
        ]
```


## Data Models

### Database Schema

```sql
-- Chat sessions table
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NULL,  -- NULL for anonymous sessions
    title VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',  -- active, archived
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at DESC)
);

-- Chat messages table
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    role VARCHAR(20) NOT NULL,  -- user, assistant, system
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Token usage tracking
    prompt_tokens INTEGER NULL,
    completion_tokens INTEGER NULL,
    total_tokens INTEGER NULL,
    
    CONSTRAINT fk_session FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_created_at (created_at)
);

-- Message-chunk association (for RAG tracking)
CREATE TABLE chat_message_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL,
    chunk_id UUID NOT NULL,
    similarity_score FLOAT NOT NULL,
    rank INTEGER NOT NULL,  -- Order of relevance
    
    CONSTRAINT fk_message FOREIGN KEY (message_id) REFERENCES chat_messages(id) ON DELETE CASCADE,
    CONSTRAINT fk_chunk FOREIGN KEY (chunk_id) REFERENCES content_chunks(id) ON DELETE CASCADE,
    INDEX idx_message_id (message_id),
    INDEX idx_chunk_id (chunk_id)
);
```

### ORM Models

```python
# src/chat/infra/persistence/models/chat_session_model.py

from sqlalchemy import Column, String, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

class ChatSessionModel(Base):
    """ORM model for chat_sessions table."""
    
    __tablename__ = "chat_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    title = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = relationship("ChatMessageModel", back_populates="session", cascade="all, delete-orphan")
```

```python
# src/chat/infra/persistence/models/chat_message_model.py

class ChatMessageModel(Base):
    """ORM model for chat_messages table."""
    
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Token usage
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    
    # Relationships
    session = relationship("ChatSessionModel", back_populates="messages")
    chunks = relationship("ChatMessageChunkModel", back_populates="message", cascade="all, delete-orphan")
```

```python
# src/chat/infra/persistence/models/chat_message_chunk_model.py

class ChatMessageChunkModel(Base):
    """ORM model for chat_message_chunks table."""
    
    __tablename__ = "chat_message_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("chat_messages.id"), nullable=False)
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("content_chunks.id"), nullable=False)
    similarity_score = Column(Float, nullable=False)
    rank = Column(Integer, nullable=False)
    
    # Relationships
    message = relationship("ChatMessageModel", back_populates="chunks")
    chunk = relationship("ContentChunkModel")
```

## API Endpoints

### REST API

```python
# POST /api/v1/chat/sessions
# Create new chat session

Request:
{
    "title": "Preguntas sobre Python",
    "user_id": "uuid-optional"
}

Response: 201 Created
{
    "session_id": "uuid",
    "title": "Preguntas sobre Python",
    "status": "active",
    "created_at": "2024-12-12T10:00:00Z"
}
```

```python
# POST /api/v1/chat/sessions/{session_id}/messages
# Send message and get streaming response

Request:
{
    "content": "¿Qué es Python?",
    "config": {
        "top_k": 5,
        "similarity_threshold": 0.7,
        "max_context_tokens": 4096,
        "filters": {
            "source_id": "uuid-optional"
        }
    }
}

Response: 200 OK (Server-Sent Events)
Content-Type: text/event-stream

data: {"type": "token", "content": "Python"}
data: {"type": "token", "content": " es"}
data: {"type": "token", "content": " un"}
...
data: {"type": "done", "message_id": "uuid", "tokens": {"prompt": 150, "completion": 50}}
```

```python
# GET /api/v1/chat/sessions/{session_id}/messages
# Get chat history

Response: 200 OK
{
    "messages": [
        {
            "id": "uuid",
            "role": "user",
            "content": "¿Qué es Python?",
            "created_at": "2024-12-12T10:00:00Z",
            "chunks_used": []
        },
        {
            "id": "uuid",
            "role": "assistant",
            "content": "Python es un lenguaje...",
            "created_at": "2024-12-12T10:00:05Z",
            "chunks_used": [
                {
                    "chunk_id": "uuid",
                    "article_title": "Introducción a Python",
                    "similarity_score": 0.92
                }
            ],
            "tokens": {
                "prompt": 150,
                "completion": 50,
                "total": 200
            }
        }
    ],
    "total": 2
}
```

```python
# GET /api/v1/chat/sessions
# List chat sessions

Query params:
- page: int (default: 1)
- page_size: int (default: 20)
- status: str (optional: active, archived)

Response: 200 OK
{
    "sessions": [
        {
            "id": "uuid",
            "title": "Preguntas sobre Python",
            "status": "active",
            "message_count": 10,
            "created_at": "2024-12-12T10:00:00Z",
            "updated_at": "2024-12-12T11:00:00Z"
        }
    ],
    "total": 50,
    "page": 1,
    "page_size": 20
}
```

```python
# DELETE /api/v1/chat/sessions/{session_id}
# Delete chat session

Response: 204 No Content
```

```python
# GET /api/v1/chat/sessions/{session_id}/messages/{message_id}/context
# Get chunks used for a specific message

Response: 200 OK
{
    "message_id": "uuid",
    "chunks": [
        {
            "chunk_id": "uuid",
            "content": "Python es un lenguaje de programación...",
            "similarity_score": 0.92,
            "rank": 1,
            "metadata": {
                "article_id": "uuid",
                "article_title": "Introducción a Python",
                "source_name": "Python.org",
                "published_at": "2024-01-01T00:00:00Z",
                "chunk_index": 0
            }
        }
    ]
}
```


## Configuration

### RAG Configuration

```python
@dataclass
class RAGConfig:
    """Configuration for RAG chat."""
    
    # Model configuration
    model_name: str = "llama3.2-vision:latest"
    ollama_base_url: str = "http://localhost:11434"
    temperature: float = 0.7
    
    # Retrieval configuration
    top_k: int = 5
    similarity_threshold: float = 0.7
    
    # Context window configuration
    max_context_tokens: int = 4096
    max_history_messages: int = 10
    
    # Prompt configuration
    system_prompt: str = """Eres un asistente útil que responde preguntas basándose en artículos.
Usa SOLO la información del contexto proporcionado.
Si no sabes la respuesta, di que no tienes esa información.
Cita las fuentes usando [Fuente N]."""
    
    # Feature flags
    enable_rag: bool = True
    enable_streaming: bool = True
    enable_multimodal: bool = False
    
    # Performance
    timeout_seconds: int = 30
    max_retries: int = 3
```

### Environment Variables

```bash
# Ollama configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2-vision:latest
OLLAMA_TIMEOUT=30

# RAG configuration
RAG_TOP_K=5
RAG_SIMILARITY_THRESHOLD=0.7
RAG_MAX_CONTEXT_TOKENS=4096
RAG_ENABLE_STREAMING=true

# Feature flags
FEATURE_RAG_ENABLED=true
FEATURE_MULTIMODAL_ENABLED=false

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname
```

## Error Handling

### Exception Hierarchy

```python
class ChatException(Exception):
    """Base exception for chat errors."""
    pass

class OllamaConnectionException(ChatException):
    """Ollama server not available."""
    pass

class ModelNotFoundException(ChatException):
    """Requested model not found in Ollama."""
    pass

class LLMGenerationException(ChatException):
    """Error during LLM generation."""
    pass

class RetrievalException(ChatException):
    """Error during chunk retrieval."""
    pass

class ContextWindowExceededException(ChatException):
    """Context exceeds model's token limit."""
    pass

class SessionNotFoundException(ChatException):
    """Chat session not found."""
    pass
```

### Error Responses

```python
# 503 Service Unavailable - Ollama not available
{
    "error": "service_unavailable",
    "message": "Ollama server is not available",
    "details": {
        "base_url": "http://localhost:11434",
        "suggestion": "Ensure Ollama is running: ollama serve"
    }
}

# 400 Bad Request - Model not found
{
    "error": "model_not_found",
    "message": "Model 'llama3.2-vision' not found",
    "details": {
        "available_models": ["llama3.2:latest", "mistral:latest"],
        "suggestion": "Pull model: ollama pull llama3.2-vision"
    }
}

# 400 Bad Request - Query too long
{
    "error": "query_too_long",
    "message": "Query exceeds maximum length",
    "details": {
        "max_length": 2000,
        "actual_length": 2500
    }
}

# 504 Gateway Timeout
{
    "error": "timeout",
    "message": "Request timed out after 30 seconds",
    "details": {
        "timeout_seconds": 30
    }
}
```

## Testing Strategy

### Unit Tests

```python
# Test RAGChatService
class TestRAGChatService:
    async def test_generate_response_with_chunks(self):
        """Should generate response using retrieved chunks."""
        pass
    
    async def test_generate_response_without_chunks(self):
        """Should generate response without RAG when no chunks found."""
        pass
    
    async def test_handles_retrieval_error_gracefully(self):
        """Should continue without RAG if retrieval fails."""
        pass

# Test PromptBuilderService
class TestPromptBuilderService:
    def test_builds_system_message_with_context(self):
        """Should format chunks into system message."""
        pass
    
    def test_includes_chat_history(self):
        """Should include recent messages for context."""
        pass
    
    def test_handles_empty_chunks(self):
        """Should build prompt without context when no chunks."""
        pass

# Test ContextWindowManager
class TestContextWindowManager:
    def test_fits_messages_within_limit(self):
        """Should truncate history to fit token limit."""
        pass
    
    def test_preserves_system_and_latest_user_message(self):
        """Should always keep system and current query."""
        pass
```

### Integration Tests

```python
@pytest.mark.integration
class TestOllamaChatModel:
    async def test_generates_streaming_response(self):
        """Should stream tokens from Ollama."""
        pass
    
    async def test_handles_ollama_unavailable(self):
        """Should raise OllamaConnectionException."""
        pass

@pytest.mark.integration
class TestPgVectorRetriever:
    async def test_retrieves_relevant_chunks(self):
        """Should retrieve chunks from pgvector."""
        pass
    
    async def test_applies_similarity_threshold(self):
        """Should filter chunks below threshold."""
        pass
    
    async def test_applies_filters(self):
        """Should filter by article_id, source_id."""
        pass
```

### E2E Tests

```python
@pytest.mark.e2e
class TestChatFlow:
    async def test_complete_chat_flow(self):
        """Should complete full chat flow with RAG."""
        # 1. Create session
        # 2. Send message
        # 3. Verify streaming response
        # 4. Verify chunks were used
        # 5. Verify message persisted
        pass
    
    async def test_multi_turn_conversation(self):
        """Should maintain context across turns."""
        pass
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Model Validation

*For any* model name configured, the system should validate that the model exists in Ollama before attempting to use it, and should provide a clear error message with available models if validation fails.

**Validates: Requirements 1.2**

### Property 2: Streaming Response Format

*For any* message sent to the model, the system should receive responses in streaming format (token by token), not as a single complete response.

**Validates: Requirements 1.3, 5.1**

### Property 3: Connection Retry with Backoff

*For any* connection error to Ollama, the system should retry the connection with exponentially increasing delays, and should log each retry attempt.

**Validates: Requirements 1.5**

### Property 4: Query Embedding Consistency

*For any* user query, the system should generate an embedding using the same model (nomic-embed-text) that was used to generate the chunk embeddings, ensuring compatibility for similarity search.

**Validates: Requirements 2.1**

### Property 5: Cosine Similarity Search

*For any* retrieval operation, the system should use cosine similarity as the distance metric when querying the vector store.

**Validates: Requirements 2.2**

### Property 6: Top-K Results

*For any* retrieval with parameter k, the system should return exactly k chunks (or fewer if insufficient chunks exist), ordered by similarity score descending.

**Validates: Requirements 2.3**

### Property 7: Similarity Threshold Filtering

*For any* retrieval with threshold t, all returned chunks should have similarity scores >= t.

**Validates: Requirements 2.4**

### Property 8: Filter Application

*For any* retrieval with filters (article_id, source_id, date range), all returned chunks should satisfy the specified filters.

**Validates: Requirements 2.5**

### Property 9: Metadata Completeness

*For any* retrieved chunk, the system should include all required metadata fields: article_title, source_name, published_at, chunk_index.

**Validates: Requirements 2.6**

### Property 10: Prompt Instructions Inclusion

*For any* prompt generated, the system should include clear instructions about how to use the provided context and how to cite sources.

**Validates: Requirements 3.1, 3.5**

### Property 11: Chunk Formatting Consistency

*For any* chunk added to the prompt, the system should format it with its metadata (title, source, date) in a consistent structure.

**Validates: Requirements 3.2**

### Property 12: Context Window Truncation

*For any* prompt that exceeds the token limit, the system should truncate older history messages while preserving the system message and the current user query.

**Validates: Requirements 3.3, 4.5**

### Property 13: History Preservation

*For any* multi-turn conversation, the system should preserve the complete message history in the session, maintaining chronological order.

**Validates: Requirements 3.6, 4.2, 4.3**

### Property 14: Unique Session IDs

*For any* two chat sessions created, they should have different unique identifiers.

**Validates: Requirements 4.1**

### Property 15: Session Persistence Round-Trip

*For any* chat session with messages, creating the session, adding messages, and then retrieving it should return the same messages in the same order.

**Validates: Requirements 4.4**

### Property 16: Session Ordering

*For any* list of sessions retrieved, they should be ordered by updated_at timestamp in descending order (most recent first).

**Validates: Requirements 4.6**

### Property 17: Cascade Delete

*For any* session that is deleted, all associated messages should also be deleted from the database.

**Validates: Requirements 4.7**

### Property 18: Token Order Preservation

*For any* streaming response, tokens should be transmitted in the correct sequential order without reordering.

**Validates: Requirements 5.2**

### Property 19: Stream Completion Event

*For any* completed streaming response, the system should send a final "done" event indicating completion and including token usage statistics.

**Validates: Requirements 5.3**

### Property 20: Error Event on Failure

*For any* error during streaming, the system should send an error event with details and close the stream gracefully.

**Validates: Requirements 5.4**

### Property 21: Configuration Application

*For any* RAG configuration parameter (top_k, threshold, max_tokens), the system should apply the configured value in all operations.

**Validates: Requirements 7.1-7.6**

### Property 22: Message Persistence

*For any* message sent or received, the system should persist it to the database with all required fields (role, content, timestamps).

**Validates: Requirements 8.1-8.3**

### Property 23: Chunk Association Tracking

*For any* assistant message generated using RAG, the system should store references to all chunks used, including their similarity scores and ranks.

**Validates: Requirements 8.4**

### Property 24: Logging Completeness

*For any* chat operation (query, retrieval, generation), the system should log relevant information including query text, number of chunks, scores, and timing.

**Validates: Requirements 10.1-10.4**


## Deployment and Operations

### Prerequisites

1. **Ollama Installation**
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.com/install.sh | sh
   
   # Start Ollama server
   ollama serve
   
   # Pull required models
   ollama pull llama3.2-vision:latest
   ollama pull nomic-embed-text:latest
   ```

2. **Database Migration**
   ```bash
   # Create chat tables
   alembic revision --autogenerate -m "Add chat tables"
   alembic upgrade head
   ```

3. **Environment Configuration**
   ```bash
   # Copy example config
   cp .env.example .env
   
   # Edit configuration
   vim .env
   ```

### Monitoring

**Key Metrics to Track:**
- Chat session creation rate
- Message throughput (messages/second)
- Average response latency (TTFB, total)
- Token generation rate (tokens/second)
- Retrieval latency
- Cache hit rate (if caching implemented)
- Error rate by type
- Ollama server health

**Logging Strategy:**
- Structured logging with correlation IDs
- Log levels: DEBUG for development, INFO for production
- Sensitive data filtering (user queries may contain PII)
- Log aggregation to centralized system

### Performance Optimization

1. **Caching Strategy**
   - Cache query embeddings for frequent queries
   - Cache retrieved chunks for popular queries
   - TTL: 1 hour for embeddings, 30 minutes for chunks

2. **Connection Pooling**
   - Maintain persistent connections to Ollama
   - Pool size: 10-20 connections
   - Connection timeout: 30 seconds

3. **Batch Processing**
   - Batch embedding generation when possible
   - Batch database writes for message history

4. **Resource Limits**
   - Max concurrent chat sessions: 100
   - Max message length: 2000 characters
   - Max context tokens: 4096
   - Request timeout: 30 seconds

## Security Considerations

### Input Validation

- Sanitize user queries to prevent injection attacks
- Validate session IDs to prevent unauthorized access
- Limit query length to prevent DoS
- Rate limiting per user/IP

### Data Privacy

- Optional user authentication
- Session isolation (users can only access their sessions)
- PII detection and masking in logs
- Secure storage of chat history

### Model Safety

- Content filtering for inappropriate queries
- Response validation for harmful content
- Audit logging of all interactions
- Ability to disable specific models

## Migration Strategy

### Phase 1: Infrastructure Setup
1. Deploy Ollama server
2. Create database tables
3. Configure environment variables

### Phase 2: Core Implementation
1. Implement domain models and services
2. Implement LangChain integration
3. Implement persistence layer

### Phase 3: API Development
1. Implement REST endpoints
2. Implement streaming support
3. Add error handling

### Phase 4: Testing and Validation
1. Unit tests for all components
2. Integration tests with Ollama
3. E2E tests for complete flows
4. Performance testing

### Phase 5: Production Deployment
1. Deploy to staging environment
2. Load testing and optimization
3. Security audit
4. Production deployment

## Future Enhancements

### Short-term (Next Sprint)
- [ ] Add conversation summarization for long sessions
- [ ] Implement query rewriting for better retrieval
- [ ] Add support for filtering by date ranges
- [ ] Implement caching layer

### Medium-term (Next Quarter)
- [ ] Add support for multimodal inputs (images)
- [ ] Implement conversation branching
- [ ] Add support for multiple users per session
- [ ] Implement feedback mechanism (thumbs up/down)

### Long-term (Future)
- [ ] Add support for voice input/output
- [ ] Implement agentic RAG (LLM decides when to retrieve)
- [ ] Add support for external knowledge sources
- [ ] Implement fine-tuning on user feedback

## Dependencies

### Python Packages

```txt
# LangChain
langchain>=0.1.0
langchain-core>=0.1.0
langchain-ollama>=0.1.0

# Vector store
pgvector>=0.2.0

# Async support
aiohttp>=3.9.0
asyncio>=3.4.3

# Existing dependencies
sqlalchemy>=2.0.0
alembic>=1.12.0
fastapi>=0.104.0
pydantic>=2.5.0
```

### External Services

- **Ollama**: Local LLM server (required)
- **PostgreSQL with pgvector**: Vector database (existing)
- **Chunking BC**: Source of embeddings (existing)

## References

- **LangChain Documentation**: https://docs.langchain.com
- **Ollama Documentation**: https://ollama.com/docs
- **pgvector Documentation**: https://github.com/pgvector/pgvector
- **RAG Best Practices**: https://docs.langchain.com/oss/python/langchain/rag
- **Streaming with FastAPI**: https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse

## Appendix: Example Prompts

### System Prompt Template

```
Eres un asistente experto que responde preguntas sobre artículos técnicos.

CONTEXTO DISPONIBLE:
{context}

INSTRUCCIONES:
1. Usa ÚNICAMENTE la información del contexto proporcionado
2. Si la respuesta no está en el contexto, indica claramente que no tienes esa información
3. Cita las fuentes usando el formato [Fuente N] donde N es el número de la fuente
4. Sé conciso y preciso en tus respuestas
5. Si hay información contradictoria, menciona ambas perspectivas
6. Responde en español

FORMATO DE RESPUESTA:
- Respuesta directa a la pregunta
- Citas de fuentes relevantes
- Información adicional si es pertinente
```

### Context Format Template

```
[Fuente 1] {article_title}
Fuente: {source_name}
Fecha: {published_at}
Contenido: {chunk_content}

---

[Fuente 2] {article_title}
Fuente: {source_name}
Fecha: {published_at}
Contenido: {chunk_content}
```

## Glossary

- **RAG**: Retrieval-Augmented Generation
- **LLM**: Large Language Model
- **SSE**: Server-Sent Events
- **TTFB**: Time To First Byte
- **Embedding**: Vector representation of text
- **Chunk**: Fragment of article content
- **Context Window**: Maximum tokens the model can process
- **Token**: Unit of text (roughly 0.75 words)
- **Similarity Score**: Cosine similarity between embeddings (0-1)
- **Top-K**: Retrieve top K most similar results


## Frontend UI Options

### Opción 1: Agent Chat UI (Recomendada)

**Agent Chat UI** es una aplicación Next.js oficial de LangChain que proporciona una interfaz conversacional lista para usar.

**Características:**
- ✅ Interfaz de chat moderna y responsiva
- ✅ Soporte para streaming en tiempo real
- ✅ Visualización de herramientas (tools)
- ✅ Time-travel debugging
- ✅ State forking
- ✅ Open source y personalizable
- ✅ Integración nativa con LangChain agents

**Implementación:**
```bash
# Clonar Agent Chat UI
git clone https://github.com/langchain-ai/agent-chat-ui.git frontend/

# Configurar
cd frontend/
npm install

# Configurar endpoint de API
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1/chat
```

**Integración con nuestro backend:**
- El Agent Chat UI se conecta a nuestra API REST
- Usa Server-Sent Events para streaming
- Requiere adaptar nuestros endpoints al formato esperado por Agent Chat UI

### Opción 2: assistant-ui (React Framework)

**assistant-ui** es un framework React para construir interfaces de chat AI con soporte para streaming.

**Características:**
- ✅ Componentes React reutilizables
- ✅ Soporte para streaming
- ✅ Integración con LangGraph
- ✅ Personalizable
- ✅ TypeScript

**Implementación:**
```bash
npm install @assistant-ui/react
```

```tsx
import { AssistantRuntimeProvider, Thread } from "@assistant-ui/react";

function ChatInterface() {
  return (
    <AssistantRuntimeProvider>
      <Thread />
    </AssistantRuntimeProvider>
  );
}
```

### Opción 3: UI Custom con React/Vue

Construir una UI custom usando frameworks modernos.

**Stack recomendado:**
- React/Next.js o Vue/Nuxt
- TailwindCSS para estilos
- EventSource API para SSE
- Markdown renderer (react-markdown)

**Ventajas:**
- ✅ Control total sobre diseño
- ✅ Integración perfecta con nuestro backend
- ✅ Sin dependencias de LangChain en frontend

**Desventajas:**
- ❌ Más tiempo de desarrollo
- ❌ Necesita implementar features desde cero

### Recomendación Final

**Usar Agent Chat UI** como punto de partida por las siguientes razones:

1. **Rápido Time-to-Market**: UI lista para usar
2. **Best Practices**: Implementa patrones probados de LangChain
3. **Mantenimiento**: Actualizado por el equipo de LangChain
4. **Personalizable**: Open source, podemos modificar según necesidades
5. **Features Avanzadas**: Time-travel debugging, state forking

**Plan de Implementación:**
1. Fase 1: Usar Agent Chat UI sin modificaciones
2. Fase 2: Personalizar estilos y branding
3. Fase 3: Agregar features custom si es necesario

## Frontend-Backend Integration

### Adapter Layer

Crear un adapter para que nuestro backend sea compatible con Agent Chat UI:

```python
# src/chat/presentation/adapters/agent_chat_ui_adapter.py

class AgentChatUIAdapter:
    """
    Adapter para hacer nuestro backend compatible con Agent Chat UI.
    
    Agent Chat UI espera un formato específico de mensajes y eventos.
    """
    
    def adapt_session_response(self, session: ChatSession) -> Dict:
        """Adapt session to Agent Chat UI format."""
        return {
            "thread_id": str(session.id),
            "title": session.title,
            "status": session.status.value,
            "created_at": session.created_at.isoformat(),
        }
    
    def adapt_message_response(self, message: ChatMessage) -> Dict:
        """Adapt message to Agent Chat UI format."""
        return {
            "id": str(message.id),
            "role": message.role.value,
            "content": message.content,
            "created_at": message.created_at.isoformat(),
            "metadata": {
                "chunks_used": len(message.retrieved_chunk_ids),
                "tokens": {
                    "prompt": message.prompt_tokens,
                    "completion": message.completion_tokens,
                }
            }
        }
    
    def adapt_streaming_event(self, event_type: str, data: Any) -> str:
        """Adapt streaming event to SSE format."""
        if event_type == "token":
            return f"data: {json.dumps({'type': 'token', 'content': data})}\n\n"
        elif event_type == "done":
            return f"data: {json.dumps({'type': 'done', 'metadata': data})}\n\n"
        elif event_type == "error":
            return f"data: {json.dumps({'type': 'error', 'message': data})}\n\n"
```

### CORS Configuration

```python
# src/main.py

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Agent Chat UI local
        "https://your-frontend-domain.com",  # Production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### WebSocket Support (Optional)

Para mejor performance, podemos agregar soporte WebSocket además de SSE:

```python
# src/chat/presentation/routers/chat_ws.py

from fastapi import WebSocket

@router.websocket("/ws/chat/{session_id}")
async def chat_websocket(
    websocket: WebSocket,
    session_id: str,
    mediator: IMediator = Depends(get_mediator),
):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            message = data["content"]
            
            # Send message command
            command = SendMessageCommand(
                session_id=session_id,
                content=message,
            )
            
            # Stream response
            async for token in mediator.send_stream(command):
                await websocket.send_json({
                    "type": "token",
                    "content": token,
                })
            
            # Send done event
            await websocket.send_json({"type": "done"})
            
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected", session_id=session_id)
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Production Setup                      │
│                                                          │
│  ┌──────────────┐         ┌──────────────┐            │
│  │   Nginx      │────────▶│  Next.js     │            │
│  │   (Reverse   │         │  (Agent Chat │            │
│  │    Proxy)    │         │     UI)      │            │
│  └──────────────┘         └──────────────┘            │
│         │                         │                     │
│         │                         │ HTTP/SSE            │
│         ▼                         ▼                     │
│  ┌──────────────────────────────────────┐             │
│  │         FastAPI Backend              │             │
│  │         (Chat API)                   │             │
│  └──────────────────────────────────────┘             │
│         │                    │                         │
│         ▼                    ▼                         │
│  ┌──────────────┐    ┌──────────────┐                │
│  │   Ollama     │    │  PostgreSQL  │                │
│  │   Server     │    │  + pgvector  │                │
│  └──────────────┘    └──────────────┘                │
└─────────────────────────────────────────────────────────┘
```

### Docker Compose Setup

```yaml
# docker-compose.yml

version: '3.8'

services:
  # Backend API
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/dbname
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - postgres
      - ollama
  
  # Frontend UI
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000/api/v1/chat
    depends_on:
      - backend
  
  # Ollama
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
  
  # PostgreSQL
  postgres:
    image: pgvector/pgvector:pg16
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=dbname
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  ollama_data:
  postgres_data:
```

## Updated Requirements

Basándome en la investigación, necesitamos actualizar los requirements para incluir:

### Requirement 13: Frontend UI Integration

**User Story:** Como usuario final, quiero una interfaz de chat moderna y responsiva para interactuar con el sistema RAG, de manera que pueda hacer preguntas de forma natural y ver las respuestas en tiempo real.

#### Acceptance Criteria

1. WHEN el usuario accede a la aplicación THEN el sistema SHALL mostrar la interfaz de Agent Chat UI
2. WHEN el usuario envía un mensaje THEN la interfaz SHALL mostrar el mensaje inmediatamente y comenzar a recibir la respuesta en streaming
3. WHEN se reciben tokens de respuesta THEN la interfaz SHALL renderizarlos en tiempo real con formato markdown
4. WHERE se citan fuentes THEN la interfaz SHALL resaltar las citaciones [Fuente N] de forma visual
5. WHEN se completa una respuesta THEN la interfaz SHALL mostrar indicadores de tokens usados y chunks recuperados
6. WHEN hay un error THEN la interfaz SHALL mostrar un mensaje de error claro y permitir reintentar

### Additional Dependencies

```txt
# Frontend (Agent Chat UI)
next>=14.0.0
react>=18.0.0
@langchain/langgraph-sdk>=0.0.1

# Backend additions for UI support
python-multipart>=0.0.6  # For file uploads (multimodal)
```
