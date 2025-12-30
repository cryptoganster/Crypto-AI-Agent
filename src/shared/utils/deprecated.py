"""Utilidad para marcar código como deprecado durante la migración."""

import functools
import warnings
from typing import Any, Callable, Type, TypeVar, Union, cast

from loguru import logger

F = TypeVar("F", bound=Callable[..., Any])
T = TypeVar("T")


def deprecated(
    reason: str,
    new_location: str,
    removal_version: str = "next",
) -> Callable[[Union[Type[T], F]], Union[Type[T], F]]:
    """
    Marca una función, clase o módulo como deprecado.

    Args:
        reason: Razón de la deprecación
        new_location: Nueva ubicación del código
        removal_version: Versión en la que se eliminará

    Example:
        @deprecated(
            reason="Migrado a bounded context",
            new_location="src.article.domain.aggregates.article",
            removal_version="2.0"
        )
        class Article:
            pass
    """

    def decorator(obj: Union[Type[T], F]) -> Union[Type[T], F]:
        # Emitir warning al momento de la decoración
        warning_msg = (
            f"{obj.__name__} is deprecated: {reason}. "
            f"Use {new_location} instead. "
            f"Will be removed in version {removal_version}."
        )
        warnings.warn(warning_msg, DeprecationWarning, stacklevel=2)

        # Log deprecation
        logger.warning(
            "DEPRECATION WARNING",
            deprecated_item=obj.__name__,
            reason=reason,
            new_location=new_location,
            removal_version=removal_version,
        )

        # Marcar como deprecado
        setattr(obj, "__deprecated__", True)
        setattr(
            obj,
            "__deprecation_info__",
            {
                "reason": reason,
                "new_location": new_location,
                "removal_version": removal_version,
            },
        )

        # Para clases, retornar directamente
        if isinstance(obj, type):
            return cast(Type[T], obj)

        # Para funciones, crear wrapper
        @functools.wraps(obj)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return obj(*args, **kwargs)  # type: ignore

        # Copiar atributos de deprecación al wrapper
        setattr(wrapper, "__deprecated__", True)
        setattr(
            wrapper,
            "__deprecation_info__",
            {
                "reason": reason,
                "new_location": new_location,
                "removal_version": removal_version,
            },
        )

        return cast(F, wrapper)

    return decorator
