"""Specification Pattern para validaciones de dominio reutilizables."""

from .base import Specification, ValidationResult
from .composite_specs import AndSpecification, NotSpecification, OrSpecification
from .constants import SCORE_MAX, SCORE_MIN
from .non_empty_string_spec import NonEmptyStringSpecification
from .score_range_spec import ScoreRangeSpecification

__all__ = [
    "Specification",
    "ValidationResult",
    "ScoreRangeSpecification",
    "NonEmptyStringSpecification",
    "AndSpecification",
    "OrSpecification",
    "NotSpecification",
    "SCORE_MIN",
    "SCORE_MAX",
]
