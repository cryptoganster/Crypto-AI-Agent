"""Property-based tests para UpdateSourceValidator.

Feature: remove-base-validator
Property 1: Invalid commands always raise exceptions
Property 2: Valid commands never raise exceptions
Validates: Requirements 2.1, 2.2
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.rss.feed.app.commands.update_source.command import UpdateRssFeedCommand
from src.rss.feed.app.commands.update_source.exception import InvalidSourceUpdateError
from src.rss.feed.app.commands.update_source.validator import UpdateSourceValidator

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
def valid_name_strategy(draw):
    """Genera nombres válidos."""
    return draw(st.text(min_size=1, max_size=255).filter(lambda x: x.strip()))


@st.composite
def invalid_name_strategy(draw):
    """Genera nombres inválidos."""
    return draw(
        st.one_of(
            st.text(max_size=10).filter(lambda x: not x.strip()),
            st.text(min_size=256, max_size=300),
        )
    )


@st.composite
def valid_description_strategy(draw):
    """Genera descripciones válidas (no vacías para contar como actualización)."""
    return draw(st.text(min_size=1, max_size=1000))


@st.composite
def invalid_description_strategy(draw):
    """Genera descripciones inválidas."""
    return draw(st.text(min_size=1001, max_size=1100))


@st.composite
def valid_config_strategy(draw):
    """Genera configuraciones válidas."""
    config = {}

    if draw(st.booleans()):
        config["fetch_enabled"] = draw(st.booleans())

    if draw(st.booleans()):
        config["priority"] = draw(st.integers(min_value=1, max_value=10))

    if draw(st.booleans()):
        config["quality_threshold"] = draw(st.floats(min_value=0.0, max_value=1.0))

    if draw(st.booleans()):
        config["max_fetch_retries"] = draw(st.integers(min_value=0, max_value=10))

    if draw(st.booleans()):
        config["fetch_timeout_seconds"] = draw(st.integers(min_value=1, max_value=300))

    if draw(st.booleans()):
        config["user_agent"] = draw(
            st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
        )

    return config if config else None


@st.composite
def invalid_config_strategy(draw):
    """Genera configuraciones inválidas."""
    config_type = draw(st.integers(min_value=0, max_value=6))

    if config_type == 0:
        # Config no es diccionario
        return draw(st.one_of(st.text(), st.integers(), st.lists(st.integers())))

    if config_type == 1:
        # fetch_enabled no es boolean
        return {"fetch_enabled": draw(st.one_of(st.text(), st.integers()))}

    if config_type == 2:
        # priority fuera de rango
        return {
            "priority": draw(
                st.one_of(
                    st.integers(max_value=0),
                    st.integers(min_value=11),
                )
            )
        }

    if config_type == 3:
        # quality_threshold fuera de rango
        return {
            "quality_threshold": draw(
                st.one_of(
                    st.floats(max_value=-0.1),
                    st.floats(min_value=1.1, max_value=2.0),
                )
            )
        }

    if config_type == 4:
        # max_fetch_retries negativo
        return {"max_fetch_retries": draw(st.integers(max_value=-1))}

    if config_type == 5:
        # fetch_timeout_seconds no positivo
        return {"fetch_timeout_seconds": draw(st.integers(max_value=0))}

    if config_type == 6:
        # user_agent vacío
        return {
            "user_agent": draw(st.text(max_size=10).filter(lambda x: not x.strip()))
        }

    return {}


@st.composite
def valid_command_strategy(draw):
    """Genera comandos válidos."""
    source_id = draw(valid_source_id_strategy())

    # Elegir qué campos incluir (al menos uno debe estar presente)
    update_type = draw(st.integers(min_value=0, max_value=6))

    if update_type == 0:
        # Solo name
        name = draw(valid_name_strategy())
        description = None
        config = None
    elif update_type == 1:
        # Solo description
        name = None
        description = draw(valid_description_strategy())
        config = None
    elif update_type == 2:
        # Solo config
        name = None
        description = None
        config = draw(valid_config_strategy())
        # Asegurar que config no sea None o vacío
        if not config:
            config = {"fetch_enabled": True}
    elif update_type == 3:
        # name + description
        name = draw(valid_name_strategy())
        description = draw(valid_description_strategy())
        config = None
    elif update_type == 4:
        # name + config
        name = draw(valid_name_strategy())
        description = None
        config = draw(valid_config_strategy())
        if not config:
            config = {"fetch_enabled": True}
    elif update_type == 5:
        # description + config
        name = None
        description = draw(valid_description_strategy())
        config = draw(valid_config_strategy())
        if not config:
            config = {"fetch_enabled": True}
    else:
        # Todos los campos
        name = draw(valid_name_strategy())
        description = draw(valid_description_strategy())
        config = draw(valid_config_strategy())
        if not config:
            config = {"fetch_enabled": True}

    correlation_id = (
        draw(st.text(min_size=1, max_size=50).filter(lambda x: x.strip()))
        if draw(st.booleans())
        else None
    )

    return UpdateRssFeedCommand(
        source_id=source_id,
        name=name,
        description=description,
        source_config=config,
        correlation_id=correlation_id,
    )


@st.composite
def invalid_command_strategy(draw):
    """Genera comandos inválidos."""
    error_type = draw(st.integers(min_value=0, max_value=5))

    if error_type == 0:
        # source_id inválido
        return UpdateRssFeedCommand(
            source_id=draw(invalid_source_id_strategy()),
            name=draw(valid_name_strategy()),
        )

    if error_type == 1:
        # Sin actualizaciones
        return UpdateRssFeedCommand(source_id=draw(valid_source_id_strategy()))

    if error_type == 2:
        # name inválido
        return UpdateRssFeedCommand(
            source_id=draw(valid_source_id_strategy()),
            name=draw(invalid_name_strategy()),
        )

    if error_type == 3:
        # description inválida
        return UpdateRssFeedCommand(
            source_id=draw(valid_source_id_strategy()),
            description=draw(invalid_description_strategy()),
        )

    if error_type == 4:
        # config inválida
        return UpdateRssFeedCommand(
            source_id=draw(valid_source_id_strategy()),
            source_config=draw(invalid_config_strategy()),
        )

    if error_type == 5:
        # correlation_id inválido
        return UpdateRssFeedCommand(
            source_id=draw(valid_source_id_strategy()),
            name=draw(valid_name_strategy()),
            correlation_id=draw(st.text(max_size=10).filter(lambda x: not x.strip())),
        )

    return UpdateRssFeedCommand(source_id=draw(valid_source_id_strategy()))


class TestUpdateSourceValidatorProperties:
    """Property-based tests para UpdateSourceValidator."""

    @given(command=valid_command_strategy())
    def test_property_valid_commands_never_raise_exceptions(
        self, command: UpdateRssFeedCommand
    ):
        """
        Property 2: Valid commands never raise exceptions.

        Feature: remove-base-validator, Property 2: Valid commands never raise exceptions
        Validates: Requirements 2.2
        """
        # Arrange
        validator = UpdateSourceValidator()

        # Act & Assert - No debería lanzar excepción
        validator.validate(command)

    @given(command=invalid_command_strategy())
    def test_property_invalid_commands_always_raise_exceptions(
        self, command: UpdateRssFeedCommand
    ):
        """
        Property 1: Invalid commands always raise exceptions.

        Feature: remove-base-validator, Property 1: Invalid commands always raise exceptions
        Validates: Requirements 2.1
        """
        # Arrange
        validator = UpdateSourceValidator()

        # Act & Assert - Debería lanzar InvalidSourceUpdateError
        with pytest.raises(InvalidSourceUpdateError):
            validator.validate(command)
