"""JWT Authentication Service with Refresh Token Rotation."""

from datetime import datetime, timedelta
from typing import Dict, Tuple
import secrets
from jose import JWTError, jwt

from wcag_backend.utils.config import Config
from wcag_backend.utils.security import hash_token
from wcag_backend.utils.exceptions import TokenExpiredError, TokenInvalidError


class AuthService:
    """Handle JWT creation, validation, and refresh token rotation."""

    def __init__(self, config: Config):
        """
        Initialize auth service.

        Args:
            config: Configuration object
        """
        self.config = config
        self.algorithm = "HS256"

    def create_access_token(self, user_id: str) -> str:
        """
        Create JWT access token.

        Args:
            user_id: User ID to encode in token

        Returns:
            JWT access token string
        """
        expires_delta = timedelta(seconds=self.config.security.jwt_access_expiry)
        expire = datetime.utcnow() + expires_delta

        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }

        return jwt.encode(
            payload,
            self.config.security.jwt_secret,
            algorithm=self.algorithm
        )

    def create_refresh_token(self) -> Tuple[str, str, datetime]:
        """
        Create refresh token (random secure string).

        Returns:
            Tuple of (token, token_hash, expires_at)
        """
        token = secrets.token_urlsafe(32)
        token_hash_value = hash_token(token)
        expires_at = datetime.utcnow() + timedelta(
            seconds=self.config.security.jwt_refresh_expiry
        )

        return token, token_hash_value, expires_at

    def validate_access_token(self, token: str) -> str:
        """
        Validate and decode JWT access token.

        Args:
            token: JWT token string

        Returns:
            User ID from token

        Raises:
            TokenExpiredError: If token has expired
            TokenInvalidError: If token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.config.security.jwt_secret,
                algorithms=[self.algorithm]
            )

            user_id: str = payload.get("sub")
            token_type: str = payload.get("type")

            if user_id is None or token_type != "access":
                raise TokenInvalidError("Invalid token payload")

            return user_id

        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Access token has expired")
        except JWTError as e:
            raise TokenInvalidError(f"Invalid token: {str(e)}")

    def create_token_pair(self, user_id: str) -> Tuple[str, str, str, datetime]:
        """
        Create access token + refresh token pair.

        Args:
            user_id: User ID

        Returns:
            Tuple of (access_token, refresh_token, refresh_token_hash, refresh_expires_at)
        """
        access_token = self.create_access_token(user_id)
        refresh_token, refresh_hash, expires_at = self.create_refresh_token()

        return access_token, refresh_token, refresh_hash, expires_at
