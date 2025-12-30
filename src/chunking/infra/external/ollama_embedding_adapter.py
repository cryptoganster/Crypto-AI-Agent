"""Adaptador para servicio de embeddings usando Ollama local."""

import asyncio
from typing import List, Optional

import numpy as np
from loguru import logger

from src.chunking.domain.interfaces.services.embedding_service import IEmbeddingService
from src.chunking.domain.value_objects.vector_embedding import VectorEmbedding


class EmbeddingGenerationException(Exception):
    """Excepción cuando la generación de embeddings falla."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        """
        Inicializa la excepción.

        Args:
            message: Mensaje de error
            original_error: Excepción original que causó el error
        """
        super().__init__(message)
        self.original_error = original_error


class OllamaEmbeddingAdapter(IEmbeddingService):
    """
    Adaptador para generar embeddings usando Ollama local.

    Implementa IEmbeddingService usando Ollama que corre localmente
    sin necesidad de API key. Usa LangChain para la integración.

    Modelos soportados en Ollama:
    - nomic-embed-text (768 dim) - Recomendado para embeddings
    - llama3 (4096 dim) - Modelo general
    - mxbai-embed-large (1024 dim) - Embeddings grandes

    Features:
    - Ejecución 100% local (sin API)
    - Batch processing con tamaño configurable (default: 32)
    - Retry logic con exponential backoff
    - Normalización automática de vectores
    - Manejo robusto de errores
    - Logging detallado
    - Conexión a Ollama local (default: http://localhost:11434)

    Attributes:
        model_name: Nombre del modelo en Ollama
        base_url: URL del servidor Ollama
        dimension: Dimensión de los embeddings (768 para nomic-embed-text)
        batch_size: Tamaño de batch para procesamiento (32)
        max_retries: Número máximo de reintentos (3)
        initial_retry_delay: Delay inicial para retry en segundos (1.0)
        max_retry_delay: Delay máximo para retry en segundos (10.0)
        timeout: Timeout para operaciones en segundos (30.0)

    Examples:
        >>> adapter = OllamaEmbeddingAdapter()
        >>> embedding = await adapter.embed_text("Bitcoin price analysis")
        >>> embedding.dimension
        768
        >>> embedding.is_normalized()
        True
        >>>
        >>> # Batch processing
        >>> texts = ["Text 1", "Text 2", "Text 3"]
        >>> embeddings = await adapter.embed_batch(texts)
        >>> len(embeddings)
        3

    Requirements:
        - 2.1: Generar embeddings usando modelo local
        - 2.2: Producir vectores de dimensión 768
        - 2.3: Batch processing para eficiencia
        - 11.1: Batch size de 32
    """

    # Modelo recomendado: nomic-embed-text en Ollama
    DEFAULT_MODEL_NAME = "nomic-embed-text"
    DEFAULT_BASE_URL = "http://localhost:11434"
    DEFAULT_DIMENSION = 768
    DEFAULT_BATCH_SIZE = 32
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_INITIAL_RETRY_DELAY = 1.0
    DEFAULT_MAX_RETRY_DELAY = 10.0
    DEFAULT_TIMEOUT = 30.0

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        base_url: str = DEFAULT_BASE_URL,
        dimension: int = DEFAULT_DIMENSION,
        batch_size: int = DEFAULT_BATCH_SIZE,
        max_retries: int = DEFAULT_MAX_RETRIES,
        initial_retry_delay: float = DEFAULT_INITIAL_RETRY_DELAY,
        max_retry_delay: float = DEFAULT_MAX_RETRY_DELAY,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """
        Inicializa el adaptador.

        Args:
            model_name: Nombre del modelo en Ollama (default: nomic-embed-text)
            base_url: URL del servidor Ollama (default: http://localhost:11434)
            dimension: Dimensión de los embeddings (default: 768)
            batch_size: Tamaño de batch para procesamiento (default: 32)
            max_retries: Número máximo de reintentos (default: 3)
            initial_retry_delay: Delay inicial para retry en segundos (default: 1.0)
            max_retry_delay: Delay máximo para retry en segundos (default: 10.0)
            timeout: Timeout para operaciones en segundos (default: 30.0)

        Raises:
            ValueError: Si los parámetros son inválidos
        """
        if batch_size <= 0:
            raise ValueError(f"batch_size debe ser > 0, recibido: {batch_size}")

        if max_retries < 0:
            raise ValueError(f"max_retries debe ser >= 0, recibido: {max_retries}")

        if initial_retry_delay <= 0:
            raise ValueError(
                f"initial_retry_delay debe ser > 0, recibido: {initial_retry_delay}"
            )

        if max_retry_delay < initial_retry_delay:
            raise ValueError(
                f"max_retry_delay debe ser >= initial_retry_delay, "
                f"recibido: {max_retry_delay} < {initial_retry_delay}"
            )

        if timeout <= 0:
            raise ValueError(f"timeout debe ser > 0, recibido: {timeout}")

        if dimension <= 0:
            raise ValueError(f"dimension debe ser > 0, recibido: {dimension}")

        self.model_name = model_name
        self.base_url = base_url
        self.dimension = dimension
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.max_retry_delay = max_retry_delay
        self.timeout = timeout

        # Lazy initialization del modelo
        self._embeddings = None

        logger.info(
            "OllamaEmbeddingAdapter inicializado",
            model=self.model_name,
            base_url=self.base_url,
            dimension=self.dimension,
            batch_size=self.batch_size,
            max_retries=self.max_retries,
            local=True,
            api_required=False,
        )

    def _get_embeddings(self):
        """
        Obtiene el modelo de embeddings (lazy initialization).

        Returns:
            OllamaEmbeddings de LangChain

        Raises:
            ImportError: Si langchain-ollama no está instalado
            EmbeddingGenerationException: Si el modelo no se puede cargar
        """
        if self._embeddings is None:
            try:
                from langchain_ollama import OllamaEmbeddings

                logger.info(
                    "Conectando a Ollama para embeddings",
                    model=self.model_name,
                    base_url=self.base_url,
                    local=True,
                )

                # Crear embeddings usando LangChain + Ollama
                self._embeddings = OllamaEmbeddings(
                    model=self.model_name,
                    base_url=self.base_url,
                )

                logger.info(
                    "Conexión a Ollama establecida exitosamente",
                    model=self.model_name,
                    dimension=self.dimension,
                )

            except ImportError as e:
                error_msg = (
                    "langchain-ollama no está instalado. "
                    "Instalar con: pip install langchain-ollama"
                )
                logger.error(error_msg, error=str(e))
                raise ImportError(error_msg) from e

            except Exception as e:
                error_msg = (
                    f"Error conectando a Ollama en {self.base_url} "
                    f"con modelo {self.model_name}: {str(e)}"
                )
                logger.error(error_msg, error=str(e))
                raise EmbeddingGenerationException(error_msg, original_error=e)

        return self._embeddings

    async def embed_text(self, text: str) -> VectorEmbedding:
        """
        Genera embedding para un texto individual.

        Implementa retry logic con exponential backoff para manejar
        errores transitorios de Ollama.

        Args:
            text: Texto a embedear (debe ser no vacío)

        Returns:
            VectorEmbedding normalizado de dimensión configurada

        Raises:
            ValueError: Si el texto está vacío o es inválido
            EmbeddingGenerationException: Si la generación falla después de reintentos
            TimeoutError: Si la operación excede el timeout

        Examples:
            >>> adapter = OllamaEmbeddingAdapter()
            >>> embedding = await adapter.embed_text("Ethereum smart contracts")
            >>> embedding.dimension
            768
            >>> embedding.is_normalized()
            True
        """
        # Validar entrada
        if not text or not text.strip():
            raise ValueError("Texto no puede estar vacío")

        logger.debug(
            "Generando embedding para texto",
            text_length=len(text),
            text_preview=text[:100],
        )

        # Implementar retry logic con exponential backoff
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                # Generar embedding con timeout
                embedding = await asyncio.wait_for(
                    self._generate_embedding_internal(text), timeout=self.timeout
                )

                logger.debug(
                    "Embedding generado exitosamente",
                    text_length=len(text),
                    dimension=embedding.dimension,
                    attempt=attempt + 1,
                )

                return embedding

            except asyncio.TimeoutError as e:
                error_msg = (
                    f"Timeout generando embedding (intento {attempt + 1}/{self.max_retries + 1}): "
                    f"operación excedió {self.timeout}s"
                )
                logger.warning(error_msg)
                last_exception = TimeoutError(error_msg)

            except Exception as e:
                error_msg = (
                    f"Error generando embedding (intento {attempt + 1}/{self.max_retries + 1}): "
                    f"{str(e)}"
                )
                logger.warning(error_msg, error=str(e))
                last_exception = e

            # Si no es el último intento, esperar antes de reintentar
            if attempt < self.max_retries:
                # Exponential backoff: delay = initial * 2^attempt
                delay = min(
                    self.initial_retry_delay * (2**attempt), self.max_retry_delay
                )

                logger.info(
                    "Reintentando generación de embedding",
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    delay_seconds=delay,
                )

                await asyncio.sleep(delay)

        # Si llegamos aquí, todos los reintentos fallaron
        error_msg = (
            f"Error generando embedding después de {self.max_retries + 1} intentos"
        )
        logger.error(error_msg, last_error=str(last_exception))

        raise EmbeddingGenerationException(error_msg, original_error=last_exception)

    async def embed_batch(self, texts: List[str]) -> List[VectorEmbedding]:
        """
        Genera embeddings para un batch de textos.

        Procesa múltiples textos en paralelo para mayor eficiencia.
        Si el batch es muy grande, lo divide en sub-batches del tamaño
        configurado (default: 32).

        Args:
            texts: Lista de textos a embedear (no debe estar vacía)

        Returns:
            Lista de VectorEmbedding en el mismo orden que los textos

        Raises:
            ValueError: Si la lista está vacía o contiene textos inválidos
            EmbeddingGenerationException: Si la generación falla para algún texto
            TimeoutError: Si la operación excede el timeout

        Examples:
            >>> adapter = OllamaEmbeddingAdapter()
            >>> texts = [
            ...     "Bitcoin halving event",
            ...     "Ethereum merge update",
            ...     "DeFi protocol security"
            ... ]
            >>> embeddings = await adapter.embed_batch(texts)
            >>> len(embeddings) == len(texts)
            True
            >>> all(emb.is_normalized() for emb in embeddings)
            True

        Performance:
            - Batch processing es ~10x más rápido que llamadas individuales
            - Usa paralelización interna de Ollama
            - Divide batches grandes en sub-batches para evitar timeouts
        """
        # Validar entrada
        if not texts:
            raise ValueError("Lista de textos no puede estar vacía")

        # Validar que todos los textos sean válidos
        for i, text in enumerate(texts):
            if not text or not text.strip():
                raise ValueError(f"Texto en posición {i} está vacío")

        logger.info(
            "Generando embeddings para batch",
            batch_size=len(texts),
            configured_batch_size=self.batch_size,
        )

        # Si el batch es pequeño, procesarlo directamente
        if len(texts) <= self.batch_size:
            return await self._process_batch(texts)

        # Si el batch es grande, dividirlo en sub-batches
        logger.info(
            "Dividiendo batch grande en sub-batches",
            total_texts=len(texts),
            sub_batch_size=self.batch_size,
        )

        all_embeddings = []

        for i in range(0, len(texts), self.batch_size):
            sub_batch = texts[i : i + self.batch_size]

            logger.debug(
                "Procesando sub-batch",
                sub_batch_index=i // self.batch_size + 1,
                sub_batch_size=len(sub_batch),
                total_batches=(len(texts) + self.batch_size - 1) // self.batch_size,
            )

            sub_embeddings = await self._process_batch(sub_batch)
            all_embeddings.extend(sub_embeddings)

        logger.info(
            "Batch completo procesado exitosamente",
            total_embeddings=len(all_embeddings),
        )

        return all_embeddings

    async def _process_batch(self, texts: List[str]) -> List[VectorEmbedding]:
        """
        Procesa un batch de textos (tamaño <= batch_size).

        Args:
            texts: Lista de textos a procesar

        Returns:
            Lista de VectorEmbedding

        Raises:
            EmbeddingGenerationException: Si la generación falla
        """
        # Implementar retry logic para el batch completo
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                # Generar embeddings con timeout
                embeddings = await asyncio.wait_for(
                    self._generate_batch_embeddings_internal(texts),
                    timeout=self.timeout * len(texts),  # Timeout proporcional al tamaño
                )

                logger.debug(
                    "Batch procesado exitosamente",
                    batch_size=len(texts),
                    attempt=attempt + 1,
                )

                return embeddings

            except asyncio.TimeoutError as e:
                error_msg = (
                    f"Timeout procesando batch (intento {attempt + 1}/{self.max_retries + 1}): "
                    f"operación excedió {self.timeout * len(texts)}s"
                )
                logger.warning(error_msg)
                last_exception = TimeoutError(error_msg)

            except Exception as e:
                error_msg = (
                    f"Error procesando batch (intento {attempt + 1}/{self.max_retries + 1}): "
                    f"{str(e)}"
                )
                logger.warning(error_msg, error=str(e))
                last_exception = e

            # Si no es el último intento, esperar antes de reintentar
            if attempt < self.max_retries:
                delay = min(
                    self.initial_retry_delay * (2**attempt), self.max_retry_delay
                )

                logger.info(
                    "Reintentando procesamiento de batch",
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    delay_seconds=delay,
                )

                await asyncio.sleep(delay)

        # Si llegamos aquí, todos los reintentos fallaron
        error_msg = f"Error procesando batch después de {self.max_retries + 1} intentos"
        logger.error(error_msg, last_error=str(last_exception))

        raise EmbeddingGenerationException(error_msg, original_error=last_exception)

    async def _generate_embedding_internal(self, text: str) -> VectorEmbedding:
        """
        Genera embedding internamente (sin retry logic).

        Args:
            text: Texto a embedear

        Returns:
            VectorEmbedding normalizado

        Raises:
            Exception: Si la generación falla
        """
        # Ejecutar en thread pool para no bloquear el event loop
        loop = asyncio.get_event_loop()

        def _embed():
            embeddings_model = self._get_embeddings()
            # Generar embedding usando LangChain + Ollama
            embedding_list = embeddings_model.embed_query(text)
            return np.array(embedding_list, dtype=np.float32)

        embedding_array = await loop.run_in_executor(None, _embed)

        # Verificar dimensión
        if len(embedding_array) != self.dimension:
            logger.warning(
                "Dimensión de embedding no coincide con la esperada",
                expected=self.dimension,
                actual=len(embedding_array),
            )
            # Actualizar dimensión si es necesario
            self.dimension = len(embedding_array)

        # Normalizar el vector
        embedding_array = self._normalize_vector(embedding_array)

        # Crear VectorEmbedding
        return VectorEmbedding(
            vector=embedding_array, model=self.model_name, dimension=self.dimension
        )

    async def _generate_batch_embeddings_internal(
        self, texts: List[str]
    ) -> List[VectorEmbedding]:
        """
        Genera embeddings para un batch internamente (sin retry logic).

        Args:
            texts: Lista de textos a embedear

        Returns:
            Lista de VectorEmbedding

        Raises:
            Exception: Si la generación falla
        """
        # Ejecutar en thread pool para no bloquear el event loop
        loop = asyncio.get_event_loop()

        def _embed_batch():
            embeddings_model = self._get_embeddings()
            # Generar embeddings en batch usando LangChain + Ollama
            embeddings_list = embeddings_model.embed_documents(texts)
            return [np.array(emb, dtype=np.float32) for emb in embeddings_list]

        embeddings_arrays = await loop.run_in_executor(None, _embed_batch)

        # Crear VectorEmbedding para cada embedding
        embeddings = []

        for i, embedding_array in enumerate(embeddings_arrays):
            # Verificar dimensión
            if len(embedding_array) != self.dimension:
                logger.warning(
                    "Dimensión de embedding no coincide con la esperada",
                    expected=self.dimension,
                    actual=len(embedding_array),
                    index=i,
                )

            # Normalizar el vector
            normalized_array = self._normalize_vector(embedding_array)

            # Crear VectorEmbedding
            embedding = VectorEmbedding(
                vector=normalized_array,
                model=self.model_name,
                dimension=len(normalized_array),
            )

            embeddings.append(embedding)

        return embeddings

    def _normalize_vector(self, vector: np.ndarray) -> np.ndarray:
        """
        Normaliza un vector a magnitud unitaria.

        Args:
            vector: Vector a normalizar

        Returns:
            Vector normalizado (magnitud = 1.0)

        Raises:
            ValueError: Si el vector tiene magnitud cero
        """
        # Calcular magnitud
        magnitude = np.linalg.norm(vector)

        if magnitude == 0:
            raise ValueError("No se puede normalizar un vector de magnitud cero")

        # Normalizar
        normalized = vector / magnitude

        # Convertir a float32 para consistencia
        normalized = normalized.astype(np.float32)

        return normalized

    def __repr__(self) -> str:
        """Representación del adaptador."""
        return (
            f"OllamaEmbeddingAdapter("
            f"model={self.model_name}, "
            f"base_url={self.base_url}, "
            f"dimension={self.dimension}, "
            f"batch_size={self.batch_size}, "
            f"max_retries={self.max_retries}, "
            f"local=True)"
        )
