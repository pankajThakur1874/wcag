"""MongoDB connection management for WCAG Scanner V2."""

from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from scanner_v2.utils.config import Config
from scanner_v2.utils.logger import get_logger
from scanner_v2.utils.exceptions import DatabaseConnectionError

logger = get_logger("database")


class MongoDB:
    """MongoDB connection manager."""

    def __init__(self, config: Config):
        """
        Initialize MongoDB connection manager.

        Args:
            config: Configuration object
        """
        self.config = config
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self) -> None:
        """
        Connect to MongoDB.

        Raises:
            DatabaseConnectionError: If connection fails
        """
        try:
            logger.info(f"Connecting to MongoDB at {self.config.database.mongodb_uri}")

            self.client = AsyncIOMotorClient(
                self.config.database.mongodb_uri,
                serverSelectionTimeoutMS=5000,
            )

            # Verify connection
            await self.client.admin.command("ping")

            self.db = self.client[self.config.database.database_name]

            logger.info(f"Connected to MongoDB database: {self.config.database.database_name}")

            # Create indexes
            await self._create_indexes()

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise DatabaseConnectionError(
                "Failed to connect to MongoDB",
                {"uri": self.config.database.mongodb_uri, "error": str(e)}
            )

    async def disconnect(self) -> None:
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    async def _create_indexes(self) -> None:
        """Create database indexes."""
        logger.info("Creating database indexes...")

        # Users indexes
        await self.db.users.create_index("email", unique=True)

        # Projects indexes
        await self.db.projects.create_index("user_id")
        await self.db.projects.create_index([("created_at", -1)])

        # Scans indexes
        await self.db.scans.create_index([("project_id", 1), ("created_at", -1)])
        await self.db.scans.create_index("status")
        await self.db.scans.create_index([("created_at", -1)])

        # Scanned pages indexes
        await self.db.scanned_pages.create_index("scan_id")
        await self.db.scanned_pages.create_index("url")

        # Issues indexes
        await self.db.issues.create_index("scan_id")
        await self.db.issues.create_index("page_id")
        await self.db.issues.create_index("wcag_criteria")
        await self.db.issues.create_index("impact")
        await self.db.issues.create_index("status")

        logger.info("Database indexes created")

    def get_database(self) -> AsyncIOMotorDatabase:
        """
        Get database instance.

        Returns:
            AsyncIOMotorDatabase instance

        Raises:
            DatabaseConnectionError: If not connected
        """
        if self.db is None:
            raise DatabaseConnectionError("Not connected to MongoDB")
        return self.db


# Global MongoDB instance
_mongodb: Optional[MongoDB] = None


async def init_db(config: Config) -> MongoDB:
    """
    Initialize global MongoDB connection.

    Args:
        config: Configuration object

    Returns:
        MongoDB instance
    """
    global _mongodb
    _mongodb = MongoDB(config)
    await _mongodb.connect()
    return _mongodb


async def close_db() -> None:
    """Close global MongoDB connection."""
    global _mongodb
    if _mongodb:
        await _mongodb.disconnect()
        _mongodb = None


def get_db() -> AsyncIOMotorDatabase:
    """
    Get global database instance.

    Returns:
        AsyncIOMotorDatabase instance

    Raises:
        DatabaseConnectionError: If not initialized
    """
    if _mongodb is None:
        raise DatabaseConnectionError("Database not initialized")
    return _mongodb.get_database()
