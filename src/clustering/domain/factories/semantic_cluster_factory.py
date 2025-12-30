"""Factory para crear SemanticCluster aggregates."""

from typing import List, Optional, Tuple

from src.clustering.domain.aggregates.semantic_cluster import SemanticCluster
from src.clustering.domain.value_objects import ClusterId, VectorEmbedding


class SemanticClusterFactory:
    """
    Factory para crear SemanticCluster aggregates con validaciones.

    Responsabilidades:
    - Validar datos de entrada antes de crear el aggregate
    - Crear SemanticCluster usando factory method
    - Aplicar defaults apropiados

    Flujo:
    1. Validar label (no vacío, longitud razonable)
    2. Validar centroid (dimensión 768, normalizado)
    3. Validar top_terms (frecuencias > 0)
    4. Crear SemanticCluster usando factory method

    Examples:
        >>> factory = SemanticClusterFactory()
        >>> cluster = factory.create_cluster(
        ...     label="Bitcoin Regulation",
        ...     centroid=embedding,
        ... )
        >>> cluster.size
        0
        >>> cluster.label
        'Bitcoin Regulation'
    """

    def create_cluster(
        self,
        label: str,
        centroid: VectorEmbedding,
        cluster_id: Optional[ClusterId] = None,
        top_terms: Optional[List[Tuple[str, float]]] = None,
    ) -> SemanticCluster:
        """
        Crea SemanticCluster con validaciones.

        Args:
            label: Label descriptivo del cluster
            centroid: Centroid del cluster (embedding promedio)
            cluster_id: ID opcional (se genera si no se provee)
            top_terms: Términos frecuentes opcionales

        Returns:
            SemanticCluster validado y listo para persistir

        Raises:
            ValueError: Si los datos son inválidos

        Examples:
            >>> factory = SemanticClusterFactory()
            >>> cluster = factory.create_cluster(
            ...     label="Bitcoin ETF",
            ...     centroid=embedding,
            ...     top_terms=[("bitcoin", 0.8), ("etf", 0.6)],
            ... )
            >>> cluster.label
            'Bitcoin ETF'
            >>> len(cluster.top_terms)
            2
        """
        # 1. Validar datos de entrada
        validation_errors = self._validate_input(label, centroid, top_terms)
        if validation_errors:
            raise ValueError(f"Validación fallida: {', '.join(validation_errors)}")

        # 2. Limpiar label
        clean_label = self._clean_label(label)

        # 3. Validar y limpiar top_terms
        clean_top_terms = self._clean_top_terms(top_terms) if top_terms else None

        # 4. Crear SemanticCluster usando factory method
        cluster = SemanticCluster.create(
            label=clean_label,
            centroid=centroid,
            cluster_id=cluster_id,
            top_terms=clean_top_terms,
        )

        return cluster

    def _validate_input(
        self,
        label: str,
        centroid: VectorEmbedding,
        top_terms: Optional[List[Tuple[str, float]]],
    ) -> List[str]:
        """
        Valida datos de entrada y retorna lista de errores.

        Args:
            label: Label a validar
            centroid: Centroid a validar
            top_terms: Términos a validar

        Returns:
            Lista de mensajes de error (vacía si es válido)
        """
        errors = []

        # Validar label
        if not label or not label.strip():
            errors.append("Label es requerido")
        elif len(label.strip()) > 200:
            errors.append("Label debe tener máximo 200 caracteres")

        # Validar centroid
        if centroid.dimension != 768:
            errors.append(
                f"Centroid debe tener dimensión 768, recibido: {centroid.dimension}"
            )

        # Validar top_terms
        if top_terms is not None:
            if not isinstance(top_terms, list):
                errors.append("top_terms debe ser una lista")
            else:
                for i, item in enumerate(top_terms):
                    if not isinstance(item, tuple) or len(item) != 2:
                        errors.append(
                            f"top_terms[{i}] debe ser tupla (término, frecuencia)"
                        )
                        continue

                    term, freq = item

                    if not isinstance(term, str) or not term.strip():
                        errors.append(
                            f"top_terms[{i}]: término debe ser string no vacío"
                        )

                    if not isinstance(freq, (int, float)) or freq <= 0:
                        errors.append(f"top_terms[{i}]: frecuencia debe ser > 0")

        return errors

    def _clean_label(self, label: str) -> str:
        """
        Limpia label removiendo espacios extra.

        Args:
            label: Label a limpiar

        Returns:
            Label limpio
        """
        # Remover espacios múltiples
        import re

        clean = re.sub(r"\s+", " ", label)

        # Trim
        clean = clean.strip()

        # Capitalizar primera letra de cada palabra
        clean = clean.title()

        return clean

    def _clean_top_terms(
        self,
        top_terms: List[Tuple[str, float]],
    ) -> List[Tuple[str, float]]:
        """
        Limpia y normaliza top_terms.

        Args:
            top_terms: Lista de (término, frecuencia)

        Returns:
            Lista limpia de (término, frecuencia)
        """
        clean_terms = []

        for term, freq in top_terms:
            # Limpiar término
            clean_term = term.strip().lower()

            # Normalizar frecuencia
            clean_freq = float(freq)

            # Agregar si es válido
            if clean_term and clean_freq > 0:
                clean_terms.append((clean_term, clean_freq))

        # Ordenar por frecuencia descendente
        clean_terms.sort(key=lambda x: x[1], reverse=True)

        return clean_terms
