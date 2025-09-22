"""
Security functions for API authentication and domain validation
"""

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from .config import Settings

settings = Settings()
security = HTTPBearer(auto_error=False)


async def verify_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> bool:
    """
    Verify API key authentication

    Args:
        credentials: Bearer authentication credentials

    Returns:
        bool: True if authentication successful

    Raises:
        HTTPException: If authentication fails
    """
    print("credentials", credentials)
    print("Settings API Key:", settings.api_key)
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.credentials != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return True


def verify_origin_domain(origin: str) -> bool:
    """
    Verify origin domain against whitelist

    Args:
        origin: Request origin domain

    Returns:
        bool: True if domain is allowed
    """
    if not origin:
        return False

    # Allow all origins in development environment
    if settings.environment == "development":
        return True

    # Check if origin is in whitelist
    return origin in settings.allowed_origins


class SecurityMiddleware:
    """Security middleware for request validation"""

    @staticmethod
    def check_request_security(origin: Optional[str] = None) -> bool:
        """
        Check request security constraints

        Args:
            origin: Request origin

        Returns:
            bool: True if security check passes
        """
        # Verify origin in production environment
        if settings.environment == "production" and origin:
            if not verify_origin_domain(origin):
                return False

        return True
