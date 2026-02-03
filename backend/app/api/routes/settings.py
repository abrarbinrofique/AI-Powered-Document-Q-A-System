from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.schemas import ApiKeyRequest, ApiKeyStatus
from app.services.crypto_service import CryptoService
from app.services.api_key_validator import ApiKeyValidator
from app.repositories.settings_repository import SettingsRepository
from app.database import get_db_session, set_tenant_context
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])

def get_tenant_id():
    """Get tenant ID from request context.
    For simplicity, we're using a default tenant.
    In production, this would extract from JWT or session.
    """
    return "00000000-0000-0000-0000-000000000001"  # Default tenant from init.sql


@router.post("/api-keys/validate")
async def validate_api_key(
    request: ApiKeyRequest,
    db: Session = Depends(get_db_session)
):
    """Validate and store user's API key.

    Args:
        request: API key request with provider and key
        db: Database session

    Returns:
        Success response with validation status
    """
    try:
        tenant_id = get_tenant_id()
        set_tenant_context(db, tenant_id)

        # Validate the key with real API request
        validator = ApiKeyValidator()
        is_valid = await validator.validate(request.provider, request.api_key)

        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail="Invalid API key. Please check and try again."
            )

        # Encrypt and store
        crypto = CryptoService()
        encrypted_key = crypto.encrypt(request.api_key)

        repo = SettingsRepository(db)
        repo.save_api_key(
            tenant_id=tenant_id,
            provider=request.provider,
            encrypted_key=encrypted_key
        )

        logger.info(f"API key validated and saved for tenant {tenant_id}, provider {request.provider}")

        return {
            "success": True,
            "message": "API key validated and saved",
            "provider": request.provider
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate API key: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api-keys/status", response_model=ApiKeyStatus)
async def get_api_key_status(db: Session = Depends(get_db_session)):
    """Check if API keys are configured for the tenant.

    Args:
        db: Database session

    Returns:
        API key configuration status
    """
    try:
        tenant_id = get_tenant_id()
        set_tenant_context(db, tenant_id)

        repo = SettingsRepository(db)
        config = repo.get_api_key_config(tenant_id, "openai")

        if not config:
            return ApiKeyStatus(configured=False)

        # Mask the key for display (show last 4 chars)
        crypto = CryptoService()
        decrypted = crypto.decrypt(config.encrypted_key)
        masked = f"sk-...{decrypted[-4:]}"

        return ApiKeyStatus(
            configured=True,
            provider=config.provider,
            masked_key=masked
        )

    except Exception as e:
        logger.error(f"Failed to get API key status: {e}")
        return ApiKeyStatus(configured=False)


@router.delete("/api-keys/{provider}")
async def delete_api_key(
    provider: str,
    db: Session = Depends(get_db_session)
):
    """Delete stored API key for a provider.

    Args:
        provider: Provider name (openai, anthropic, etc.)
        db: Database session

    Returns:
        Success response
    """
    try:
        tenant_id = get_tenant_id()
        set_tenant_context(db, tenant_id)

        repo = SettingsRepository(db)
        repo.delete_api_key(tenant_id, provider)

        logger.info(f"Deleted API key for tenant {tenant_id}, provider {provider}")

        return {
            "success": True,
            "message": f"{provider} API key deleted"
        }

    except Exception as e:
        logger.error(f"Failed to delete API key: {e}")
        raise HTTPException(status_code=500, detail=str(e))
