from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from app.models.database import ApiKeyConfig
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

class SettingsRepository:
    """Repository for managing API key configurations."""

    def __init__(self, db: Session):
        self.db = db

    def save_api_key(self, tenant_id: str, provider: str, encrypted_key: str) -> None:
        """Save encrypted API key to database.

        Args:
            tenant_id: Tenant UUID
            provider: Provider name (openai, anthropic, etc.)
            encrypted_key: Encrypted API key
        """
        try:
            # Delete existing key for this provider
            self.db.execute(
                delete(ApiKeyConfig).where(
                    ApiKeyConfig.tenant_id == UUID(tenant_id),
                    ApiKeyConfig.provider == provider
                )
            )

            # Insert new key
            config = ApiKeyConfig(
                tenant_id=UUID(tenant_id),
                provider=provider,
                encrypted_key=encrypted_key
            )
            self.db.add(config)
            self.db.commit()
            logger.info(f"Saved API key for tenant {tenant_id}, provider {provider}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save API key: {e}")
            raise

    def get_api_key_config(self, tenant_id: str, provider: str = "openai") -> ApiKeyConfig:
        """Get API key configuration for tenant.

        Args:
            tenant_id: Tenant UUID
            provider: Provider name (defaults to openai)

        Returns:
            ApiKeyConfig or None if not found
        """
        try:
            result = self.db.execute(
                select(ApiKeyConfig).where(
                    ApiKeyConfig.tenant_id == UUID(tenant_id),
                    ApiKeyConfig.provider == provider
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get API key config: {e}")
            return None

    def delete_api_key(self, tenant_id: str, provider: str) -> None:
        """Delete API key for tenant.

        Args:
            tenant_id: Tenant UUID
            provider: Provider name
        """
        try:
            self.db.execute(
                delete(ApiKeyConfig).where(
                    ApiKeyConfig.tenant_id == UUID(tenant_id),
                    ApiKeyConfig.provider == provider
                )
            )
            self.db.commit()
            logger.info(f"Deleted API key for tenant {tenant_id}, provider {provider}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete API key: {e}")
            raise
