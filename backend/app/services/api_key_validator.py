import logging
from typing import Optional

logger = logging.getLogger(__name__)

class ApiKeyValidator:
    """Validates API keys by making test requests to the provider."""

    async def validate(self, provider: str, api_key: str) -> bool:
        """Validate API key with real request to the provider.

        Args:
            provider: Provider name (openai, anthropic, cohere)
            api_key: API key to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            if provider == "openai":
                return await self._validate_openai(api_key)
            elif provider == "anthropic":
                return await self._validate_anthropic(api_key)
            else:
                logger.warning(f"Unknown provider: {provider}")
                return False
        except Exception as e:
            logger.error(f"API key validation failed for {provider}: {e}")
            return False

    async def _validate_openai(self, api_key: str) -> bool:
        """Test OpenAI API key with minimal embedding request.

        Args:
            api_key: OpenAI API key

        Returns:
            True if valid, False otherwise
        """
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)

            # Minimal test request
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input="test"
            )

            return len(response.data) > 0
        except Exception as e:
            logger.error(f"OpenAI validation error: {e}")
            return False

    async def _validate_anthropic(self, api_key: str) -> bool:
        """Test Anthropic API key with minimal request.

        Args:
            api_key: Anthropic API key

        Returns:
            True if valid, False otherwise
        """
        try:
            from anthropic import Anthropic

            client = Anthropic(api_key=api_key)

            # Minimal test request
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )

            return response.content is not None
        except Exception as e:
            logger.error(f"Anthropic validation error: {e}")
            return False
