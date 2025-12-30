"""Unit tests para ErrorInfo Value Object."""

from datetime import datetime, timezone

import pytest

from src.rss.article.domain.value_objects.error_info import ErrorInfo


class TestErrorInfo:
    """Unit tests para ErrorInfo VO."""

    def test_no_error_creates_valid_instance(self):
        """Debería crear instancia sin error."""
        info = ErrorInfo.no_error()

        assert not info.has_error
        assert info.error_type is None
        assert info.error_message is None
        assert info.error_marked_by is None
        assert info.error_marked_at is None
        assert info.is_valid
        assert not info.has_timestamp

    def test_create_error_creates_valid_instance(self):
        """Debería crear instancia con error."""
        info = ErrorInfo.create_error(
            error_type="validation_error",
            error_message="Contenido inválido",
            marked_by="validation_service",
        )

        assert info.has_error
        assert info.error_type == "validation_error"
        assert info.error_message == "Contenido inválido"
        assert info.error_marked_by == "validation_service"
        assert info.error_marked_at is not None
        assert not info.is_valid
        assert info.has_timestamp

    def test_create_error_with_custom_timestamp(self):
        """Debería crear error con timestamp personalizado."""
        custom_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        info = ErrorInfo.create_error(
            error_type="test_error",
            error_message="Test",
            marked_by="test",
            marked_at=custom_time,
        )

        assert info.error_marked_at == custom_time

    def test_create_error_rejects_empty_error_type(self):
        """Debería rechazar error_type vacío."""
        with pytest.raises(ValueError) as exc_info:
            ErrorInfo.create_error(
                error_type="", error_message="Test", marked_by="test"
            )

        assert "error_type no puede ser None o vacío" in str(exc_info.value)

    def test_create_error_rejects_whitespace_error_type(self):
        """Debería rechazar error_type con solo espacios."""
        with pytest.raises(ValueError) as exc_info:
            ErrorInfo.create_error(
                error_type="   ", error_message="Test", marked_by="test"
            )

        assert "error_type no puede ser None o vacío" in str(exc_info.value)

    def test_create_error_rejects_empty_error_message(self):
        """Debería rechazar error_message vacío."""
        with pytest.raises(ValueError) as exc_info:
            ErrorInfo.create_error(
                error_type="test", error_message="", marked_by="test"
            )

        assert "error_message no puede ser None o vacío" in str(exc_info.value)

    def test_create_error_rejects_empty_marked_by(self):
        """Debería rechazar marked_by vacío."""
        with pytest.raises(ValueError) as exc_info:
            ErrorInfo.create_error(
                error_type="test", error_message="Test", marked_by=""
            )

        assert "marked_by no puede ser None o vacío" in str(exc_info.value)

    def test_post_init_validates_has_error_true_requires_fields(self):
        """Debería validar que has_error=True requiere campos."""
        with pytest.raises(ValueError) as exc_info:
            ErrorInfo(has_error=True, error_type=None)

        assert "error_type es requerido" in str(exc_info.value)

    def test_post_init_validates_error_type_not_empty(self):
        """Debería validar que error_type no esté vacío."""
        with pytest.raises(ValueError) as exc_info:
            ErrorInfo(
                has_error=True,
                error_type="",
                error_message="Test",
                error_marked_by="test",
            )

        assert "error_type es requerido" in str(exc_info.value)

    def test_post_init_validates_error_message_not_empty(self):
        """Debería validar que error_message no esté vacío."""
        with pytest.raises(ValueError) as exc_info:
            ErrorInfo(
                has_error=True,
                error_type="test",
                error_message="",
                error_marked_by="test",
            )

        assert "error_message es requerido" in str(exc_info.value)

    def test_post_init_validates_error_marked_by_not_empty(self):
        """Debería validar que error_marked_by no esté vacío."""
        with pytest.raises(ValueError) as exc_info:
            ErrorInfo(
                has_error=True,
                error_type="test",
                error_message="Test",
                error_marked_by="",
            )

        assert "error_marked_by es requerido" in str(exc_info.value)

    def test_clear_error_returns_new_instance(self):
        """Debería retornar nueva instancia sin error."""
        original = ErrorInfo.create_error(
            error_type="test_error", error_message="Test", marked_by="test"
        )

        cleared = original.clear_error()

        # Verificar que son instancias diferentes
        assert original is not cleared

        # Verificar que el original no cambió
        assert original.has_error
        assert original.error_type == "test_error"

        # Verificar que el nuevo no tiene error
        assert not cleared.has_error
        assert cleared.error_type is None
        assert cleared.error_message is None

    def test_update_error_returns_new_instance(self):
        """Debería retornar nueva instancia con error actualizado."""
        original = ErrorInfo.create_error(
            error_type="old_error", error_message="Old message", marked_by="old_system"
        )

        updated = original.update_error(
            error_type="new_error", error_message="New message", marked_by="new_system"
        )

        # Verificar que son instancias diferentes
        assert original is not updated

        # Verificar que el original no cambió
        assert original.error_type == "old_error"

        # Verificar que el nuevo tiene valores actualizados
        assert updated.error_type == "new_error"
        assert updated.error_message == "New message"
        assert updated.error_marked_by == "new_system"

    def test_get_error_summary_returns_formatted_string(self):
        """Debería retornar resumen formateado del error."""
        info = ErrorInfo.create_error(
            error_type="validation_error",
            error_message="Contenido inválido",
            marked_by="validator",
        )

        summary = info.get_error_summary()

        assert summary is not None
        assert "validation_error" in summary
        assert "Contenido inválido" in summary
        assert "validator" in summary

    def test_get_error_summary_returns_none_when_no_error(self):
        """Debería retornar None cuando no hay error."""
        info = ErrorInfo.no_error()

        summary = info.get_error_summary()

        assert summary is None

    def test_immutability(self):
        """Debería ser inmutable (frozen dataclass)."""
        info = ErrorInfo.no_error()

        with pytest.raises(AttributeError):
            info.has_error = True  # type: ignore

    def test_is_valid_true_when_no_error(self):
        """Debería retornar True cuando no hay error."""
        info = ErrorInfo.no_error()

        assert info.is_valid

    def test_is_valid_false_when_has_error(self):
        """Debería retornar False cuando hay error."""
        info = ErrorInfo.create_error(
            error_type="test", error_message="Test", marked_by="test"
        )

        assert not info.is_valid

    def test_default_values(self):
        """Debería tener valores por defecto correctos."""
        info = ErrorInfo()

        assert not info.has_error
        assert info.error_type is None
        assert info.error_message is None
        assert info.error_marked_by is None
        assert info.error_marked_at is None
