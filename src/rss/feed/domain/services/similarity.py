"""Domain Service: SourceSimilarityService - Análisis de similaridad entre fuentes RSS."""

from typing import List, Optional

from src.rss.feed.domain.aggregates import Source
from src.rss.feed.domain.interfaces.services.similarity import ISourceSimilarityService
from src.rss.feed.domain.value_objects.rss_feed_url import RssFeedUrl, SourceUrl


class SourceSimilarityService(ISourceSimilarityService):
    """
    Domain Service especializado en análisis de similaridad de fuentes RSS.

    Responsabilidades:
    - Detectar sources duplicadas por URL
    - Calcular scores de similaridad entre sources
    - Comparación de URLs y metadatos
    - Análisis de dominios y subdominios relacionados
    """

    def find_exact_duplicate_source(
        self,
        target_url: SourceUrl,
        sources: List[Source],
    ) -> Optional[Source]:
        """
        Busca source con URL exactamente igual.

        Algoritmo optimizado O(n) lineal.

        Args:
            target_url: URL objetivo a buscar
            sources: Lista de sources donde buscar

        Returns:
            Source duplicada o None si no se encuentra
        """
        target_url_str = target_url.value.lower().strip()

        for source in sources:
            if source.url.value.lower().strip() == target_url_str:
                return source

        return None

    def find_similar_sources(
        self,
        target_url: SourceUrl,
        sources: List[Source],
        similarity_threshold: float = 0.8,
        max_results: int = 10,
        include_inactive: bool = False,
    ) -> List[Source]:
        """
        Encuentra sources similares usando algoritmo de similaridad URL.

        Características:
        - Threshold configurable
        - Filtrado por estado activo/inactivo
        - Ordenamiento por score descendente
        - Limitación de resultados

        Args:
            target_url: URL objetivo
            sources: Lista de sources
            similarity_threshold: Umbral de similaridad (0.0-1.0)
            max_results: Número máximo de resultados
            include_inactive: Incluir sources inactivas

        Returns:
            Lista de sources similares ordenadas por score
        """
        similar_sources = []

        for source in sources:
            # Filtrar sources inactivas si no se solicitan
            if not include_inactive and not source.is_active:
                continue

            # Calcular score de similaridad
            similarity_score = self.calculate_source_similarity_by_url(
                target_url, source.url
            )

            # Agregar si supera threshold
            if similarity_score >= similarity_threshold:
                similar_sources.append((source, similarity_score))

        # Ordenar por score descendente y limitar resultados
        similar_sources.sort(key=lambda x: x[1], reverse=True)
        return [source for source, _ in similar_sources[:max_results]]

    def calculate_source_similarity(
        self,
        source1: Source,
        source2: Source,
    ) -> float:
        """
        Calcula score de similaridad entre dos sources RSS.

        Algoritmo combinado:
        - Similaridad de URL (peso: 0.8)
        - Similaridad de metadatos (peso: 0.2)

        Args:
            source1: Primera source
            source2: Segunda source

        Returns:
            Score de similaridad (0.0-1.0)
        """
        # Similaridad por URL (peso principal)
        url_similarity = self.calculate_source_similarity_by_url(
            source1.url, source2.url
        )

        # Similaridad por metadatos (nombres, descripciones)
        metadata_similarity = self._calculate_source_metadata_similarity(
            source1, source2
        )

        return url_similarity * 0.8 + metadata_similarity * 0.2

    def calculate_source_similarity_by_url(
        self,
        url1: SourceUrl,
        url2: SourceUrl,
    ) -> float:
        """
        Calcula score de similaridad entre URLs RSS.

        Algoritmo detallado:
        - Dominio exacto: 1.0
        - Subdominios del mismo dominio base: 0.85
        - Mismo dominio + paths RSS comunes: 0.95
        - Mismo dominio + paths diferentes: 0.7
        - Dominios diferentes: 0.0

        Args:
            url1: Primera URL
            url2: Segunda URL

        Returns:
            Score de similaridad (0.0-1.0)
        """
        # URLs exactamente iguales
        if url1.value.lower() == url2.value.lower():
            return 1.0

        # Extraer dominios y paths usando SourceUrl VO methods
        try:
            domain1 = url1.get_domain().lower()
            domain2 = url2.get_domain().lower()
            path1 = url1.get_path().lower()
            path2 = url2.get_path().lower()
        except Exception:
            # Fallback si SourceUrl no tiene métodos
            return 0.0

        # Dominios exactamente iguales
        if domain1 == domain2:
            # Mismo dominio + paths RSS comunes
            if self._are_paths_similar(path1, path2):
                return 0.95
            # Mismo dominio + paths exactos
            if path1 == path2:
                return 0.9
            # Mismo dominio + paths diferentes
            return 0.7

        # Subdominios del mismo dominio base
        if self._are_subdomains_related(domain1, domain2):
            if self._are_paths_similar(path1, path2):
                return 0.85
            return 0.6

        # Dominios completamente diferentes
        return 0.0

    def are_sources_similar(
        self,
        source1: Source,
        source2: Source,
        threshold: float = 0.8,
    ) -> bool:
        """
        Determina si dos sources son similares según threshold.

        Wrapper conveniente para comparación booleana.

        Args:
            source1: Primera source
            source2: Segunda source
            threshold: Umbral de similaridad

        Returns:
            True si son similares, False en caso contrario
        """
        similarity_score = self.calculate_source_similarity(source1, source2)
        return similarity_score >= threshold

    # ===============================
    # PRIVATE HELPER METHODS
    # ===============================

    def _calculate_source_metadata_similarity(
        self, source1: Source, source2: Source
    ) -> float:
        """
        Calcula similaridad entre metadatos de sources.

        Compara nombres y descripciones usando algoritmo de similaridad de texto.
        """
        name_similarity = 0.0
        desc_similarity = 0.0

        # Similaridad de nombres
        if source1.name and source2.name:
            name_similarity = self._calculate_text_similarity(
                source1.name.value, source2.name.value
            )

        # Similaridad de descripciones
        if (
            hasattr(source1, "description")
            and hasattr(source2, "description")
            and source1.description
            and source2.description
        ):
            desc_similarity = self._calculate_text_similarity(
                source1.description.value, source2.description.value
            )

        # Promedio ponderado (nombre más importante)
        return name_similarity * 0.7 + desc_similarity * 0.3

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calcula similaridad entre textos usando algoritmo Jaccard.

        Returns:
            Score de similaridad (0.0-1.0)
        """
        if not text1 or not text2:
            return 0.0

        # Normalizar textos
        t1 = text1.strip().lower()
        t2 = text2.strip().lower()

        # Textos exactos
        if t1 == t2:
            return 1.0

        # Similaridad por palabras comunes (Jaccard similarity)
        words1 = set(t1.split())
        words2 = set(t2.split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0

    def _are_paths_similar(self, path1: str, path2: str) -> bool:
        """
        Determina si dos paths RSS son similares.

        Algoritmo expandido con más paths RSS comunes.
        """
        # Paths exactos
        if path1 == path2:
            return True

        # Normalizar paths (remover trailing slashes)
        path1 = path1.rstrip("/")
        path2 = path2.rstrip("/")

        # Paths RSS comunes expandidos
        common_rss_paths = {
            "",  # root
            "/rss",
            "/feed",
            "/feeds",
            "/rss.xml",
            "/feed.xml",
            "/atom.xml",
            "/index.xml",
            "/rss2.xml",
            "/atom",
            "/blog/feed",
            "/blog/rss",
            "/news/feed",
            "/news/rss",
            "/api/rss",
            "/content/feed",
        }

        if path1 in common_rss_paths and path2 in common_rss_paths:
            return True

        return False

    def _are_subdomains_related(self, domain1: str, domain2: str) -> bool:
        """
        Determina si dos dominios son subdominios relacionados.

        Ejemplos:
        - blog.example.com vs www.example.com → True
        - feeds.google.com vs news.google.com → True
        - example.com vs different.com → False
        """

        def get_base_domain(domain: str) -> str:
            parts = domain.split(".")
            if len(parts) >= 2:
                return ".".join(parts[-2:])
            return domain

        base1 = get_base_domain(domain1)
        base2 = get_base_domain(domain2)

        return base1 == base2 and len(base1.split(".")) >= 2
