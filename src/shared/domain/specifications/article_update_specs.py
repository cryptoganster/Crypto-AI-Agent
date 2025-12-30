"""Specifications compuestas para validar actualizaciones batch de Article aggregate."""

from typing import Any, Dict, List

from src.shared.domain.specifications.base import Specification, ValidationResult
from src.shared.domain.specifications.non_empty_string_spec import (
    NonEmptyStringSpecification,
)
from src.shared.domain.specifications.score_range_spec import ScoreRangeSpecification


class ArticleMetadataUpdateSpecification(Specification[Dict[str, Any]]):
    """
    Specification compuesta para validar actualizaciones de metadata en batch.

    Valida todos los parámetros de metadata (language, category, confidence scores)
    en una sola operación, retornando todos los errores encontrados.

    Example:
        >>> spec = ArticleMetadataUpdateSpecification()
        >>> params = {
        ...     "language": "en",
        ...     "category": "Technology",
        ...     "language_confidence": 0.95,
        ...     "category_confidence": 0.90
        ... }
        >>> result = spec.is_satisfied_by(params)
        >>> assert result.is_valid
    """

    def __init__(self):
        """Inicializa specifications reutilizables."""
        self._language_spec = NonEmptyStringSpecification("language")
        self._category_spec = NonEmptyStringSpecification("category")
        self._score_spec = ScoreRangeSpecification("confidence")

    def is_satisfied_by(self, params: Dict[str, Any]) -> ValidationResult:
        """
        Valida todos los parámetros de metadata.

        Args:
            params: Diccionario con parámetros a validar:
                - language: Optional[str]
                - category: Optional[str]
                - language_confidence: float
                - category_confidence: float

        Returns:
            ValidationResult con resultado y todos los errores encontrados
        """
        errors: List[str] = []

        # Validar language si se proporciona
        language = params.get("language")
        if language is not None:
            # Validar que no esté vacío
            result = self._language_spec.is_satisfied_by(language)
            if not result.is_valid:
                errors.append(result.error_message or "Language no puede estar vacío")

            # Validar confidence
            language_confidence = params.get("language_confidence", 1.0)
            result = self._score_spec.is_satisfied_by(language_confidence)
            if not result.is_valid:
                errors.append(
                    f"Language confidence debe estar entre 0.0 y 1.0, recibido: {language_confidence}"
                )

        # Validar category si se proporciona
        category = params.get("category")
        if category is not None and str(category).strip():
            # Validar que no esté vacío
            result = self._category_spec.is_satisfied_by(category)
            if not result.is_valid:
                errors.append(result.error_message or "Category no puede estar vacío")

            # Validar confidence
            category_confidence = params.get("category_confidence", 1.0)
            result = self._score_spec.is_satisfied_by(category_confidence)
            if not result.is_valid:
                errors.append(
                    f"Category confidence debe estar entre 0.0 y 1.0, recibido: {category_confidence}"
                )

        return ValidationResult(
            is_valid=len(errors) == 0,
            error_message="; ".join(errors) if errors else None,
            error_code="METADATA_UPDATE_INVALID" if errors else None,
        )


class ArticleQualityUpdateSpecification(Specification[Dict[str, Any]]):
    """
    Specification compuesta para validar actualizaciones de quality en batch.

    Valida readability_score y content_hash en una sola operación.

    Example:
        >>> spec = ArticleQualityUpdateSpecification()
        >>> params = {
        ...     "readability_score": 0.85,
        ...     "content_hash": "abc123"
        ... }
        >>> result = spec.is_satisfied_by(params)
        >>> assert result.is_valid
    """

    def __init__(self):
        """Inicializa specifications reutilizables."""
        self._score_spec = ScoreRangeSpecification("readability_score")
        self._hash_spec = NonEmptyStringSpecification("content_hash")

    def is_satisfied_by(self, params: Dict[str, Any]) -> ValidationResult:
        """
        Valida todos los parámetros de quality.

        Args:
            params: Diccionario con parámetros a validar:
                - readability_score: Optional[float]
                - content_hash: Optional[str]

        Returns:
            ValidationResult con resultado y todos los errores encontrados
        """
        errors: List[str] = []

        # Validar readability_score si se proporciona
        readability_score = params.get("readability_score")
        if readability_score is not None:
            result = self._score_spec.is_satisfied_by(readability_score)
            if not result.is_valid:
                errors.append(
                    result.error_message
                    or f"Readability score debe estar entre 0.0 y 1.0, recibido: {readability_score}"
                )

        # Validar content_hash si se proporciona
        content_hash = params.get("content_hash")
        if content_hash is not None:
            # Validar que sea string
            if not isinstance(content_hash, str):
                errors.append(
                    f"Content hash debe ser string, recibido: {type(content_hash).__name__}"
                )
            else:
                # Validar que no esté vacío
                result = self._hash_spec.is_satisfied_by(content_hash)
                if not result.is_valid:
                    errors.append(
                        result.error_message or "Content hash no puede estar vacío"
                    )

        return ValidationResult(
            is_valid=len(errors) == 0,
            error_message="; ".join(errors) if errors else None,
            error_code="QUALITY_UPDATE_INVALID" if errors else None,
        )


