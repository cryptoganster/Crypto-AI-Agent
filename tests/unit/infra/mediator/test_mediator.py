"""Tests unitarios para Mediator."""

from typing import Callable, Dict, Type
from unittest.mock import AsyncMock, Mock

import pytest

from src.shared.infra.mediator import HandlerNotFoundError, Mediator
from src.shared.kernel.bus import IEventBus
from src.shared.kernel.logger import ILogger


# Test fixtures y helpers
class DummyCommand:
    """Comando de prueba."""

    def __init__(self, value: str):
        self.value = value


class DummyQuery:
    """Query de prueba."""

    def __init__(self, id: str):
        self.id = id


class DummyCommandHandler:
    """Handler de prueba para DummyCommand."""

    async def handle(self, command: DummyCommand) -> dict:
        """Maneja el comando de prueba."""
        return {"success": True, "value": command.value}


class DummyQueryHandler:
    """Handler de prueba para DummyQuery."""

    async def handle(self, query: DummyQuery) -> dict:
        """Maneja el query de prueba."""
        return {"id": query.id, "data": "test data"}


class DummyEvent:
    """Evento de prueba."""

    def __init__(self, name: str):
        self.name = name


@pytest.fixture
def mock_logger():
    """Crea un mock del logger."""
    logger = Mock(spec=ILogger)
    logger.bind.return_value = logger
    logger.debug = Mock()
    logger.error = Mock()
    return logger


@pytest.fixture
def mock_event_bus():
    """Crea un mock del event bus."""
    event_bus = Mock(spec=IEventBus)
    event_bus.publish = AsyncMock()
    return event_bus


@pytest.fixture
def empty_handler_registry():
    """Crea un handler registry vacío."""
    return {}


@pytest.fixture
def handler_registry_with_command():
    """Crea un handler registry con un comando registrado."""
    handler = DummyCommandHandler()
    return {DummyCommand: handler}


@pytest.fixture
def handler_registry_with_query():
    """Crea un handler registry con un query registrado."""
    handler = DummyQueryHandler()
    return {DummyQuery: handler}


@pytest.fixture
def mediator_with_empty_registry(empty_handler_registry, mock_event_bus, mock_logger):
    """Crea un mediator con registry vacío."""
    return Mediator(
        handler_registry=empty_handler_registry,
        event_bus=mock_event_bus,
        logger=mock_logger,
    )


@pytest.fixture
def mediator_with_command(handler_registry_with_command, mock_event_bus, mock_logger):
    """Crea un mediator con un comando registrado."""
    return Mediator(
        handler_registry=handler_registry_with_command,
        event_bus=mock_event_bus,
        logger=mock_logger,
    )


@pytest.fixture
def mediator_with_query(handler_registry_with_query, mock_event_bus, mock_logger):
    """Crea un mediator con un query registrado."""
    return Mediator(
        handler_registry=handler_registry_with_query,
        event_bus=mock_event_bus,
        logger=mock_logger,
    )


class TestMediatorInitialization:
    """Tests para inicialización del Mediator."""

    def test_mediator_initializes_with_handler_registry(
        self, empty_handler_registry, mock_event_bus, mock_logger
    ):
        """Debería inicializar correctamente con handler registry."""
        # Act
        mediator = Mediator(
            handler_registry=empty_handler_registry,
            event_bus=mock_event_bus,
            logger=mock_logger,
        )

        # Assert
        assert mediator._handler_registry == empty_handler_registry
        assert mediator._event_bus == mock_event_bus
        assert mediator._logger is not None

    def test_mediator_binds_logger_with_component_name(
        self, empty_handler_registry, mock_event_bus, mock_logger
    ):
        """Debería hacer bind del logger con el nombre del componente."""
        # Act
        Mediator(
            handler_registry=empty_handler_registry,
            event_bus=mock_event_bus,
            logger=mock_logger,
        )

        # Assert
        mock_logger.bind.assert_called_once_with(component="Mediator")


