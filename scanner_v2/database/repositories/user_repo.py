"""User repository for database operations."""

from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from passlib.context import CryptContext

from scanner_v2.utils.logger import get_logger
from scanner_v2.utils.helpers import utc_now, is_valid_object_id
from scanner_v2.utils.exceptions import InvalidInputError, InvalidCredentialsError
from scanner_v2.database.models import User, UserRole, to_mongo_dict

logger = get_logger("user_repo")


class UserRepository:
    """Repository for user operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize user repository.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.collection = db.users
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async def create(
        self,
        email: str,
        password: str,
        name: Optional[str] = None,
        role: UserRole = UserRole.USER
    ) -> User:
        """
        Create a new user.

        Args:
            email: User email
            password: Plain text password
            name: Optional name
            role: User role

        Returns:
            Created user
        """
        # Hash password
        password_hash = self.pwd_context.hash(password)

        user = User(
            email=email,
            password_hash=password_hash,
            name=name,
            role=role,
            created_at=utc_now(),
            updated_at=utc_now()
        )

        doc = to_mongo_dict(user)

        result = await self.collection.insert_one(doc)
        user.id = str(result.inserted_id)

        logger.info(f"Created user: {user.id} - {email}")

        return user

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User or None
        """
        if not is_valid_object_id(user_id):
            raise InvalidInputError(f"Invalid user ID: {user_id}")

        doc = await self.collection.find_one({"_id": ObjectId(user_id)})

        if not doc:
            return None

        return self._doc_to_user(doc)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.

        Args:
            email: User email

        Returns:
            User or None
        """
        doc = await self.collection.find_one({"email": email})

        if not doc:
            return None

        return self._doc_to_user(doc)

    async def authenticate(self, email: str, password: str) -> User:
        """
        Authenticate user with email and password.

        Args:
            email: User email
            password: Plain text password

        Returns:
            Authenticated user

        Raises:
            InvalidCredentialsError: If credentials are invalid
        """
        user = await self.get_by_email(email)

        if not user:
            raise InvalidCredentialsError("Invalid email or password")

        # Verify password
        if not self.pwd_context.verify(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")

        logger.info(f"User authenticated: {user.id} - {email}")

        return user

    async def update(self, user_id: str, **updates) -> Optional[User]:
        """
        Update user.

        Args:
            user_id: User ID
            **updates: Fields to update

        Returns:
            Updated user or None
        """
        if not is_valid_object_id(user_id):
            raise InvalidInputError(f"Invalid user ID: {user_id}")

        updates["updated_at"] = utc_now()

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": updates},
            return_document=True
        )

        if not result:
            return None

        logger.info(f"Updated user: {user_id}")

        return self._doc_to_user(result)

    async def change_password(self, user_id: str, new_password: str) -> bool:
        """
        Change user password.

        Args:
            user_id: User ID
            new_password: New plain text password

        Returns:
            True if successful
        """
        if not is_valid_object_id(user_id):
            raise InvalidInputError(f"Invalid user ID: {user_id}")

        password_hash = self.pwd_context.hash(new_password)

        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"password_hash": password_hash, "updated_at": utc_now()}}
        )

        if result.modified_count > 0:
            logger.info(f"Changed password for user: {user_id}")
            return True

        return False

    async def delete(self, user_id: str) -> bool:
        """
        Delete user.

        Args:
            user_id: User ID

        Returns:
            True if deleted
        """
        if not is_valid_object_id(user_id):
            raise InvalidInputError(f"Invalid user ID: {user_id}")

        result = await self.collection.delete_one({"_id": ObjectId(user_id)})

        if result.deleted_count > 0:
            logger.info(f"Deleted user: {user_id}")
            return True

        return False

    def _doc_to_user(self, doc: dict) -> User:
        """
        Convert MongoDB document to User.

        Args:
            doc: MongoDB document

        Returns:
            User instance
        """
        doc["_id"] = str(doc["_id"])

        # Convert role enum
        if "role" in doc and isinstance(doc["role"], str):
            doc["role"] = UserRole(doc["role"])

        return User(**doc)
