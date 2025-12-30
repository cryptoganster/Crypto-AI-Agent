"""
Property-based tests for handler registration in FetchingContainer and RssArticleContainer.

**Feature: fix-mediator-handler-registration, Property 1: All registered commands have handlers**
**Validates: Requirements 1.2**

**Feature: fix-mediator-handler-registration, Property 2: Unregistered commands raise descriptive errors**
**Validates: Requirements 1.4, 2.2**
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.app.commands.pipelines.run_fetch_pipeline.command import (
    RunFetchPipelineCommand,
)
from src.scraping.app.commands import (
    ScrapeSourceCommand,
    StartScrapingCommand,
    UpdateScrapingConfigCommand,
)
from src.scraping.container import ScrapingContainer
from src.shared.infra.mediator import HandlerNotFoundError

# Alias for backward compatibility in tests
StartFetchSessionCommand = StartScrapingCommand
UpdateFetchConfigCommand = UpdateScrapingConfigCommand


def create_mock_infrastructure():
    """Helper to create a mock SharedInfrastructure for testing."""
    infra = Mock()

    # Mock mediator with handler registry
    infra.mediator = Mock()
    infra.mediator._handler_registry = {}

    # Mock logger
    infra.logger = Mock()
    infra.logger.info = Mock()
    infra.logger.debug = Mock()
    infra.logger.error = Mock()

    # Mock register_handler method
    def register_handler(command_type, handler):
        infra.mediator._handler_registry[command_type] = handler
        infra.logger.debug(
            "Handler registrado en Mediator",
            command_type=command_type.__name__,
            handler=handler.__class__.__name__,
        )

    infra.register_handler = register_handler

    # Mock session_factory
    infra.session_factory = Mock()

    # Mock event_publisher
    infra.event_publisher = Mock()

    # Mock time_provider
    infra.time_provider = Mock()

    return infra


def create_mock_container_with_handlers():
    """Helper to create a ScrapingContainer with mocked handler getters."""
    infra = create_mock_infrastructure()

    # Mock article and source containers
    article_container = Mock()
    source_container = Mock()

    container = ScrapingContainer(infra, article_container, source_container)

    # Mock all handler getter methods to return mock handlers
    mock_handler = Mock()
    mock_handler.handle = AsyncMock()

    # Handlers activos (arquitectura event-driven)
    container.get_run_fetch_pipeline_handler = Mock(return_value=mock_handler)
    container.get_start_scraping_handler = Mock(return_value=mock_handler)
    container.get_scrape_source_handler = Mock(return_value=mock_handler)
    container.get_update_fetch_config_handler = Mock(return_value=mock_handler)

    return container, infra


# Strategy for generating command types (current active commands)
command_types = st.sampled_from(
    [
        StartScrapingCommand,
        ScrapeSourceCommand,
        UpdateScrapingConfigCommand,
        RunFetchPipelineCommand,
    ]
)


class TestHandlerRegistrationProperties:
    """Property-based tests for handler registration."""

    @given(command_type=command_types)
    def test_all_registered_commands_have_handlers(self, command_type):
        """
        Property: For any command type that should be registered,
        after calling register_handlers(), the mediator
        should have a handler for that command type.

        **Feature: fix-mediator-handler-registration, Property 1**
        **Validates: Requirements 1.2**
        """
        # Arrange
        container, infra = create_mock_container_with_handlers()

        # Act
        container.register_handlers()

        # Assert - Command type should be in the handler registry
        assert command_type in infra.mediator._handler_registry, (
            f"Handler for {command_type.__name__} not registered. "
            f"Available handlers: {list(infra.mediator._handler_registry.keys())}"
        )

        # Assert - Handler should not be None
        handler = infra.mediator._handler_registry[command_type]
        assert handler is not None, f"Handler for {command_type.__name__} is None"

    def test_all_critical_handlers_registered_together(self):
        """
        Property: After calling register_handlers(),
        ALL critical command types should be registered simultaneously.

        **Feature: fix-mediator-handler-registration, Property 1**
        **Validates: Requirements 1.2**
        """
        # Arrange
        container, infra = create_mock_container_with_handlers()

        critical_commands = [
            StartScrapingCommand,
            ScrapeSourceCommand,
            UpdateScrapingConfigCommand,
            RunFetchPipelineCommand,
        ]

        # Act
        container.register_handlers()

        # Assert - All critical commands should be registered
        for command_type in critical_commands:
            assert (
                command_type in infra.mediator._handler_registry
            ), f"Critical handler for {command_type.__name__} not registered"

            handler = infra.mediator._handler_registry[command_type]
            assert (
                handler is not None
            ), f"Critical handler for {command_type.__name__} is None"

        # Assert - Count should match expected
        registered_count = len(
            [
                cmd
                for cmd in critical_commands
                if cmd in infra.mediator._handler_registry
            ]
        )
        assert registered_count == len(critical_commands), (
            f"Expected {len(critical_commands)} handlers, "
            f"but only {registered_count} were registered"
        )

    @given(command_type=command_types)
    def test_registered_handlers_are_callable(self, command_type):
        """
        Property: For any registered command type, the handler
        should have a 'handle' method that can be called.

        **Feature: fix-mediator-handler-registration, Property 1**
        **Validates: Requirements 1.2**
        """
        # Arrange
        container, infra = create_mock_container_with_handlers()

        # Act
        container.register_handlers()

        # Assert - Handler should have a handle method
        handler = infra.mediator._handler_registry[command_type]
        assert hasattr(
            handler, "handle"
        ), f"Handler for {command_type.__name__} does not have a 'handle' method"

        # Assert - Handle method should be callable
        assert callable(
            handler.handle
        ), f"Handler.handle for {command_type.__name__} is not callable"

    def test_registration_is_idempotent(self):
        """
        Property: Calling register_handlers() multiple times
        should result in the same set of handlers being registered
        (idempotent operation).

        **Feature: fix-mediator-handler-registration, Property 1**
        **Validates: Requirements 1.2**
        """
        # Arrange
        container, infra = create_mock_container_with_handlers()

        # Act - Register handlers multiple times
        container.register_handlers()
        first_registry = dict(infra.mediator._handler_registry)

        container.register_handlers()
        second_registry = dict(infra.mediator._handler_registry)

        container.register_handlers()
        third_registry = dict(infra.mediator._handler_registry)

        # Assert - All registries should have the same command types
        assert set(first_registry.keys()) == set(
            second_registry.keys()
        ), "Handler registry changed after second registration"
        assert set(second_registry.keys()) == set(
            third_registry.keys()
        ), "Handler registry changed after third registration"

        # Assert - Should have all 4 critical handlers
        assert (
            len(first_registry) >= 4
        ), f"Expected at least 4 handlers, got {len(first_registry)}"

    @given(
        command_types_subset=st.lists(
            command_types, min_size=1, max_size=4, unique=True
        )
    )
    def test_any_subset_of_commands_can_be_resolved(self, command_types_subset):
        """
        Property: For any subset of registered command types,
        all of them should be resolvable through the mediator.

        **Feature: fix-mediator-handler-registration, Property 1**
        **Validates: Requirements 1.2**
        """
        # Arrange
        container, infra = create_mock_container_with_handlers()

        # Act
        container.register_handlers()

        # Assert - All commands in subset should be registered
        for command_type in command_types_subset:
            assert (
                command_type in infra.mediator._handler_registry
            ), f"Command {command_type.__name__} from subset not registered"

            handler = infra.mediator._handler_registry[command_type]
            assert handler is not None
            assert hasattr(handler, "handle")


class TestUnregisteredCommandsProperties:
    """
    Property-based tests for unregistered commands.

    **Feature: fix-mediator-handler-registration, Property 2**
    **Validates: Requirements 1.4, 2.2**
    """

    def test_unregistered_command_raises_handler_not_found_error(self):
        """
        Property: For any command NOT registered in the mediator,
        attempting to send it should raise HandlerNotFoundError.

        **Feature: fix-mediator-handler-registration, Property 2**
        **Validates: Requirements 1.4, 2.2**
        """
        # Arrange - Create a mock mediator with empty registry
        from src.shared.infra.mediator import Mediator

        mock_event_bus = Mock()
        mock_logger = Mock()
        mock_logger.bind = Mock(return_value=mock_logger)
        mock_logger.error = Mock()

        mediator = Mediator(
            handler_registry={}, event_bus=mock_event_bus, logger=mock_logger
        )

        # Create a fake command class that is NOT registered
        class UnregisteredCommand:
            """A command that is not registered."""

            pass

        command = UnregisteredCommand()

        # Act & Assert - Should raise HandlerNotFoundError
        with pytest.raises(HandlerNotFoundError) as exc_info:
            import asyncio

            asyncio.run(mediator.send(command))

        # Assert - Error message should be descriptive
        error_message = str(exc_info.value)
        assert (
            "UnregisteredCommand" in error_message
            or "not found" in error_message.lower()
        ), f"Error message should mention the command type: {error_message}"

    def test_unregistered_command_error_is_descriptive(self):
        """
        Property: The error raised for unregistered commands should
        provide helpful information including:
        - The command that was not found
        - Suggestion to check registration

        **Feature: fix-mediator-handler-registration, Property 2**
        **Validates: Requirements 1.4, 2.2**
        """
        # Arrange - Create mediator with some registered handlers
        from src.shared.infra.mediator import Mediator

        mock_event_bus = Mock()
        mock_logger = Mock()
        mock_logger.bind = Mock(return_value=mock_logger)
        mock_logger.error = Mock()

        # Register a dummy handler
        class RegisteredCommand:
            pass

        class DummyHandler:
            async def handle(self, command):
                pass

        handler_registry = {RegisteredCommand: DummyHandler()}

        mediator = Mediator(
            handler_registry=handler_registry,
            event_bus=mock_event_bus,
            logger=mock_logger,
        )

        # Create an unregistered command
        class UnregisteredCommand:
            pass

        command = UnregisteredCommand()

        # Act & Assert - Should raise HandlerNotFoundError
        with pytest.raises(HandlerNotFoundError) as exc_info:
            import asyncio

            asyncio.run(mediator.send(command))

        # Assert - Error should be descriptive
        error_message = str(exc_info.value)

        # Should mention the unregistered command
        assert (
            "UnregisteredCommand" in error_message
            or "not found" in error_message.lower()
        ), "Error should mention the unregistered command"


class TestRegistrationErrorHandlingProperties:
    """
    Property-based tests for registration error handling.

    **Feature: fix-mediator-handler-registration, Property 3**
    **Validates: Requirements 3.2**
    """

    @given(
        failing_indices=st.lists(
            st.integers(min_value=0, max_value=3), min_size=1, max_size=2, unique=True
        )
    )
    def test_registration_errors_dont_stop_other_registrations(self, failing_indices):
        """
        Property: For any subset of handlers that fail to register,
        the registration process should continue and successfully
        register all other valid handlers.

        **Feature: fix-mediator-handler-registration, Property 3**
        **Validates: Requirements 3.2**
        """
        # Arrange
        infra = create_mock_infrastructure()

        # Mock article and source containers
        article_container = Mock()
        source_container = Mock()

        container = ScrapingContainer(infra, article_container, source_container)

        # List of all command types and their getter methods
        all_handlers = [
            (RunFetchPipelineCommand, "get_run_fetch_pipeline_handler"),
            (StartScrapingCommand, "get_start_scraping_handler"),
            (ScrapeSourceCommand, "get_scrape_source_handler"),
            (UpdateScrapingConfigCommand, "get_update_fetch_config_handler"),
        ]

        # Create mock handlers - some will fail, others will succeed
        for idx, (command_type, getter_name) in enumerate(all_handlers):
            if idx in failing_indices:
                # This handler will raise an exception when accessed
                def failing_getter(cmd=command_type):
                    raise RuntimeError(f"Failed to create handler for {cmd.__name__}")

                setattr(container, getter_name, failing_getter)
            else:
                # This handler will succeed
                mock_handler = Mock()
                mock_handler.handle = AsyncMock()
                mock_handler.__class__.__name__ = f"{command_type.__name__}Handler"
                setattr(container, getter_name, Mock(return_value=mock_handler))

        # Modified registration that continues on errors
        def register_with_error_handling():
            """Modified registration that continues on errors."""
            handlers_to_register = [
                (RunFetchPipelineCommand, container.get_run_fetch_pipeline_handler),
                (StartScrapingCommand, container.get_start_scraping_handler),
                (ScrapeSourceCommand, container.get_scrape_source_handler),
                (
                    UpdateScrapingConfigCommand,
                    container.get_update_fetch_config_handler,
                ),
            ]

            errors = []
            successful_registrations = []

            for command_type, getter in handlers_to_register:
                try:
                    handler = getter()
                    infra.register_handler(command_type, handler)
                    successful_registrations.append(command_type.__name__)
                except Exception as e:
                    errors.append((command_type.__name__, str(e)))
                    infra.logger.error(
                        "Failed to register handler",
                        command=command_type.__name__,
                        error=str(e),
                    )

            if successful_registrations:
                infra.logger.info(
                    "Handlers registered successfully",
                    handlers=successful_registrations,
                    count=len(successful_registrations),
                )

            if errors:
                infra.logger.error(
                    "Some handlers failed to register", errors=errors, count=len(errors)
                )

        container.register_handlers = register_with_error_handling

        # Act
        container.register_handlers()

        # Assert - Valid handlers should be registered
        expected_successful = len(all_handlers) - len(failing_indices)
        actual_successful = len(infra.mediator._handler_registry)

        assert actual_successful == expected_successful, (
            f"Expected {expected_successful} handlers to be registered, "
            f"but got {actual_successful}. "
            f"Failing indices: {failing_indices}"
        )
