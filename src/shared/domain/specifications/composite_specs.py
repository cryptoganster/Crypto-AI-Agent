"""Composite Specifications para combinar validaciones."""

from typing import TypeVar

from .base import Specification, ValidationResult

T = TypeVar("T")


class AndSpecification(Specification[T]):
    """
    Combina dos specifications con lógica AND.

    Ambas specifications deben satisfacerse para que el resultado sea válido.

    Example:
        >>> score_spec = ScoreRangeSpecification("score")
        >>> string_spec = NonEmptyStringSpecification("name")
        >>> combined = AndSpecification(score_spec, string_spec)
    """

    def __init__(self, left: Specification[T], right: Specification[T]):
        """
        Inicializa specification compuesta.

        Args:
            left: Primera specification
            right: Segunda specification
        """
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: T) -> ValidationResult:
        """
        Verifica que ambas specifications se satisfagan.

        Args:
            candidate: Valor a validar

        Returns:
            ValidationResult - falla si alguna falla
        """
        left_result = self.left.is_satisfied_by(candidate)
        if not left_result.is_valid:
            return left_result

        return self.right.is_satisfied_by(candidate)


class OrSpecification(Specification[T]):
    """
    Combina dos specifications con lógica OR.

    Al menos una specification debe satisfacerse para que el resultado sea válido.

    Example:
        >>> spec1 = ScoreRangeSpecification("score1")
        >>> spec2 = ScoreRangeSpecification("score2")
        >>> combined = OrSpecification(spec1, spec2)
    """

    def __init__(self, left: Specification[T], right: Specification[T]):
        """
        Inicializa specification compuesta.

        Args:
            left: Primera specification
            right: Segunda specification
        """
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: T) -> ValidationResult:
        """
        Verifica que al menos una specification se satisfaga.

        Args:
            candidate: Valor a validar

        Returns:
            ValidationResult - éxito si alguna tiene éxito
        """
        left_result = self.left.is_satisfied_by(candidate)
        if left_result.is_valid:
            return left_result

        right_result = self.right.is_satisfied_by(candidate)
        if right_result.is_valid:
            return right_result

        # Ambas fallaron, retornar el error de la derecha
        return right_result


class NotSpecification(Specification[T]):
    """
    Niega una specification.

    La specification original NO debe satisfacerse para que el resultado sea válido.

    Example:
        >>> spec = ScoreRangeSpecification("score")
        >>> negated = NotSpecification(spec)
        >>> result = negated.is_satisfied_by(1.5)  # Fuera de rango
        >>> assert result.is_valid  # Válido porque NO satisface el rango
    """

    def __init__(self, spec: Specification[T]):
        """
        Inicializa specification negada.

        Args:
            spec: Specification a negar
        """
        self.spec = spec

    def is_satisfied_by(self, candidate: T) -> ValidationResult:
        """
        Verifica que la specification NO se satisfaga.

        Args:
            candidate: Valor a validar

        Returns:
            ValidationResult - inverso de la specification original
        """
        result = self.spec.is_satisfied_by(candidate)

        if result.is_valid:
            return ValidationResult.failure(
                "Specification should not be satisfied", "NOT_SATISFIED"
            )

        return ValidationResult.success()
