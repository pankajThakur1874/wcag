"""Refresh token repository for database operations."""

from typing import Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from wcag_backend.database.models import RefreshToken, to_mongo_dict
from wcag_backend.utils.exceptions import (
    RefreshTokenNotFoundException,
    TokenExpiredError,
    TokenInvalidError
)


class RefreshTokenRepository:
    """Repository for RefreshToken collection operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize refresh token repository.

        Args:
            db: MongoDB database instance
        """
        self.collection = db.refresh_tokens

    async def create_token(
        self,
        user_id: str,
        token_hash: str,
        expires_at: datetime
    ) -> RefreshToken:
        """
        Create a new refresh token.

        Args:
            user_id: User ID
            token_hash: SHA256 hash of the token
            expires_at: Expiration datetime

        Returns:
            Created RefreshToken object
        """
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )

        # Insert into database
        token_dict = to_mongo_dict(token)
        result = await self.collection.insert_one(token_dict)

        # Update token with generated ID
        token.id = str(result.inserted_id)

        return token

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken:
        """
        Get refresh token by its hash.

        Args:
            token_hash: SHA256 hash of the token

        Returns:
            RefreshToken object

        Raises:
            TokenInvalidError: If token not found
            TokenExpiredError: If token has expired or been revoked
        """
        doc = await self.collection.find_one({"token_hash": token_hash})

        if not doc:
            raise TokenInvalidError("Invalid refresh token")

        # Convert MongoDB document to RefreshToken model
        doc["_id"] = str(doc["_id"])
        token = RefreshToken(**doc)

        # Check if token has been revoked
        if token.revoked:
            raise TokenExpiredError("Refresh token has been revoked")

        # Check if token has expired
        if token.expires_at < datetime.utcnow():
            raise TokenExpiredError("Refresh token has expired")

        return token

    async def revoke_token(self, token_id: str, replaced_by: Optional[str] = None) -> None:
        """
        Revoke a refresh token.

        Args:
            token_id: Token ID to revoke
            replaced_by: Optional ID of the new token that replaced this one

        Raises:
            RefreshTokenNotFoundException: If token not found
        """
        update_data = {
            "revoked": True,
            "updated_at": datetime.utcnow()
        }

        if replaced_by:
            update_data["replaced_by"] = replaced_by

        result = await self.collection.update_one(
            {"_id": ObjectId(token_id)},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            raise RefreshTokenNotFoundException(token_id)

    async def revoke_all_user_tokens(self, user_id: str) -> None:
        """
        Revoke all refresh tokens for a user.

        Args:
            user_id: User ID
        """
        await self.collection.update_many(
            {"user_id": user_id, "revoked": False},
            {"$set": {"revoked": True, "updated_at": datetime.utcnow()}}
        )

    async def cleanup_expired(self) -> int:
        """
        Delete expired tokens from database.
        Note: MongoDB TTL index will handle this automatically,
        but this method can be used for manual cleanup.

        Returns:
            Number of tokens deleted
        """
        result = await self.collection.delete_many({
            "expires_at": {"$lt": datetime.utcnow()}
        })

        return result.deleted_count
