"""Security utilities for password hashing and token generation."""

import hashlib
import secrets
from passlib.context import CryptContext


# Password hashing context (using bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    For passwords longer than 72 bytes, pre-hash with SHA256.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    # Bcrypt has a 72-byte limit, so pre-hash long passwords
    if len(password.encode('utf-8')) > 72:
        password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    For passwords longer than 72 bytes, pre-hash with SHA256.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    # Bcrypt has a 72-byte limit, so pre-hash long passwords
    if len(plain_password.encode('utf-8')) > 72:
        plain_password = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    return pwd_context.verify(plain_password, hashed_password)


def generate_refresh_token() -> str:
    """
    Generate a secure random refresh token.

    Returns:
        Random token string (hex)
    """
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """
    Hash a token using SHA256 for storage.

    Args:
        token: Token to hash

    Returns:
        SHA256 hash of token (hex)
    """
    return hashlib.sha256(token.encode()).hexdigest()
