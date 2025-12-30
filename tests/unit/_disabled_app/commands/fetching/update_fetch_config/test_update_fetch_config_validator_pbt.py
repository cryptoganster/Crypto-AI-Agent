"""Property-based tests para UpdateFetchConfigValidator.

Feature: remove-base-validator
Property 1: Invalid commands always raise exceptions
Property 2: Valid commands never raise exceptions
Validates: Requirements 3.1, 3.2
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.app.commands.fetching.update_fetch_config.command import (
    UpdateFetchConfigCommand,
)
from src.app.commands.fetching.update_fetch_config.exception import (
    InvalidFetchConfigError,
)
from src.app.commands.fetching.update_fetch_config.validator import (
    UpdateFetchConfigValidator,
)

# Estrategias para generar datos de prueba


@st.composite
def valid_source_id_strategy(draw):
    """Genera source_id válidos."""
    return draw(st.text(min_size=1, max_size=100).filter(lambda x: x.strip()))


@st.composite
def invalid_source_id_strategy(draw):
    """Genera source_id inválidos."""
    return draw(
        st.one_of(
            st.none(),
            st.just(""),
            st.text(max_size=10).filter(lambda x: not x.strip()),
        )
    )


@st.composite
def valid_fetch_config_strategy(draw):
    """Genera configuraciones de fetch válidas."""
    config = {}

    if draw(st.booleans()):
        config["interval_seconds"] = draw(st.integers(min_value=60, max_value=3600))

    if draw(st.booleans()):
        config["max_concurrency"] = draw(st.integers(min_value=1, max_value=50))

    if draw(st.booleans()):
        config["request_timeout"] = draw(st.integers(min_value=5, max_value=300))

    if draw(st.booleans()):
        config["user_agent"] = draw(
            st.text(min_size=1, max_size=255).filter(lambda x: x.strip())
        )

    if draw(st.booleans()):
        config["max_articles_per_fetch"] = draw(
            st.integers(min_value=1, max_value=1000)
        )

    if draw(st.booleans()):
        config["retry_attempts"] = draw(st.integers(min_value=0, max_value=10))

    if draw(st.booleans()):
        config["backoff_multiplier"] = draw(st.floats(min_value=0.1, max_value=10.0))

    if draw(st.booleans()):
        config["quality_threshold"] = draw(st.floats(min_value=0.0, max_value=1.0))

    # Asegurar que al menos un campo esté presente
    if not config:
        config["interval_seconds"] = draw(st.integers(min_value=60, max_value=3600))

    return config


@st.composite
def invalid_fetch_config_strategy(draw):
    """Genera configuraciones de fetch inválidas."""
    config_type = draw(st.integers(min_value=0, max_value=10))

    if config_type == 0:
        # Config no es diccionario
        return draw(st.one_of(st.text(), st.integers(), st.lists(st.integers())))

    if config_type == 1:
        # interval_seconds menor a 60
        return {"interval_seconds": draw(st.integers(min_value=1, max_value=59))}

    if config_type == 2:
        # interval_seconds negativo
        return {"interval_seconds": draw(st.integers(max_value=0))}

    if config_type == 3:
        # max_concurrency fuera de rango
        return {
            "max_concurrency": draw(
                st.one_of(
                    st.integers(max_value=0),
                    st.integers(min_value=51, max_value=100),
                )
            )
        }

    if config_type == 4:
        # request_timeout fuera de rango
        return {
            "request_timeout": draw(
                st.one_of(
                    st.integers(max_value=4),
                    st.integers(min_value=301, max_value=500),
                )
            )
        }

    if config_type == 5:
        # user_agent vacío
        return {
            "user_agent": draw(st.text(max_size=10).filter(lambda x: not x.strip()))
        }

    if config_type == 6:
        # user_agent demasiado largo
        return {"user_agent": draw(st.text(min_size=256, max_size=300))}

    if config_type == 7:
        # max_articles_per_fetch inválido
        return {
            "max_articles_per_fetch": draw(
                st.one_of(
                    st.integers(max_value=0),
                    st.integers(min_value=1001, max_value=2000),
                )
            )
        }

    if config_type == 8:
        # retry_attempts fuera de rango
        return {
            "retry_attempts": draw(
                st.one_of(
                    st.integers(max_value=-1),
                    st.integers(min_value=11, max_value=20),
                )
            )
        }

    if config_type == 9:
        # backoff_multiplier negativo
        return {"backoff_multiplier": draw(st.floats(max_value=0.0))}

    if config_type == 10:
        # quality_threshold fuera de rango
        return {
            "quality_threshold": draw(
                st.one_of(
                    st.floats(max_value=-0.1),
                    st.floats(min_value=1.1, max_value=2.0),
                )
            )
        }

    return {}


@st.composite
def valid_command_strategy(draw):
    """Genera comandos válidos."""
    source_id = draw(valid_source_id_strategy())
    fetch_config = draw(valid_fetch_config_strategy())

    correlation_id = (
        draw(st.text(min_size=1, max_size=50).filter(lambda x: x.strip()))
        if draw(st.booleans())
        else None
    )

    updated_by = (
        draw(st.text(min_size=1, max_size=50).filter(lambda x: x.strip()))
        if draw(st.booleans())
        else None
    )

    return UpdateFetchConfigCommand(
        source_id=source_id,
        fetch_config=fetch_config,
        correlation_id=correlation_id,
        updated_by=updated_by,
    )


@st.composite
def invalid_command_strategy(draw):
    """Genera comandos inválidos."""
    error_type = draw(st.integers(min_value=0, max_value=4))

    if error_type == 0:
        # source_id inválido
        return UpdateFetchConfigCommand(
            source_id=draw(invalid_source_id_strategy()),
            fetch_config=draw(valid_fetch_config_strategy()),
        )

    if error_type == 1:
        # fetch_config None
        return UpdateFetchConfigCommand(
            source_id=draw(valid_source_id_strategy()),
            fetch_config=None,
        )

    if error_type == 2:
        # fetch_config inválida
        return UpdateFetchConfigCommand(
            source_id=draw(valid_source_id_strategy()),
            fetch_config=draw(invalid_fetch_config_strategy()),
        )

    if error_type == 3:
        # correlation_id inválido
        return UpdateFetchConfigCommand(
            source_id=draw(valid_source_id_strategy()),
            fetch_config=draw(valid_fetch_config_strategy()),
            correlation_id=draw(st.text(max_size=10).filter(lambda x: not x.strip())),
        )

    if error_type == 4:
        # updated_by inválido
        return UpdateFetchConfigCommand(
            source_id=draw(valid_source_id_strategy()),
            fetch_config=draw(valid_fetch_config_strategy()),
            updated_by=draw(st.text(max_size=10).filter(lambda x: not x.strip())),
        )

    return UpdateFetchConfigCommand(
        source_id=draw(valid_source_id_strategy()),
        fetch_config=None,
    )


class TestUpdateFetchConfigValidatorProperties:
    """Property-based tests para UpdateFetchConfigValidator."""

    @given(command=valid_command_strategy())
    def test_property_valid_commands_never_raise_exceptions(
        self, command: UpdateFetchConfigCommand
    ):
        """
        Property 2: Valid commands never raise exceptions.

        Feature: remove-base-validator, Property 2: Valid commands never raise exceptions
        Validates: Requirements 3.2
        """
        # Arrange
        validator = UpdateFetchConfigValidator()

        # Act & Assert - No debería lanzar excepción
        validator.validate(command)

    @given(command=invalid_command_strategy())
    def test_property_invalid_commands_always_raise_exceptions(
        self, command: UpdateFetchConfigCommand
    ):
        """
        Property 1: Invalid commands always raise exceptions.

        Feature: remove-base-validator, Property 1: Invalid commands always raise exceptions
        Validates: Requirements 3.1
        """
        # Arrange
        validator = UpdateFetchConfigValidator()

        # Act & Assert - Debería lanzar InvalidFetchConfigError
        with pytest.raises(InvalidFetchConfigError):
            validator.validate(command)