class TestMediatorSendCommand:
    """Tests para envío de comandos."""

    @pytest.mark.asyncio
    async def test_send_resolves_registered_command(self, mediator_with_command):
        """Debería resolver y ejecutar un comando registrado."""
        # Arrange
        command = DummyCommand(value="test")

        # Act
        result = await mediator_with_command.send(command)

        # Assert
        assert result["success"] is True
        assert result["value"] == "test"

    @pytest.mark.asyncio
    async def test_send_logs_dispatch_for_command(
        self, mediator_with_command, mock_logger
    ):
        """Debería loggear el dispatch del comando."""
        # Arrange
        command = DummyCommand(value="test")

        # Act
        await mediator_with_command.send(command)

        # Assert
        # Verificar que se llamó debug al menos una vez
        assert mock_logger.debug.call_count >= 1
        # Verificar que se loggeó el dispatch
        calls = [str(call) for call in mock_logger.debug.call_args_list]
        assert any("Dispatching request" in str(call) for call in calls)

    @pytest.mark.asyncio
    async def test_send_logs_success_for_command(
        self, mediator_with_command, mock_logger
    ):
        """Debería loggear el éxito del comando."""
        # Arrange
        command = DummyCommand(value="test")

        # Act
        await mediator_with_command.send(command)

        # Assert
        # Verificar que se loggeó el éxito
        calls = [str(call) for call in mock_logger.debug.call_args_list]
        assert any("Request handled successfully" in str(call) for call in calls)

    @pytest.mark.asyncio
    async def test_send_raises_handler_not_found_error_when_no_handler(
        self, mediator_with_empty_registry
    ):
        """Debería lanzar HandlerNotFoundError cuando no hay handler."""
        # Arrange
        command = DummyCommand(value="test")

        # Act & Assert
        with pytest.raises(HandlerNotFoundError) as exc_info:
            await mediator_with_empty_registry.send(command)

        assert "No handler registered for DummyCommand" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_logs_error_when_no_handler(
        self, mediator_with_empty_registry, mock_logger
    ):
        """Debería loggear error cuando no hay handler."""
        # Arrange
        command = DummyCommand(value="test")

        # Act
        try:
            await mediator_with_empty_registry.send(command)
        except HandlerNotFoundError:
            pass

        # Assert
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "No handler registered for request" in call_args[0]

    @pytest.mark.asyncio
    async def test_send_logs_error_when_handler_fails(
        self, handler_registry_with_command, mock_event_bus, mock_logger
    ):
        """Debería loggear error cuando el handler falla."""
        # Arrange
        # Modificar el handler para que falle
        failing_handler = Mock()
        failing_handler.handle = AsyncMock(side_effect=ValueError("Handler error"))
        failing_handler.__class__.__name__ = "FailingHandler"
        handler_registry_with_command[DummyCommand] = failing_handler

        mediator = Mediator(
            handler_registry=handler_registry_with_command,
            event_bus=mock_event_bus,
            logger=mock_logger,
        )
        command = DummyCommand(value="test")

        # Act & Assert
        with pytest.raises(ValueError):
            await mediator.send(command)

        # Verificar que se loggeó el error
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "Error handling request" in call_args[0]


class TestMediatorSendQuery:
    """Tests para envío de queries."""

    @pytest.mark.asyncio
    async def test_send_resolves_registered_query(self, mediator_with_query):
        """Debería resolver y ejecutar un query registrado."""
        # Arrange
        query = DummyQuery(id="123")

        # Act
        result = await mediator_with_query.send(query)

        # Assert
        assert result["id"] == "123"
        assert result["data"] == "test data"

    @pytest.mark.asyncio
    async def test_send_logs_dispatch_for_query(self, mediator_with_query, mock_logger):
        """Debería loggear el dispatch del query."""
        # Arrange
        query = DummyQuery(id="123")

        # Act
        await mediator_with_query.send(query)

        # Assert
        # Verificar que se loggeó el dispatch
        calls = [str(call) for call in mock_logger.debug.call_args_list]
        assert any("Dispatching request" in str(call) for call in calls)