class ArticleContentUpdateSpecification(Specification[Dict[str, Any]]):
    """
    Specification compuesta para validar actualizaciones de content en batch.

    Valida markdown, plaintext, scrapped y excerpt. Por ahora solo genera
    warnings, no errores, ya que las validaciones de content son más permisivas.

    Example:
        >>> spec = ArticleContentUpdateSpecification()
        >>> params = {
        ...     "markdown": "# Title\\n\\nContent",
        ...     "plaintext": "Title Content"
        ... }
        >>> result = spec.is_satisfied_by(params)
        >>> assert result.is_valid
    """

    # Límites de tamaño
    MAX_MARKDOWN_LENGTH = 100000  # 100KB
    MAX_PLAINTEXT_LENGTH = 100000  # 100KB
    MAX_SCRAPPED_LENGTH = 200000  # 200KB para HTML
    MAX_EXCERPT_LENGTH = 1000  # 1KB

    def is_satisfied_by(self, params: Dict[str, Any]) -> ValidationResult:
        """
        Valida todos los parámetros de content.

        Args:
            params: Diccionario con parámetros a validar:
                - markdown: Optional[str]
                - plaintext: Optional[str]
                - scrapped: Optional[str]
                - excerpt: Optional[str]

        Returns:
            ValidationResult con resultado (siempre válido por ahora)
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Validar markdown si se proporciona
        markdown = params.get("markdown")
        if markdown is not None and str(markdown).strip():
            if len(markdown) > self.MAX_MARKDOWN_LENGTH:
                warnings.append(
                    f"Markdown muy largo ({len(markdown)} chars), "
                    f"máximo recomendado: {self.MAX_MARKDOWN_LENGTH}"
                )

        # Validar plaintext si se proporciona
        plaintext = params.get("plaintext")
        if plaintext is not None and str(plaintext).strip():
            if len(plaintext) > self.MAX_PLAINTEXT_LENGTH:
                warnings.append(
                    f"Plaintext muy largo ({len(plaintext)} chars), "
                    f"máximo recomendado: {self.MAX_PLAINTEXT_LENGTH}"
                )

        # Validar scrapped si se proporciona
        scrapped = params.get("scrapped")
        if scrapped is not None and str(scrapped).strip():
            if len(scrapped) > self.MAX_SCRAPPED_LENGTH:
                warnings.append(
                    f"HTML scrapeado muy largo ({len(scrapped)} chars), "
                    f"máximo recomendado: {self.MAX_SCRAPPED_LENGTH}"
                )

        # Validar excerpt si se proporciona
        excerpt = params.get("excerpt")
        if excerpt is not None and str(excerpt).strip():
            if len(excerpt) > self.MAX_EXCERPT_LENGTH:
                warnings.append(
                    f"Excerpt muy largo ({len(excerpt)} chars), "
                    f"máximo recomendado: {self.MAX_EXCERPT_LENGTH}"
                )

        # Por ahora, content validation solo genera warnings, no errors
        # En el futuro se pueden agregar validaciones más estrictas

        return ValidationResult(
            is_valid=len(errors) == 0,
            error_message="; ".join(errors) if errors else None,
            error_code="CONTENT_UPDATE_INVALID" if errors else None,
        )
