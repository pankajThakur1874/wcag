"""Page repository for database operations."""

from typing import List, Optional, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from scanner_v2.utils.logger import get_logger
from scanner_v2.utils.helpers import utc_now, is_valid_object_id
from scanner_v2.utils.exceptions import PageNotFoundException, InvalidInputError
from scanner_v2.database.models import ScannedPage, RawScanResults, to_mongo_dict

logger = get_logger("page_repo")


class PageRepository:
    """Repository for scanned page operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize page repository.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.collection = db.scanned_pages

    async def create(self, page: ScannedPage) -> ScannedPage:
        """
        Create a new scanned page.

        Args:
            page: Scanned page to create

        Returns:
            Created page with ID
        """
        doc = to_mongo_dict(page)
        doc["created_at"] = utc_now()

        result = await self.collection.insert_one(doc)
        page.id = str(result.inserted_id)

        logger.debug(f"Created scanned page: {page.id} - {page.url}")

        return page

    async def create_many(self, pages: List[ScannedPage]) -> List[str]:
        """
        Create multiple scanned pages.

        Args:
            pages: List of pages to create

        Returns:
            List of created page IDs
        """
        if not pages:
            return []

        docs = []
        for page in pages:
            doc = to_mongo_dict(page)
            doc["created_at"] = utc_now()
            docs.append(doc)

        result = await self.collection.insert_many(docs)

        page_ids = [str(id) for id in result.inserted_ids]

        logger.info(f"Created {len(page_ids)} scanned pages")

        return page_ids

    async def get_by_id(self, page_id: str) -> ScannedPage:
        """
        Get page by ID.

        Args:
            page_id: Page ID

        Returns:
            Scanned page

        Raises:
            PageNotFoundException: If page not found
        """
        if not is_valid_object_id(page_id):
            raise InvalidInputError(f"Invalid page ID: {page_id}")

        doc = await self.collection.find_one({"_id": ObjectId(page_id)})

        if not doc:
            raise PageNotFoundException(page_id)

        return self._doc_to_page(doc)

    async def get_by_scan(
        self,
        scan_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[ScannedPage], int]:
        """
        Get pages by scan ID.

        Args:
            scan_id: Scan ID
            skip: Number to skip
            limit: Maximum to return

        Returns:
            Tuple of (pages list, total count)
        """
        # Get total count
        total = await self.collection.count_documents({"scan_id": scan_id})

        # Get pages
        cursor = self.collection.find({"scan_id": scan_id}).skip(skip).limit(limit)

        pages = []
        async for doc in cursor:
            pages.append(self._doc_to_page(doc))

        logger.debug(f"Found {len(pages)} pages for scan {scan_id}")

        return pages, total

    async def get_by_url(self, scan_id: str, url: str) -> Optional[ScannedPage]:
        """
        Get page by scan ID and URL.

        Args:
            scan_id: Scan ID
            url: Page URL

        Returns:
            Scanned page or None
        """
        doc = await self.collection.find_one({"scan_id": scan_id, "url": url})

        if not doc:
            return None

        return self._doc_to_page(doc)

    async def delete_by_scan(self, scan_id: str) -> int:
        """
        Delete all pages for a scan.

        Args:
            scan_id: Scan ID

        Returns:
            Number of deleted pages
        """
        result = await self.collection.delete_many({"scan_id": scan_id})

        logger.info(f"Deleted {result.deleted_count} pages for scan {scan_id}")

        return result.deleted_count

    def _doc_to_page(self, doc: Dict) -> ScannedPage:
        """
        Convert MongoDB document to ScannedPage.

        Args:
            doc: MongoDB document

        Returns:
            ScannedPage instance
        """
        doc["_id"] = str(doc["_id"])

        # Convert nested models
        if "raw_results" in doc and isinstance(doc["raw_results"], dict):
            doc["raw_results"] = RawScanResults(**doc["raw_results"])

        return ScannedPage(**doc)