class TestMediatorPublish:
    """Tests para publicación de eventos."""

    @pytest.mark.asyncio
    async def test_publish_delegates_to_event_bus(
        self, mediator_with_empty_registry, mock_event_bus
    ):
        """Debería delegar la publicación al event bus."""
        # Arrange
        event = DummyEvent(name="test_event")

        # Act
        await mediator_with_empty_registry.publish(event)

        # Assert
        mock_event_bus.publish.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_publish_logs_event_dispatch(
        self, mediator_with_empty_registry, mock_logger
    ):
        """Debería loggear el dispatch del evento."""
        # Arrange
        event = DummyEvent(name="test_event")

        # Act
        await mediator_with_empty_registry.publish(event)

        # Assert
        # Verificar que se loggeó el dispatch
        calls = [str(call) for call in mock_logger.debug.call_args_list]
        assert any("Publishing event via Event Bus" in str(call) for call in calls)

    @pytest.mark.asyncio
    async def test_publish_logs_success(
        self, mediator_with_empty_registry, mock_logger
    ):
        """Debería loggear el éxito de la publicación."""
        # Arrange
        event = DummyEvent(name="test_event")

        # Act
        await mediator_with_empty_registry.publish(event)

        # Assert
        # Verificar que se loggeó el éxito
        calls = [str(call) for call in mock_logger.debug.call_args_list]
        assert any("Event published successfully" in str(call) for call in calls)

    @pytest.mark.asyncio
    async def test_publish_logs_error_when_event_bus_fails(
        self, mediator_with_empty_registry, mock_event_bus, mock_logger
    ):
        """Debería loggear error cuando el event bus falla."""
        # Arrange
        mock_event_bus.publish = AsyncMock(side_effect=RuntimeError("Event bus error"))
        event = DummyEvent(name="test_event")

        # Act & Assert
        with pytest.raises(RuntimeError):
            await mediator_with_empty_registry.publish(event)

        # Verificar que se loggeó el error
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "Error publishing event" in call_args[0]


class TestMediatorHandlerRegistry:
    """Tests para el handler registry."""

    @pytest.mark.asyncio
    async def test_mediator_can_handle_multiple_command_types(
        self, mock_event_bus, mock_logger
    ):
        """Debería poder manejar múltiples tipos de comandos."""
        # Arrange
        handler1 = DummyCommandHandler()
        handler2 = DummyQueryHandler()
        registry = {DummyCommand: handler1, DummyQuery: handler2}

        mediator = Mediator(
            handler_registry=registry, event_bus=mock_event_bus, logger=mock_logger
        )

        # Act
        result1 = await mediator.send(DummyCommand(value="test1"))
        result2 = await mediator.send(DummyQuery(id="123"))

        # Assert
        assert result1["success"] is True
        assert result2["id"] == "123"

    def test_handler_registry_is_mutable(
        self, empty_handler_registry, mock_event_bus, mock_logger
    ):
        """El handler registry debería ser mutable para permitir registro dinámico."""
        # Arrange
        mediator = Mediator(
            handler_registry=empty_handler_registry,
            event_bus=mock_event_bus,
            logger=mock_logger,
        )

        # Act - Registrar handler dinámicamente
        handler = DummyCommandHandler()
        mediator._handler_registry[DummyCommand] = handler

        # Assert
        assert DummyCommand in mediator._handler_registry
        assert mediator._handler_registry[DummyCommand] == handler


