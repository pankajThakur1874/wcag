"""User repository for database operations."""

from typing import Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from wcag_backend.database.models import User, to_mongo_dict
from wcag_backend.utils.security import hash_password, verify_password
from wcag_backend.utils.exceptions import (
    UserNotFoundException,
    EmailAlreadyExistsError,
    InvalidCredentialsError
)


class UserRepository:
    """Repository for User collection operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize user repository.

        Args:
            db: MongoDB database instance
        """
        self.collection = db.users

    async def create(self, name: str, email: str, password: str) -> User:
        """
        Create a new user.

        Args:
            name: User's full name
            email: User's email address
            password: Plain text password (will be hashed)

        Returns:
            Created User object

        Raises:
            EmailAlreadyExistsError: If email already exists
        """
        # Check if email already exists
        existing = await self.collection.find_one({"email": email})
        if existing:
            raise EmailAlreadyExistsError(email)

        # Create user document
        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password)
        )

        # Insert into database
        user_dict = to_mongo_dict(user)
        result = await self.collection.insert_one(user_dict)

        # Update user with generated ID
        user.id = str(result.inserted_id)

        return user

    async def get_by_id(self, user_id: str) -> User:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User object

        Raises:
            UserNotFoundException: If user not found
        """
        try:
            doc = await self.collection.find_one({"_id": ObjectId(user_id)})
        except Exception:
            raise UserNotFoundException(user_id)

        if not doc:
            raise UserNotFoundException(user_id)

        # Convert MongoDB document to User model
        doc["_id"] = str(doc["_id"])
        return User(**doc)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.

        Args:
            email: User's email address

        Returns:
            User object if found, None otherwise
        """
        doc = await self.collection.find_one({"email": email})

        if not doc:
            return None

        # Convert MongoDB document to User model
        doc["_id"] = str(doc["_id"])
        return User(**doc)

    async def authenticate(self, email: str, password: str) -> User:
        """
        Authenticate user with email and password.

        Args:
            email: User's email
            password: Plain text password

        Returns:
            User object if authentication successful

        Raises:
            InvalidCredentialsError: If email or password is incorrect
        """
        user = await self.get_by_email(email)

        if not user:
            raise InvalidCredentialsError("Invalid email or password")

        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")

        return user

    async def update(self, user_id: str, **updates) -> User:
        """
        Update user fields.

        Args:
            user_id: User ID
            **updates: Fields to update

        Returns:
            Updated User object

        Raises:
            UserNotFoundException: If user not found
        """
        updates["updated_at"] = datetime.utcnow()

        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": updates}
        )

        if result.matched_count == 0:
            raise UserNotFoundException(user_id)

        return await self.get_by_id(user_id)
