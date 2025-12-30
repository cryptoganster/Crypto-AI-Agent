"""
Property-based tests for Mediator command resolution.

**Feature: refactor-scheduling-jobs, Property 1: Mediator resolves registered commands**
**Validates: Requirements 1.3**
"""

from dataclasses import dataclass
from unittest.mock import AsyncMock, Mock

import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.shared.infra.mediator import Mediator


def create_test_mediator():
    """Helper to create a Mediator instance for testing."""
    handler_registry = {}
    event_bus = Mock()
    logger = Mock()
    logger.bind = Mock(return_value=logger)
    logger.debug = Mock()
    logger.error = Mock()
    return Mediator(handler_registry, event_bus, logger)


# Test command types
@dataclass
class TestCommand:
    """Test command for property testing."""

    value: str


@dataclass
class AnotherTestCommand:
    """Another test command for property testing."""

    number: int


@dataclass
class YetAnotherTestCommand:
    """Yet another test command for property testing."""

    flag: bool


# Strategies for generating commands
test_commands = st.builds(TestCommand, value=st.text(min_size=1, max_size=50))

another_test_commands = st.builds(
    AnotherTestCommand, number=st.integers(min_value=0, max_value=1000)
)

yet_another_test_commands = st.builds(YetAnotherTestCommand, flag=st.booleans())


class TestMediatorResolutionProperty:
    """Property-based tests for Mediator command resolution."""

    @pytest.mark.asyncio
    @given(command=test_commands)
    async def test_mediator_resolves_any_registered_command(self, command):
        """
        Property: For any command type that is registered with a handler,
        the mediator should successfully resolve and execute that handler.

        **Validates: Requirements 1.3**
        """
        # Arrange
        mediator = create_test_mediator()

        # Create a mock handler
        mock_handler = AsyncMock()
        expected_result = f"Handled: {command.value}"
        mock_handler.handle = AsyncMock(return_value=expected_result)

        # Register the handler
        mediator._handler_registry[TestCommand] = mock_handler

        # Act
        result = await mediator.send(command)

        # Assert
        assert result == expected_result
        mock_handler.handle.assert_called_once_with(command)

    @pytest.mark.asyncio
    @given(
        command1=test_commands,
        command2=another_test_commands,
        command3=yet_another_test_commands,
    )
    async def test_mediator_resolves_multiple_registered_commands(
        self, command1, command2, command3
    ):
        """
        Property: For any set of different command types that are registered,
        the mediator should correctly resolve each to its corresponding handler.

        **Validates: Requirements 1.3**
        """
        # Arrange
        mediator = create_test_mediator()

        # Create mock handlers for each command type
        handler1 = AsyncMock()
        handler1.handle = AsyncMock(return_value=f"Result1: {command1.value}")

        handler2 = AsyncMock()
        handler2.handle = AsyncMock(return_value=f"Result2: {command2.number}")

        handler3 = AsyncMock()
        handler3.handle = AsyncMock(return_value=f"Result3: {command3.flag}")

        # Register all handlers
        mediator._handler_registry[TestCommand] = handler1
        mediator._handler_registry[AnotherTestCommand] = handler2
        mediator._handler_registry[YetAnotherTestCommand] = handler3

        # Act
        result1 = await mediator.send(command1)
        result2 = await mediator.send(command2)
        result3 = await mediator.send(command3)

        # Assert - Each command resolves to its correct handler
        assert result1 == f"Result1: {command1.value}"
        assert result2 == f"Result2: {command2.number}"
        assert result3 == f"Result3: {command3.flag}"

        handler1.handle.assert_called_once_with(command1)
        handler2.handle.assert_called_once_with(command2)
        handler3.handle.assert_called_once_with(command3)

    @pytest.mark.asyncio
    @given(command=test_commands)
    async def test_mediator_resolution_is_consistent(self, command):
        """
        Property: For any command, resolving it multiple times should
        always use the same handler (consistency).

        **Validates: Requirements 1.3**
        """
        # Arrange
        mediator = create_test_mediator()

        mock_handler = AsyncMock()
        call_count = 0

        async def counting_handler(cmd):
            nonlocal call_count
            call_count += 1
            return f"Call {call_count}: {cmd.value}"

        mock_handler.handle = counting_handler
        mediator._handler_registry[TestCommand] = mock_handler

        # Act - Send the same command multiple times
        result1 = await mediator.send(command)
        result2 = await mediator.send(command)
        result3 = await mediator.send(command)

        # Assert - All calls went to the same handler
        assert call_count == 3
        assert "Call 1:" in result1
        assert "Call 2:" in result2
        assert "Call 3:" in result3

    @pytest.mark.asyncio
    @given(commands=st.lists(test_commands, min_size=1, max_size=10))
    async def test_mediator_handles_command_sequence(self, commands):
        """
        Property: For any sequence of commands of the same type,
        the mediator should resolve each one correctly in order.

        **Validates: Requirements 1.3**
        """
        # Arrange
        mediator = create_test_mediator()

        handled_commands = []

        async def tracking_handler(cmd):
            handled_commands.append(cmd)
            return f"Handled: {cmd.value}"

        mock_handler = AsyncMock()
        mock_handler.handle = tracking_handler
        mediator._handler_registry[TestCommand] = mock_handler

        # Act - Send all commands in sequence
        results = []
        for command in commands:
            result = await mediator.send(command)
            results.append(result)

        # Assert - All commands were handled in order
        assert len(handled_commands) == len(commands)
        assert handled_commands == commands
        assert len(results) == len(commands)

        for i, (command, result) in enumerate(zip(commands, results)):
            assert result == f"Handled: {command.value}"

    @pytest.mark.asyncio
    @given(command=test_commands)
    async def test_unregistered_command_raises_error(self, command):
        """
        Property: For any command that is NOT registered,
        the mediator should raise an appropriate error.

        **Validates: Requirements 1.3**
        """
        # Arrange
        mediator = create_test_mediator()
        # Deliberately NOT registering any handler

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await mediator.send(command)

        # Verify error message mentions the command type
        assert (
            "TestCommand" in str(exc_info.value)
            or "handler" in str(exc_info.value).lower()
        )

    @pytest.mark.asyncio
    @given(
        command=test_commands, num_registrations=st.integers(min_value=1, max_value=5)
    )
    async def test_last_registered_handler_wins(self, command, num_registrations):
        """
        Property: If a command type is registered multiple times,
        the last registered handler should be used.

        **Validates: Requirements 1.3**
        """
        # Arrange
        mediator = create_test_mediator()

        # Register multiple handlers for the same command type
        handlers = []
        for i in range(num_registrations):
            handler = AsyncMock()
            handler.handle = AsyncMock(return_value=f"Handler {i}")
            handlers.append(handler)
            mediator._handler_registry[TestCommand] = handler

        # Act
        result = await mediator.send(command)

        # Assert - Only the last handler should have been called
        assert result == f"Handler {num_registrations - 1}"

        # Only the last handler was called
        handlers[-1].handle.assert_called_once_with(command)

        # Earlier handlers were not called
        for handler in handlers[:-1]:
            handler.handle.assert_not_called()
