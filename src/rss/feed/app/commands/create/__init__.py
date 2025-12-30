"""Create Source Command Package - CQRS Implementation for RSS Feeds."""

from .command import CreateSourceCommand
from .dto import (
    ContentSourceConfigDto,
    ContentSourceDuplicateCheckDto,
    ContentSourcePreviewDto,
    ContentSourceValidationDto,
    CreateSourceRequestDto,
    CreateSourceResponseDto,
)
from .exception import (
    CreateSourceException,
    CreateSourceValidationException,
    DuplicateContentSourceException,
    DuplicateSourceException,
    SourceRepositoryException,
)
from .handler import CreateSourceCommandHandler
from .result import (
    CreateSourceDuplicateFailure,
    CreateSourceFailure,
    CreateSourceNetworkFailure,
    CreateSourceResult,
    CreateSourceResultBuilder,
    CreateSourceResultStatus,
    CreateSourceSuccess,
    CreateSourceValidationFailure,
)

__all__ = [
    # Core Command and Handler
    "CreateSourceCommand",
    "CreateSourceCommandHandler",
    # Exceptions
    "CreateSourceException",
    "DuplicateSourceException",
    "CreateSourceValidationException",
    "SourceRepositoryException",
    "DuplicateContentSourceException",
    # DTOs
    "CreateSourceRequestDto",
    "CreateSourceResponseDto",
    "ContentSourceValidationDto",
    "ContentSourceConfigDto",
    "ContentSourcePreviewDto",
    "ContentSourceDuplicateCheckDto",
    # Result Types
    "CreateSourceResult",
    "CreateSourceSuccess",
    "CreateSourceFailure",
    "CreateSourceValidationFailure",
    "CreateSourceDuplicateFailure",
    "CreateSourceNetworkFailure",
    "CreateSourceResultStatus",
    "CreateSourceResultBuilder",
]
