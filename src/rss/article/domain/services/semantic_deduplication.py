"""Semantic Deduplication Service para Article BC.

Detecta artículos duplicados usando embeddings vectoriales.
"""

from dataclasses import dataclass
from typing import List, Optional

from src.shared.kernel.logger import ILogger


@dataclass(frozen=True)
class DuplicateMatch:
    """Representa un artículo duplicado detectado."""

    article_id: str
    similarity_score: float
    title: str
    url: str


@dataclass(frozen=True)
class ChunkWithSimilarity:
    """Chunk con score de similitud."""

    chunk_id: str
    article_id: str
    similarity_score: float
    content: str


class SemanticDeduplicationService:
    """
    Servicio de dominio para detectar duplicados usando embeddings.

    Responsabilidades:
    - Buscar artículos similares por embedding
    - Aplicar threshold de similitud
    - Retornar matches ordenados por score

    NOTA: Este servicio vive en Article BC porque la deduplicación
    es una capacidad del dominio Article, aunque usa embeddings
    generados por Embedding BC.
    """

    def __init__(
        self,
        chunk_read_repository,  # IContentChunkReadRepository
        similarity_threshold: float,
        logger: ILogger,
    ):
        """
        Inicializa servicio.

        Args:
            chunk_read_repository: Repository para leer chunks con embeddings
            similarity_threshold: Threshold de similitud (0.0-1.0)
            logger: Logger para tracking
        """
        self._chunk_repo = chunk_read_repository
        self._threshold = similarity_threshold
        self._logger = logger.bind(
            layer="domain",
            service="SemanticDeduplicationService",
        )

    async def find_duplicates(
        self,
        article_id: str,
        max_results: int = 10,
    ) -> List[DuplicateMatch]:
        """
        Busca artículos duplicados basándose en similitud de embeddings de chunks.

        Estrategia: Usa el primer chunk del artículo como representación
        para búsqueda de similitud.

        Args:
            article_id: ID del artículo a verificar
            max_results: Máximo número de duplicados a retornar

        Returns:
            Lista de DuplicateMatch ordenados por similitud (mayor a menor)

        Raises:
            ValueError: Si article_id no tiene chunks con embeddings
        """
        self._logger.info(
            "Buscando duplicados semánticos",
            article_id=article_id,
            threshold=self._threshold,
        )

        # 1. Obtener chunks del artículo
        chunks = await self._chunk_repo.find_by_article_id(article_id)

        if not chunks:
            self._logger.warning(
                "Artículo no tiene chunks generados",
                article_id=article_id,
            )
            raise ValueError(f"Article {article_id} no tiene chunks")

        # 2. Usar el primer chunk como representación del artículo
        first_chunk = chunks[0]

        if first_chunk.embedding is None:
            self._logger.warning(
                "Chunk no tiene embedding generado",
                article_id=article_id,
                chunk_id=first_chunk.id,
            )
            raise ValueError(f"Article {article_id} no tiene embeddings")

        # 3. Buscar chunks similares (que pertenecen a otros artículos)
        similar_results = await self._chunk_repo.find_similar_by_embedding(
            embedding_vector=first_chunk.embedding.vector,
            threshold=self._threshold,
            limit=max_results * 3,  # Buscar más porque filtraremos por article_id
        )

        # 4. Agrupar por article_id y calcular score promedio
        article_scores = {}
        for chunk, similarity_score in similar_results:
            if chunk.article_id == article_id:
                continue  # Excluir el mismo artículo

            if chunk.article_id not in article_scores:
                article_scores[chunk.article_id] = {
                    "scores": [],
                    "chunk": chunk,
                }

            article_scores[chunk.article_id]["scores"].append(similarity_score)

        # 5. Calcular score promedio y crear DuplicateMatch
        duplicates = []
        for article_id_dup, data in article_scores.items():
            avg_score = sum(data["scores"]) / len(data["scores"])
            chunk = data["chunk"]

            # Extraer metadata del source_url (formato: article_title|article_url)
            # Por ahora usamos valores por defecto
            duplicates.append(
                DuplicateMatch(
                    article_id=article_id_dup,
                    similarity_score=avg_score,
                    title="Sin título",  # TODO: Agregar metadata al chunk
                    url=chunk.source_url,
                )
            )

        # 6. Ordenar por score y limitar resultados
        duplicates.sort(key=lambda x: x.similarity_score, reverse=True)
        duplicates = duplicates[:max_results]

        self._logger.info(
            "Duplicados encontrados",
            article_id=article_id,
            count=len(duplicates),
            top_score=duplicates[0].similarity_score if duplicates else 0.0,
        )

        return duplicates

    async def is_duplicate(
        self,
        article_id: str,
        strict_threshold: Optional[float] = None,
    ) -> bool:
        """
        Verifica si un artículo es duplicado de otro existente.

        Args:
            article_id: ID del artículo a verificar
            strict_threshold: Threshold más estricto (opcional)

        Returns:
            True si se encontró al menos un duplicado
        """
        threshold = strict_threshold or self._threshold

        try:
            duplicates = await self.find_duplicates(article_id, max_results=1)

            if not duplicates:
                return False

            # Verificar si el mejor match supera el threshold
            return duplicates[0].similarity_score >= threshold

        except ValueError:
            # No tiene embedding, no puede ser duplicado
            return False
