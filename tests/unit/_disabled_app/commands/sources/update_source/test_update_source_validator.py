"""Tests unitarios para UpdateSourceValidator."""

import pytest

from src.rss.feed.app.commands.update_source.command import UpdateRssFeedCommand
from src.rss.feed.app.commands.update_source.exception import InvalidSourceUpdateError
from src.rss.feed.app.commands.update_source.validator import UpdateSourceValidator


class TestUpdateSourceValidator:
    """Tests para UpdateSourceValidator."""

    @pytest.fixture
    def validator(self):
        """Crea instancia del validator."""
        return UpdateSourceValidator()

    def test_validate_with_valid_name_update_succeeds(self, validator):
        """Debería validar correctamente cuando se actualiza solo el nombre."""
        # Arrange
        command = UpdateRssFeedCommand(
            source_id="src-123",
            name="Nuevo Nombre",
        )

        # Act & Assert - No debería lanzar excepción
        validator.validate(command)

    def test_validate_with_valid_description_update_succeeds(self, validator):
        """Debería validar correctamente cuando se actualiza solo la descripción."""
        # Arrange
        command = UpdateRssFeedCommand(
            source_id="src-123",
            description="Nueva descripción del source",
        )

        # Act & Assert - No debería lanzar excepción
        validator.validate(command)

    def test_validate_with_valid_config_update_succeeds(self, validator):
        """Debería validar correctamente cuando se actualiza solo la configuración."""
        # Arrange
        command = UpdateRssFeedCommand(
            source_id="src-123",
            source_config={
                "fetch_enabled": True,
                "priority": 5,
                "quality_threshold": 0.7,
            },
        )

        # Act & Assert - No debería lanzar excepción
        validator.validate(command)

    def test_validate_with_all_fields_succeeds(self, validator):
        """Debería validar correctamente cuando se actualizan todos los campos."""
        # Arrange
        command = UpdateRssFeedCommand(
            source_id="src-123",
            name="Nuevo Nombre",
            description="Nueva descripción",
            source_config={
                "fetch_enabled": True,
                "priority": 8,
                "quality_threshold": 0.8,
                "max_fetch_retries": 3,
                "fetch_timeout_seconds": 60,
                "user_agent": "CustomBot/1.0",
            },
            correlation_id="corr-456",
        )

        # Act & Assert - No debería lanzar excepción
        validator.validate(command)

    def test_validate_with_empty_source_id_raises_exception(self, validator):
        """Debería lanzar excepción cuando source_id está vacío."""
        # Arrange
        command = UpdateRssFeedCommand(
            source_id="",
            name="Nuevo Nombre",
        )

        # Act & Assert
        with pytest.raises(InvalidSourceUpdateError) as exc_info:
            validator.validate(command)

        assert "source_id es requerido" in str(exc_info.value)

    def test_validate_with_none_source_id_raises_exception(self, validator):
        """Debería lanzar excepción cuando source_id es None."""
        # Arrange
        command = UpdateRssFeedCommand(
            source_id=None,
            name="Nuevo Nombre",
        )

        # Act & Assert
        with pytest.raises(InvalidSourceUpdateError) as exc_info:
            validator.validate(command)

        assert "source_id es requerido" in str(exc_info.value)

    def test_validate_with_no_updates_raises_exception(self, validator):
        """Debería lanzar excepción cuando no se especifica ninguna actualización."""
        # Arrange
        command = UpdateRssFeedCommand(source_id="src-123")

        # Act & Assert
        with pytest.raises(InvalidSourceUpdateError) as exc_info:
            validator.validate(command)

        assert "al menos un campo para actualizar" in str(exc_info.value)

    def test_validate_with_empty_name_raises_exception(self, validator):
        """Debería lanzar excepción cuando name está vacío."""
        # Arrange
        command = UpdateRssFeedCommand(
            source_id="src-123",
            name="   ",
        )

        # Act & Assert
        with pytest.raises(InvalidSourceUpdateError) as exc_info:
            validator.validate(command)

        assert "name debe ser string no vacío" in str(exc_info.value)

    def test_validate_with_name_too_long_raises_exception(self, validator):
        """Debería lanzar excepción cuando name excede 255 caracteres."""
        # Arrange
        command = UpdateRssFeedCommand(
            source_id="src-123",
            name="a" * 256,
        )

        # Act & Assert
        with pytest.raises(InvalidSourceUpdateError) as exc_info:
            validator.validate(command)

        assert "name no puede exceder 255 caracteres" in str(exc_info.value)

    def test_validate_with_description_too_long_raises_exception(self, validator):
        """Debería lanzar excepción cuando description excede 1000 caracteres."""
        # Arrange
        command = UpdateRssFeedCommand(
            source_id="src-123",
            description="a" * 1001,
        )

        # Act & Assert
        with pytest.raises(InvalidSourceUpdateError) as exc_info:
            validator.validate(command)

        assert "description no puede exceder 1000 caracteres" in str(exc_info.value)

    def test_validate_with_invalid_config_type_raises_exception(self, validator):
        """Debería lanzar excepción cuando source_config no es un diccionario."""
        # Arrange
        command = UpdateRssFeedCommand(
            source_id="src-123",
            source_config="invalid",
        )

        # Act & Assert
        with pytest.raises(InvalidSourceUpdateError) as exc_info:
            validator.validate(command)

        assert "source_config debe ser un diccionario" in str(exc_info.value)

    def test_validate_with_invalid_config_fields_raises_exception(self, validator):
        """Debería lanzar excepción cuando source_config tiene campos inválidos."""
        # Arrange
        command = UpdateRssFeedCommand(
            source_id="src-123",
            source_config={
                "invalid_field": "value",
                "another_invalid": 123,
            },
        )

        # Act & Assert
        with pytest.raises(InvalidSourceUpdateError) as exc_info:
            validator.validate(command)

        assert "Campos de configuración no válidos" in str(exc_info.value)

    def test_validate_with_invalid_fetch_enabled_type_raises_exception(self, validator):
        """Debería lanzar excepción cuando fetch_enabled no es boolean."""
        # Arrange
        command = UpdateRssFeedCommand(
            source_id="src-123",
            source_config={"fetch_enabled": "true"},
        )

        # Act & Assert
        with pytest.raises(InvalidSourceUpdateError) as exc_info:
            validator.validate(command)

        assert "fetch_enabled debe ser boolean" in str(exc_info.value)

    def test_validate_with_invalid_priority_range_raises_exception(self, validator):
        """Debería lanzar excepción cuando priority está fuera de rango."""
        # Arrange
        command = UpdateRssFeedCommand(
            source_id="src-123",
            source_config={"priority": 11},
        )

        # Act & Assert
        with pytest.raises(InvalidSourceUpdateError) as exc_info:
            validator.validate(command)

        assert "priority debe ser entero entre 1 y 10" in str(exc_info.value)

    def test_validate_with_invalid_quality_threshold_range_raises_exception(
        self, validator
    ):
        """Debería lanzar excepción cuando quality_threshold está fuera de rango."""
        # Arrange
        command = UpdateRssFeedCommand(
            source_id="src-123",
            source_config={"quality_threshold": 1.5},
        )

        # Act & Assert
        with pytest.raises(InvalidSourceUpdateError) as exc_info:
            validator.validate(command)

        assert "quality_threshold debe ser número entre 0.0 y 1.0" in str(
            exc_info.value
        )

    def test_validate_with_negative_max_retries_raises_exception(self, validator):
        """Debería lanzar excepción cuando max_fetch_retries es negativo."""
        # Arrange
        command = UpdateRssFeedCommand(
            source_id="src-123",
            source_config={"max_fetch_retries": -1},
        )

        # Act & Assert
        with pytest.raises(InvalidSourceUpdateError) as exc_info:
            validator.validate(command)

        assert "max_fetch_retries debe ser entero no negativo" in str(exc_info.value)

    def test_validate_with_invalid_timeout_raises_exception(self, validator):
        """Debería lanzar excepción cuando fetch_timeout_seconds no es positivo."""
        # Arrange
        command = UpdateRssFeedCommand(
            source_id="src-123",
            source_config={"fetch_timeout_seconds": 0},
        )

        # Act & Assert
        with pytest.raises(InvalidSourceUpdateError) as exc_info:
            validator.validate(command)

        assert "fetch_timeout_seconds debe ser entero positivo" in str(exc_info.value)

    def test_validate_with_empty_user_agent_raises_exception(self, validator):
        """Debería lanzar excepción cuando user_agent está vacío."""
        # Arrange
        command = UpdateRssFeedCommand(
            source_id="src-123",
            source_config={"user_agent": "   "},
        )

        # Act & Assert
        with pytest.raises(InvalidSourceUpdateError) as exc_info:
            validator.validate(command)

        assert "user_agent debe ser string no vacío" in str(exc_info.value)

    def test_validate_with_empty_correlation_id_raises_exception(self, validator):
        """Debería lanzar excepción cuando correlation_id está vacío."""
        # Arrange
        command = UpdateRssFeedCommand(
            source_id="src-123",
            name="Nuevo Nombre",
            correlation_id="   ",
        )

        # Act & Assert
        with pytest.raises(InvalidSourceUpdateError) as exc_info:
            validator.validate(command)

        assert "correlation_id debe ser string no vacío" in str(exc_info.value)

    def test_validate_with_multiple_errors_combines_messages(self, validator):
        """Debería combinar múltiples errores en un solo mensaje."""
        # Arrange
        command = UpdateRssFeedCommand(
            source_id="",
            name="",
            source_config={"priority": 15, "quality_threshold": 2.0},
        )

        # Act & Assert
        with pytest.raises(InvalidSourceUpdateError) as exc_info:
            validator.validate(command)

        error_message = str(exc_info.value)
        assert "source_id es requerido" in error_message
        assert "name debe ser string no vacío" in error_message
        assert "priority debe ser entero entre 1 y 10" in error_message
        assert "quality_threshold debe ser número entre 0.0 y 1.0" in error_message

    def test_validate_with_none_description_succeeds(self, validator):
        """Debería validar correctamente cuando description es None explícitamente."""
        # Arrange
        command = UpdateRssFeedCommand(
            source_id="src-123",
            name="Nuevo Nombre",
            description=None,
        )

        # Act & Assert - No debería lanzar excepción
        validator.validate(command)

    def test_validate_with_empty_description_succeeds(self, validator):
        """Debería validar correctamente cuando description está vacía."""
        # Arrange
        command = UpdateRssFeedCommand(
            source_id="src-123",
            name="Nuevo Nombre",
            description="",
        )

        # Act & Assert - No debería lanzar excepción
        validator.validate(command)

    def test_validate_with_valid_config_boundary_values_succeeds(self, validator):
        """Debería validar correctamente con valores límite válidos."""
        # Arrange
        command = UpdateRssFeedCommand(
            source_id="src-123",
            source_config={
                "priority": 1,  # Mínimo válido
                "quality_threshold": 0.0,  # Mínimo válido
                "max_fetch_retries": 0,  # Mínimo válido
                "fetch_timeout_seconds": 1,  # Mínimo válido
            },
        )

        # Act & Assert - No debería lanzar excepción
        validator.validate(command)

    def test_validate_with_valid_config_max_boundary_values_succeeds(self, validator):
        """Debería validar correctamente con valores límite máximos válidos."""
        # Arrange
        command = UpdateRssFeedCommand(
            source_id="src-123",
            source_config={
                "priority": 10,  # Máximo válido
                "quality_threshold": 1.0,  # Máximo válido
            },
        )

        # Act & Assert - No debería lanzar excepción
        validator.validate(command)