class TestMediatorErrorHandling:
    """Tests para manejo de errores del Mediator."""

    @pytest.mark.asyncio
    async def test_handler_not_found_error_includes_descriptive_message(
        self, mediator_with_empty_registry
    ):
        """Debería lanzar HandlerNotFoundError con mensaje descriptivo."""
        # Arrange
        command = DummyCommand(value="test")

        # Act & Assert
        with pytest.raises(HandlerNotFoundError) as exc_info:
            await mediator_with_empty_registry.send(command)

        # Verificar que el mensaje incluye el nombre del comando
        error_message = str(exc_info.value)
        assert "No handler registered for DummyCommand" in error_message
        assert "Available handlers:" in error_message

    @pytest.mark.asyncio
    async def test_handler_not_found_error_logs_command_without_handler(
        self, mediator_with_empty_registry, mock_logger
    ):
        """Debería loggear el comando sin handler."""
        # Arrange
        command = DummyCommand(value="test")

        # Act
        try:
            await mediator_with_empty_registry.send(command)
        except HandlerNotFoundError:
            pass

        # Assert
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args

        # Verificar que se loggeó el mensaje correcto
        assert "No handler registered for request" in call_args[0]

        # Verificar que se loggeó el tipo de request
        assert call_args[1]["request_type"] == "DummyCommand"

    @pytest.mark.asyncio
    async def test_handler_not_found_error_includes_available_handlers_list(
        self, handler_registry_with_command, mock_event_bus, mock_logger
    ):
        """Debería incluir lista de handlers disponibles en el error."""
        # Arrange
        mediator = Mediator(
            handler_registry=handler_registry_with_command,
            event_bus=mock_event_bus,
            logger=mock_logger,
        )
        # Intentar enviar un comando no registrado
        query = DummyQuery(id="123")

        # Act & Assert
        with pytest.raises(HandlerNotFoundError) as exc_info:
            await mediator.send(query)

        # Verificar que el mensaje incluye la lista de handlers disponibles
        error_message = str(exc_info.value)
        assert "Available handlers:" in error_message
        # Verificar que menciona el handler que SÍ está registrado
        assert "DummyCommand" in error_message

    @pytest.mark.asyncio
    async def test_handler_not_found_error_logs_available_handlers(
        self, handler_registry_with_command, mock_event_bus, mock_logger
    ):
        """Debería loggear la lista de handlers disponibles."""
        # Arrange
        mediator = Mediator(
            handler_registry=handler_registry_with_command,
            event_bus=mock_event_bus,
            logger=mock_logger,
        )
        query = DummyQuery(id="123")

        # Act
        try:
            await mediator.send(query)
        except HandlerNotFoundError:
            pass

        # Assert
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args

        # Verificar que se loggeó la lista de handlers disponibles
        assert "available_handlers" in call_args[1]
        available_handlers = call_args[1]["available_handlers"]

        # Verificar que la lista contiene el handler registrado
        assert len(available_handlers) == 1
        assert "DummyCommand" in available_handlers[0]

    @pytest.mark.asyncio
    async def test_handler_not_found_error_with_empty_registry_shows_empty_list(
        self, mediator_with_empty_registry, mock_logger
    ):
        """Debería mostrar lista vacía cuando no hay handlers registrados."""
        # Arrange
        command = DummyCommand(value="test")

        # Act
        try:
            await mediator_with_empty_registry.send(command)
        except HandlerNotFoundError:
            pass

        # Assert
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args

        # Verificar que la lista de handlers disponibles está vacía
        assert "available_handlers" in call_args[1]
        available_handlers = call_args[1]["available_handlers"]
        assert len(available_handlers) == 0

    @pytest.mark.asyncio
    async def test_handler_not_found_error_with_multiple_handlers_lists_all(
        self, mock_event_bus, mock_logger
    ):
        """Debería listar todos los handlers disponibles cuando hay múltiples."""
        # Arrange
        handler1 = DummyCommandHandler()
        handler2 = DummyQueryHandler()
        registry = {DummyCommand: handler1, DummyQuery: handler2}

        mediator = Mediator(
            handler_registry=registry, event_bus=mock_event_bus, logger=mock_logger
        )

        # Crear un comando no registrado
        class UnregisteredCommand:
            pass

        unregistered = UnregisteredCommand()

        # Act
        try:
            await mediator.send(unregistered)
        except HandlerNotFoundError:
            pass

        # Assert
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args

        # Verificar que se loggearon todos los handlers disponibles
        assert "available_handlers" in call_args[1]
        available_handlers = call_args[1]["available_handlers"]
        assert len(available_handlers) == 2
        assert "DummyCommand" in available_handlers[0]
        assert "DummyQuery" in available_handlers[1]
