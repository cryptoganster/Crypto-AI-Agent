"""Tests para AIProcessingConfig.

Requirements: 3.5
"""

import os

import pytest

from src.shared.config.ai_processing_config import AIProcessingConfig


class TestAIProcessingConfig:
    """Tests para AIProcessingConfig."""

    def test_default_values_are_correct(self):
        """Debería tener valores por defecto correctos."""
        # Arrange & Act
        config = AIProcessingConfig()

        # Assert - Feature Flags
        assert config.use_new_ai_processing_pipeline is False
        assert config.enable_global_summary is True
        assert config.enable_tldr is True

        # Assert - Límites de Texto
        assert config.max_text_length_for_global_summary == 10000
        assert config.max_chunk_summaries_for_tldr == 10

        # Assert - Retry Configuration
        assert config.max_retries == 3
        assert config.retry_delay_seconds == 2.0

        # Assert - Timeouts
        assert config.chunking_timeout_seconds == 30.0
        assert config.embedding_timeout_seconds == 60.0
        assert config.summarization_timeout_seconds == 120.0

        # Assert - Batch Processing
        assert config.summary_batch_size == 5

    def test_from_env_loads_from_environment_variables(self, monkeypatch):
        """Debería cargar valores desde variables de entorno."""
        # Arrange
        monkeypatch.setenv("AI_USE_NEW_PIPELINE", "true")
        monkeypatch.setenv("AI_ENABLE_GLOBAL_SUMMARY", "false")
        monkeypatch.setenv("AI_ENABLE_TLDR", "false")
        monkeypatch.setenv("AI_MAX_TEXT_LENGTH_GLOBAL_SUMMARY", "5000")
        monkeypatch.setenv("AI_MAX_CHUNK_SUMMARIES_TLDR", "5")
        monkeypatch.setenv("AI_MAX_RETRIES", "5")
        monkeypatch.setenv("AI_RETRY_DELAY_SECONDS", "1.5")
        monkeypatch.setenv("AI_CHUNKING_TIMEOUT", "60.0")
        monkeypatch.setenv("AI_EMBEDDING_TIMEOUT", "120.0")
        monkeypatch.setenv("AI_SUMMARIZATION_TIMEOUT", "180.0")
        monkeypatch.setenv("AI_SUMMARY_BATCH_SIZE", "10")

        # Act
        config = AIProcessingConfig.from_env()

        # Assert
        assert config.use_new_ai_processing_pipeline is True
        assert config.enable_global_summary is False
        assert config.enable_tldr is False
        assert config.max_text_length_for_global_summary == 5000
        assert config.max_chunk_summaries_for_tldr == 5
        assert config.max_retries == 5
        assert config.retry_delay_seconds == 1.5
        assert config.chunking_timeout_seconds == 60.0
        assert config.embedding_timeout_seconds == 120.0
        assert config.summarization_timeout_seconds == 180.0
        assert config.summary_batch_size == 10

    def test_from_env_uses_defaults_when_env_vars_not_set(self, monkeypatch):
        """Debería usar valores por defecto cuando variables de entorno no están configuradas."""
        # Arrange - Limpiar variables de entorno
        for key in [
            "AI_USE_NEW_PIPELINE",
            "AI_ENABLE_GLOBAL_SUMMARY",
            "AI_ENABLE_TLDR",
            "AI_MAX_TEXT_LENGTH_GLOBAL_SUMMARY",
            "AI_MAX_CHUNK_SUMMARIES_TLDR",
            "AI_MAX_RETRIES",
            "AI_RETRY_DELAY_SECONDS",
            "AI_CHUNKING_TIMEOUT",
            "AI_EMBEDDING_TIMEOUT",
            "AI_SUMMARIZATION_TIMEOUT",
            "AI_SUMMARY_BATCH_SIZE",
        ]:
            monkeypatch.delenv(key, raising=False)

        # Act
        config = AIProcessingConfig.from_env()

        # Assert - Debe usar valores por defecto
        assert config.use_new_ai_processing_pipeline is False
        assert config.enable_global_summary is True
        assert config.enable_tldr is True
        assert config.max_text_length_for_global_summary == 10000
        assert config.max_chunk_summaries_for_tldr == 10
        assert config.max_retries == 3
        assert config.retry_delay_seconds == 2.0
        assert config.chunking_timeout_seconds == 30.0
        assert config.embedding_timeout_seconds == 60.0
        assert config.summarization_timeout_seconds == 120.0
        assert config.summary_batch_size == 5

    def test_from_env_with_custom_prefix(self, monkeypatch):
        """Debería permitir prefijo personalizado para variables de entorno."""
        # Arrange
        monkeypatch.setenv("CUSTOM_USE_NEW_PIPELINE", "true")
        monkeypatch.setenv("CUSTOM_MAX_RETRIES", "7")

        # Act
        config = AIProcessingConfig.from_env(env_prefix="CUSTOM_")

        # Assert
        assert config.use_new_ai_processing_pipeline is True
        assert config.max_retries == 7

    def test_for_testing_creates_config_with_defaults(self):
        """Debería crear configuración para testing con valores por defecto."""
        # Act
        config = AIProcessingConfig.for_testing()

        # Assert
        assert config.use_new_ai_processing_pipeline is False
        assert config.max_retries == 3
        assert config.chunking_timeout_seconds == 30.0

    def test_for_testing_allows_overrides(self):
        """Debería permitir sobrescribir valores en configuración de testing."""
        # Act
        config = AIProcessingConfig.for_testing(
            use_new_ai_processing_pipeline=True,
            max_retries=10,
            chunking_timeout_seconds=120.0,
        )

        # Assert
        assert config.use_new_ai_processing_pipeline is True
        assert config.max_retries == 10
        assert config.chunking_timeout_seconds == 120.0
        # Otros valores deben ser defaults
        assert config.enable_global_summary is True
        assert config.summary_batch_size == 5

    def test_validation_rejects_invalid_max_text_length(self):
        """Debería rechazar max_text_length_for_global_summary inválido."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            AIProcessingConfig(max_text_length_for_global_summary=0)

        assert "max_text_length_for_global_summary debe ser > 0" in str(exc_info.value)

    def test_validation_rejects_invalid_max_chunk_summaries(self):
        """Debería rechazar max_chunk_summaries_for_tldr inválido."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            AIProcessingConfig(max_chunk_summaries_for_tldr=-1)

        assert "max_chunk_summaries_for_tldr debe ser > 0" in str(exc_info.value)

    def test_validation_rejects_negative_max_retries(self):
        """Debería rechazar max_retries negativo."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            AIProcessingConfig(max_retries=-1)

        assert "max_retries debe ser >= 0" in str(exc_info.value)

    def test_validation_accepts_zero_max_retries(self):
        """Debería aceptar max_retries = 0 (sin reintentos)."""
        # Act
        config = AIProcessingConfig(max_retries=0)

        # Assert
        assert config.max_retries == 0

    def test_validation_rejects_negative_retry_delay(self):
        """Debería rechazar retry_delay_seconds negativo."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            AIProcessingConfig(retry_delay_seconds=-1.0)

        assert "retry_delay_seconds debe ser >= 0" in str(exc_info.value)

    def test_validation_rejects_invalid_chunking_timeout(self):
        """Debería rechazar chunking_timeout_seconds inválido."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            AIProcessingConfig(chunking_timeout_seconds=0)

        assert "chunking_timeout_seconds debe ser > 0" in str(exc_info.value)

    def test_validation_rejects_invalid_embedding_timeout(self):
        """Debería rechazar embedding_timeout_seconds inválido."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            AIProcessingConfig(embedding_timeout_seconds=-10.0)

        assert "embedding_timeout_seconds debe ser > 0" in str(exc_info.value)

    def test_validation_rejects_invalid_summarization_timeout(self):
        """Debería rechazar summarization_timeout_seconds inválido."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            AIProcessingConfig(summarization_timeout_seconds=0)

        assert "summarization_timeout_seconds debe ser > 0" in str(exc_info.value)

    def test_validation_rejects_invalid_summary_batch_size(self):
        """Debería rechazar summary_batch_size inválido."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            AIProcessingConfig(summary_batch_size=0)

        assert "summary_batch_size debe ser > 0" in str(exc_info.value)

    def test_config_is_frozen(self):
        """Debería ser inmutable (frozen dataclass)."""
        # Arrange
        config = AIProcessingConfig()

        # Act & Assert
        with pytest.raises(AttributeError):
            config.max_retries = 10

    def test_feature_flag_use_new_pipeline_defaults_to_false(self):
        """Feature flag use_new_ai_processing_pipeline debería ser False por defecto."""
        # Arrange & Act
        config = AIProcessingConfig()

        # Assert
        assert config.use_new_ai_processing_pipeline is False

    def test_feature_flag_enable_global_summary_defaults_to_true(self):
        """Feature flag enable_global_summary debería ser True por defecto."""
        # Arrange & Act
        config = AIProcessingConfig()

        # Assert
        assert config.enable_global_summary is True

    def test_feature_flag_enable_tldr_defaults_to_true(self):
        """Feature flag enable_tldr debería ser True por defecto."""
        # Arrange & Act
        config = AIProcessingConfig()

        # Assert
        assert config.enable_tldr is True

    def test_from_env_parses_boolean_flags_correctly(self, monkeypatch):
        """Debería parsear flags booleanos correctamente desde strings."""
        # Arrange - Probar diferentes variaciones de true/false
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("1", False),  # Solo "true" es True
            ("yes", False),  # Solo "true" es True
        ]

        for env_value, expected in test_cases:
            # Arrange
            monkeypatch.setenv("AI_USE_NEW_PIPELINE", env_value)

            # Act
            config = AIProcessingConfig.from_env()

            # Assert
            assert (
                config.use_new_ai_processing_pipeline is expected
            ), f"Expected {expected} for env value '{env_value}'"

    def test_all_timeouts_are_positive(self):
        """Todos los timeouts deben ser positivos."""
        # Arrange & Act
        config = AIProcessingConfig()

        # Assert
        assert config.chunking_timeout_seconds > 0
        assert config.embedding_timeout_seconds > 0
        assert config.summarization_timeout_seconds > 0

    def test_all_limits_are_positive(self):
        """Todos los límites deben ser positivos."""
        # Arrange & Act
        config = AIProcessingConfig()

        # Assert
        assert config.max_text_length_for_global_summary > 0
        assert config.max_chunk_summaries_for_tldr > 0
        assert config.summary_batch_size > 0

    def test_retry_configuration_is_sensible(self):
        """Configuración de retry debe ser sensata."""
        # Arrange & Act
        config = AIProcessingConfig()

        # Assert
        assert config.max_retries >= 0
        assert config.retry_delay_seconds >= 0
        # Delay no debería ser excesivo
        assert config.retry_delay_seconds < 60.0
