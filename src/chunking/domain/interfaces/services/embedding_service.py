"""Interface para servicio de generación de embeddings vectoriales."""

from typing import List, Protocol

from src.chunking.domain.value_objects.vector_embedding import VectorEmbedding


class IEmbeddingService(Protocol):
    """
    Interface para servicio de embeddings.

    Define el contrato para servicios que generan embeddings vectoriales
    a partir de texto. Los embeddings capturan el significado semántico
    del texto en un espacio vectorial de alta dimensión.

    Implementaciones:
    - NomicEmbeddingAdapter: Usa nomic-embed-text (768 dims)
    - SentenceTransformersAdapter: Usa sentence-transformers
    - OpenAIEmbeddingAdapter: Usa text-embedding-ada-002 (1536 dims)

    Responsabilidades:
    - Generar embeddings normalizados para texto
    - Procesar batches de textos eficientemente
    - Manejar errores de generación
    - Retornar vectores normalizados (magnitud = 1.0)

    Invariantes:
    - Todos los embeddings retornados deben estar normalizados
    - La dimensión debe ser consistente para un modelo dado
    - Los vectores no deben contener NaN o Inf

    Examples:
        >>> service: IEmbeddingService = NomicEmbeddingAdapter()
        >>> embedding = await service.embed_text("Bitcoin price analysis")
        >>> embedding.dimension
        768
        >>> embedding.is_normalized()
        True
        >>>
        >>> # Batch processing
        >>> texts = ["Text 1", "Text 2", "Text 3"]
        >>> embeddings = await service.embed_batch(texts)
        >>> len(embeddings)
        3
    """

    async def embed_text(self, text: str) -> VectorEmbedding:
        """
        Genera embedding para un texto individual.

        Convierte el texto en un vector denso que captura su significado
        semántico. El vector resultante está normalizado (magnitud = 1.0)
        para permitir comparaciones usando similitud coseno.

        Args:
            text: Texto a embedear (debe ser no vacío)

        Returns:
            VectorEmbedding normalizado

        Raises:
            ValueError: Si el texto está vacío o es inválido
            EmbeddingGenerationException: Si la generación falla
            TimeoutError: Si la operación excede el timeout

        Examples:
            >>> embedding = await service.embed_text("Ethereum smart contracts")
            >>> embedding.dimension
            768
            >>> embedding.model
            'nomic-embed-text'
            >>> embedding.magnitude()
            1.0

        Notes:
            - El texto puede ser preprocesado (lowercase, truncado, etc.)
            - Textos muy largos pueden ser truncados según límites del modelo
            - El modelo usado determina la dimensión del vector resultante
        """
        ...

    async def embed_batch(self, texts: List[str]) -> List[VectorEmbedding]:
        """
        Genera embeddings para un batch de textos.

        Procesa múltiples textos en paralelo para mayor eficiencia.
        El orden de los embeddings en la lista resultante corresponde
        al orden de los textos de entrada.

        Args:
            texts: Lista de textos a embedear (no debe estar vacía)

        Returns:
            Lista de VectorEmbedding en el mismo orden que los textos

        Raises:
            ValueError: Si la lista está vacía o contiene textos inválidos
            EmbeddingGenerationException: Si la generación falla para algún texto
            TimeoutError: Si la operación excede el timeout

        Examples:
            >>> texts = [
            ...     "Bitcoin halving event",
            ...     "Ethereum merge update",
            ...     "DeFi protocol security"
            ... ]
            >>> embeddings = await service.embed_batch(texts)
            >>> len(embeddings) == len(texts)
            True
            >>> all(emb.is_normalized() for emb in embeddings)
            True

        Notes:
            - Batch size óptimo: 32 textos (según Requirements 11.1)
            - Si el batch es muy grande, puede dividirse internamente
            - Todos los embeddings usan el mismo modelo
            - Si un texto falla, puede retornar vector cero o lanzar excepción

        Performance:
            - Batch processing es ~10x más rápido que llamadas individuales
            - Usa paralelización interna del modelo
            - Recomendado para procesar múltiples chunks de un artículo
        """
        ...
