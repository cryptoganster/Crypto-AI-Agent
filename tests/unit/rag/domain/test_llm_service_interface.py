"""Tests para ILLMService interface."""

from typing import Optional

import pytest

from src.rag.domain.interfaces import ILLMService


class TestILLMServiceInterface:
    """Tests para verificar que ILLMService está correctamente definida."""

    def test_interface_exists(self):
        """Debería poder importar ILLMService."""
        assert ILLMService is not None

    def test_interface_has_generate_method(self):
        """Debería tener método generate."""
        assert hasattr(ILLMService, "generate")

    def test_mock_implementation_satisfies_interface(self):
        """Un mock que implementa los métodos debería satisfacer la interface."""

        class MockLLMService:
            """Mock implementation para testing."""

            async def generate(
                self,
                prompt: str,
                max_tokens: int = 500,
                temperature: float = 0.7,
                system_prompt: Optional[str] = None,
            ) -> str:
                """Mock generate method."""
                return f"Generated text for: {prompt[:50]}"

        # Verificar que el mock satisface la interface
        mock: ILLMService = MockLLMService()
        assert mock is not None

    @pytest.mark.asyncio
    async def test_mock_generate_returns_string(self):
        """El método generate debería retornar string."""

        class MockLLMService:
            async def generate(
                self,
                prompt: str,
                max_tokens: int = 500,
                temperature: float = 0.7,
                system_prompt: Optional[str] = None,
            ) -> str:
                return "Generated text"

        mock: ILLMService = MockLLMService()
        result = await mock.generate("Test prompt")

        assert isinstance(result, str)
        assert result == "Generated text"

    @pytest.mark.asyncio
    async def test_mock_generate_accepts_all_parameters(self):
        """El método generate debería aceptar todos los parámetros."""

        class MockLLMService:
            async def generate(
                self,
                prompt: str,
                max_tokens: int = 500,
                temperature: float = 0.7,
                system_prompt: Optional[str] = None,
            ) -> str:
                return f"prompt={prompt}, max_tokens={max_tokens}, temp={temperature}, system={system_prompt}"

        mock: ILLMService = MockLLMService()

        # Test con todos los parámetros
        result = await mock.generate(
            prompt="Test prompt",
            max_tokens=200,
            temperature=0.3,
            system_prompt="You are a helpful assistant",
        )

        assert "Test prompt" in result
        assert "200" in result
        assert "0.3" in result
        assert "You are a helpful assistant" in result

    @pytest.mark.asyncio
    async def test_mock_generate_with_defaults(self):
        """El método generate debería funcionar con valores por defecto."""

        class MockLLMService:
            async def generate(
                self,
                prompt: str,
                max_tokens: int = 500,
                temperature: float = 0.7,
                system_prompt: Optional[str] = None,
            ) -> str:
                return f"Generated with defaults: {prompt}"

        mock: ILLMService = MockLLMService()

        # Test solo con prompt (otros parámetros usan defaults)
        result = await mock.generate("Test prompt")

        assert isinstance(result, str)
        assert "Test prompt" in result
