"""Mediator implementation for CQRS pattern."""

from src.shared.infra.mediator.mediator import HandlerNotFoundError, Mediator

__all__ = ["Mediator", "HandlerNotFoundError"]
