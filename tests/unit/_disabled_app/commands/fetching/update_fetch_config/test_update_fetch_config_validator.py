"""Tests unitarios para UpdateFetchConfigValidator."""

import pytest

from src.app.commands.fetching.update_fetch_config.command import (
    UpdateFetchConfigCommand,
)
from src.app.commands.fetching.update_fetch_config.exception import (
    InvalidFetchConfigError,
)
from src.app.commands.fetching.update_fetch_config.validator import (
    UpdateFetchConfigValidator,
)


class TestUpdateFetchConfigValidator:
    """Tests para UpdateFetchConfigValidator."""

    @pytest.fixture
    def validator(self):
        """Crea instancia del validator."""
        return UpdateFetchConfigValidator()

    def test_validate_with_valid_interval_seconds_succeeds(self, validator):
        """Debería validar correctamente cuando se actualiza interval_seconds."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="src-123",
            fetch_config={"interval_seconds": 300},
        )

        # Act & Assert - No debería lanzar excepción
        validator.validate(command)

    def test_validate_with_valid_max_concurrency_succeeds(self, validator):
        """Debería validar correctamente cuando se actualiza max_concurrency."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="src-123",
            fetch_config={"max_concurrency": 10},
        )

        # Act & Assert - No debería lanzar excepción
        validator.validate(command)

    def test_validate_with_valid_request_timeout_succeeds(self, validator):
        """Debería validar correctamente cuando se actualiza request_timeout."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="src-123",
            fetch_config={"request_timeout": 60},
        )

        # Act & Assert - No debería lanzar excepción
        validator.validate(command)

    def test_validate_with_all_fields_succeeds(self, validator):
        """Debería validar correctamente cuando se actualizan todos los campos."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="src-123",
            fetch_config={
                "interval_seconds": 600,
                "max_concurrency": 20,
                "request_timeout": 120,
                "user_agent": "CustomBot/1.0",
                "max_articles_per_fetch": 500,
                "retry_attempts": 5,
                "backoff_multiplier": 2.0,
                "quality_threshold": 0.8,
            },
            correlation_id="corr-456",
            updated_by="admin",
        )

        # Act & Assert - No debería lanzar excepción
        validator.validate(command)

    def test_validate_with_empty_source_id_raises_exception(self, validator):
        """Debería lanzar excepción cuando source_id está vacío."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="",
            fetch_config={"interval_seconds": 300},
        )

        # Act & Assert
        with pytest.raises(InvalidFetchConfigError) as exc_info:
            validator.validate(command)

        assert "source_id" in str(exc_info.value)

    def test_validate_with_none_source_id_raises_exception(self, validator):
        """Debería lanzar excepción cuando source_id es None."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id=None,
            fetch_config={"interval_seconds": 300},
        )

        # Act & Assert
        with pytest.raises(InvalidFetchConfigError) as exc_info:
            validator.validate(command)

        assert "source_id es requerido" in str(exc_info.value)

    def test_validate_with_none_fetch_config_raises_exception(self, validator):
        """Debería lanzar excepción cuando fetch_config es None."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="src-123",
            fetch_config=None,
        )

        # Act & Assert
        with pytest.raises(InvalidFetchConfigError) as exc_info:
            validator.validate(command)

        assert "fetch_config es requerido" in str(exc_info.value)

    def test_validate_with_invalid_fetch_config_type_raises_exception(self, validator):
        """Debería lanzar excepción cuando fetch_config no es un diccionario."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="src-123",
            fetch_config="invalid",
        )

        # Act & Assert
        with pytest.raises(InvalidFetchConfigError) as exc_info:
            validator.validate(command)

        assert "fetch_config es requerido y debe ser diccionario válido" in str(
            exc_info.value
        )

    def test_validate_with_invalid_config_fields_raises_exception(self, validator):
        """Debería lanzar excepción cuando fetch_config tiene campos inválidos."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="src-123",
            fetch_config={
                "invalid_field": "value",
                "another_invalid": 123,
            },
        )

        # Act & Assert
        with pytest.raises(InvalidFetchConfigError) as exc_info:
            validator.validate(command)

        assert "Campos de configuración no válidos" in str(exc_info.value)

    def test_validate_with_interval_seconds_too_low_raises_exception(self, validator):
        """Debería lanzar excepción cuando interval_seconds es menor a 60."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="src-123",
            fetch_config={"interval_seconds": 30},
        )

        # Act & Assert
        with pytest.raises(InvalidFetchConfigError) as exc_info:
            validator.validate(command)

        assert "interval_seconds debe ser al menos 60 segundos" in str(exc_info.value)

    def test_validate_with_negative_interval_seconds_raises_exception(self, validator):
        """Debería lanzar excepción cuando interval_seconds es negativo."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="src-123",
            fetch_config={"interval_seconds": -100},
        )

        # Act & Assert
        with pytest.raises(InvalidFetchConfigError) as exc_info:
            validator.validate(command)

        assert "interval_seconds debe ser entero positivo" in str(exc_info.value)

    def test_validate_with_max_concurrency_too_high_raises_exception(self, validator):
        """Debería lanzar excepción cuando max_concurrency excede 50."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="src-123",
            fetch_config={"max_concurrency": 51},
        )

        # Act & Assert
        with pytest.raises(InvalidFetchConfigError) as exc_info:
            validator.validate(command)

        assert "max_concurrency debe ser entero entre 1 y 50" in str(exc_info.value)

    def test_validate_with_max_concurrency_zero_raises_exception(self, validator):
        """Debería lanzar excepción cuando max_concurrency es cero."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="src-123",
            fetch_config={"max_concurrency": 0},
        )

        # Act & Assert
        with pytest.raises(InvalidFetchConfigError) as exc_info:
            validator.validate(command)

        assert "max_concurrency debe ser entero entre 1 y 50" in str(exc_info.value)

    def test_validate_with_request_timeout_too_low_raises_exception(self, validator):
        """Debería lanzar excepción cuando request_timeout es menor a 5."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="src-123",
            fetch_config={"request_timeout": 3},
        )

        # Act & Assert
        with pytest.raises(InvalidFetchConfigError) as exc_info:
            validator.validate(command)

        assert "request_timeout debe ser entero entre 5 y 300 segundos" in str(
            exc_info.value
        )

    def test_validate_with_request_timeout_too_high_raises_exception(self, validator):
        """Debería lanzar excepción cuando request_timeout excede 300."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="src-123",
            fetch_config={"request_timeout": 400},
        )

        # Act & Assert
        with pytest.raises(InvalidFetchConfigError) as exc_info:
            validator.validate(command)

        assert "request_timeout debe ser entero entre 5 y 300 segundos" in str(
            exc_info.value
        )

    def test_validate_with_empty_user_agent_raises_exception(self, validator):
        """Debería lanzar excepción cuando user_agent está vacío."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="src-123",
            fetch_config={"user_agent": "   "},
        )

        # Act & Assert
        with pytest.raises(InvalidFetchConfigError) as exc_info:
            validator.validate(command)

        assert "user_agent debe ser string no vacío" in str(exc_info.value)

    def test_validate_with_user_agent_too_long_raises_exception(self, validator):
        """Debería lanzar excepción cuando user_agent excede 255 caracteres."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="src-123",
            fetch_config={"user_agent": "a" * 256},
        )

        # Act & Assert
        with pytest.raises(InvalidFetchConfigError) as exc_info:
            validator.validate(command)

        assert "user_agent no puede exceder 255 caracteres" in str(exc_info.value)

    def test_validate_with_max_articles_per_fetch_zero_raises_exception(
        self, validator
    ):
        """Debería lanzar excepción cuando max_articles_per_fetch es cero."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="src-123",
            fetch_config={"max_articles_per_fetch": 0},
        )

        # Act & Assert
        with pytest.raises(InvalidFetchConfigError) as exc_info:
            validator.validate(command)

        assert "max_articles_per_fetch debe ser entero positivo" in str(exc_info.value)

    def test_validate_with_max_articles_per_fetch_too_high_raises_exception(
        self, validator
    ):
        """Debería lanzar excepción cuando max_articles_per_fetch excede 1000."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="src-123",
            fetch_config={"max_articles_per_fetch": 1001},
        )

        # Act & Assert
        with pytest.raises(InvalidFetchConfigError) as exc_info:
            validator.validate(command)

        assert "max_articles_per_fetch no puede exceder 1000" in str(exc_info.value)

    def test_validate_with_retry_attempts_negative_raises_exception(self, validator):
        """Debería lanzar excepción cuando retry_attempts es negativo."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="src-123",
            fetch_config={"retry_attempts": -1},
        )

        # Act & Assert
        with pytest.raises(InvalidFetchConfigError) as exc_info:
            validator.validate(command)

        assert "retry_attempts debe ser entero entre 0 y 10" in str(exc_info.value)

    def test_validate_with_retry_attempts_too_high_raises_exception(self, validator):
        """Debería lanzar excepción cuando retry_attempts excede 10."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="src-123",
            fetch_config={"retry_attempts": 11},
        )

        # Act & Assert
        with pytest.raises(InvalidFetchConfigError) as exc_info:
            validator.validate(command)

        assert "retry_attempts debe ser entero entre 0 y 10" in str(exc_info.value)

    def test_validate_with_negative_backoff_multiplier_raises_exception(
        self, validator
    ):
        """Debería lanzar excepción cuando backoff_multiplier es negativo."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="src-123",
            fetch_config={"backoff_multiplier": -1.5},
        )

        # Act & Assert
        with pytest.raises(InvalidFetchConfigError) as exc_info:
            validator.validate(command)

        assert "backoff_multiplier debe ser número positivo" in str(exc_info.value)

    def test_validate_with_quality_threshold_too_high_raises_exception(self, validator):
        """Debería lanzar excepción cuando quality_threshold excede 1.0."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="src-123",
            fetch_config={"quality_threshold": 1.5},
        )

        # Act & Assert
        with pytest.raises(InvalidFetchConfigError) as exc_info:
            validator.validate(command)

        assert "quality_threshold debe ser número entre 0.0 y 1.0" in str(
            exc_info.value
        )

    def test_validate_with_quality_threshold_negative_raises_exception(self, validator):
        """Debería lanzar excepción cuando quality_threshold es negativo."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="src-123",
            fetch_config={"quality_threshold": -0.1},
        )

        # Act & Assert
        with pytest.raises(InvalidFetchConfigError) as exc_info:
            validator.validate(command)

        assert "quality_threshold debe ser número entre 0.0 y 1.0" in str(
            exc_info.value
        )

    def test_validate_with_empty_correlation_id_raises_exception(self, validator):
        """Debería lanzar excepción cuando correlation_id está vacío."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="src-123",
            fetch_config={"interval_seconds": 300},
            correlation_id="   ",
        )

        # Act & Assert
        with pytest.raises(InvalidFetchConfigError) as exc_info:
            validator.validate(command)

        assert "correlation_id debe ser string no vacío" in str(exc_info.value)

    def test_validate_with_empty_updated_by_raises_exception(self, validator):
        """Debería lanzar excepción cuando updated_by está vacío."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="src-123",
            fetch_config={"interval_seconds": 300},
            updated_by="   ",
        )

        # Act & Assert
        with pytest.raises(InvalidFetchConfigError) as exc_info:
            validator.validate(command)

        assert "updated_by debe ser string no vacío" in str(exc_info.value)

    def test_validate_with_multiple_errors_combines_messages(self, validator):
        """Debería combinar múltiples errores en un solo mensaje."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="",
            fetch_config={
                "interval_seconds": 30,
                "max_concurrency": 100,
                "quality_threshold": 2.0,
            },
        )

        # Act & Assert
        with pytest.raises(InvalidFetchConfigError) as exc_info:
            validator.validate(command)

        error_message = str(exc_info.value)
        assert "source_id" in error_message
        assert "interval_seconds" in error_message
        assert "max_concurrency" in error_message
        assert "quality_threshold" in error_message

    def test_validate_with_valid_boundary_values_succeeds(self, validator):
        """Debería validar correctamente con valores límite válidos."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="src-123",
            fetch_config={
                "interval_seconds": 60,  # Mínimo válido
                "max_concurrency": 1,  # Mínimo válido
                "request_timeout": 5,  # Mínimo válido
                "max_articles_per_fetch": 1,  # Mínimo válido
                "retry_attempts": 0,  # Mínimo válido
                "quality_threshold": 0.0,  # Mínimo válido
            },
        )

        # Act & Assert - No debería lanzar excepción
        validator.validate(command)

    def test_validate_with_valid_max_boundary_values_succeeds(self, validator):
        """Debería validar correctamente con valores límite máximos válidos."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="src-123",
            fetch_config={
                "max_concurrency": 50,  # Máximo válido
                "request_timeout": 300,  # Máximo válido
                "max_articles_per_fetch": 1000,  # Máximo válido
                "retry_attempts": 10,  # Máximo válido
                "quality_threshold": 1.0,  # Máximo válido
            },
        )

        # Act & Assert - No debería lanzar excepción
        validator.validate(command)

    def test_validate_with_none_correlation_id_succeeds(self, validator):
        """Debería validar correctamente cuando correlation_id es None."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="src-123",
            fetch_config={"interval_seconds": 300},
            correlation_id=None,
        )

        # Act & Assert - No debería lanzar excepción
        validator.validate(command)

    def test_validate_with_none_updated_by_succeeds(self, validator):
        """Debería validar correctamente cuando updated_by es None."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="src-123",
            fetch_config={"interval_seconds": 300},
            updated_by=None,
        )

        # Act & Assert - No debería lanzar excepción
        validator.validate(command)
