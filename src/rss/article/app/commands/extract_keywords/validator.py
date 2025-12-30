"""Validator para ExtractArticleKeywords command."""

from dataclasses import dataclass
from typing import List

from .command import ExtractArticleKeywordsCommand


@dataclass
class ValidationResult:
    """Resultado de validación."""

    is_valid: bool
    errors: List[str]


class ExtractArticleKeywordsValidator:
    """Validador para ExtractArticleKeywordsCommand."""

    SUPPORTED_TRIGGERS = ["system", "user", "scheduler", "api"]
    SUPPORTED_LANGUAGES = ["auto", "es", "en", "fr", "de", "pt", "it"]
    MIN_MAX_KEYWORDS = 1
    MAX_MAX_KEYWORDS = 100
    MIN_SCORE = 0.0
    MAX_SCORE = 1.0

    def validate(self, command: ExtractArticleKeywordsCommand) -> ValidationResult:
        """
        Valida el comando de extracción de keywords.

        Reglas:
        - article_id no puede estar vacío
        - max_keywords debe estar entre 1 y 100
        - min_keyword_score debe estar entre 0.0 y 1.0
        - language debe ser soportado
        - triggered_by debe ser válido
        """
        errors = []

        # Validar article_id
        if not command.article_id or not command.article_id.strip():
            errors.append("article_id no puede estar vacío")

        # Validar max_keywords
        if command.max_keywords < self.MIN_MAX_KEYWORDS:
            errors.append(
                f"max_keywords debe ser al menos {self.MIN_MAX_KEYWORDS}. "
                f"Recibido: {command.max_keywords}"
            )

        if command.max_keywords > self.MAX_MAX_KEYWORDS:
            errors.append(
                f"max_keywords no puede exceder {self.MAX_MAX_KEYWORDS}. "
                f"Recibido: {command.max_keywords}"
            )

        # Validar min_keyword_score
        if command.min_keyword_score < self.MIN_SCORE:
            errors.append(
                f"min_keyword_score debe ser al menos {self.MIN_SCORE}. "
                f"Recibido: {command.min_keyword_score}"
            )

        if command.min_keyword_score > self.MAX_SCORE:
            errors.append(
                f"min_keyword_score no puede exceder {self.MAX_SCORE}. "
                f"Recibido: {command.min_keyword_score}"
            )

        # Validar language
        if command.language not in self.SUPPORTED_LANGUAGES:
            errors.append(
                f"language debe ser uno de: {', '.join(self.SUPPORTED_LANGUAGES)}. "
                f"Recibido: {command.language}"
            )

        # Validar triggered_by
        if command.triggered_by not in self.SUPPORTED_TRIGGERS:
            errors.append(
                f"triggered_by debe ser uno de: {', '.join(self.SUPPORTED_TRIGGERS)}. "
                f"Recibido: {command.triggered_by}"
            )

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
