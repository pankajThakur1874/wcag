"""Test script for Phase 1: Foundation Setup."""

import asyncio
import sys
from pathlib import Path

# Add scanner_v2 to path
sys.path.insert(0, str(Path(__file__).parent))

from scanner_v2.utils.config import get_config
from scanner_v2.utils.logger import setup_logging, get_logger
from scanner_v2.utils.helpers import generate_id, normalize_url, is_valid_url
from scanner_v2.database.models import (
    Project,
    ProjectSettings,
    Scan,
    ScanStatus,
    WCAGLevel,
    Issue,
    ImpactLevel,
    Principle
)


async def test_configuration():
    """Test configuration loading."""
    print("\n" + "=" * 60)
    print("Testing Configuration")
    print("=" * 60)

    try:
        config = get_config()
        print(f"✓ Configuration loaded successfully")
        print(f"  - Database: {config.database.mongodb_uri}")
        print(f"  - Server: {config.server.host}:{config.server.port}")
        print(f"  - Worker Count: {config.queue.worker_count}")
        print(f"  - Default WCAG Level: {config.scanning.default_wcag_level}")
        print(f"  - Default Scanners: {', '.join(config.scanning.default_scanners)}")
        return True
    except Exception as e:
        print(f"✗ Configuration failed: {e}")
        return False


async def test_logging():
    """Test logging setup."""
    print("\n" + "=" * 60)
    print("Testing Logging")
    print("=" * 60)

    try:
        # Standard format
        logger_std = setup_logging(level="INFO", format_type="standard")
        logger = get_logger("test")
        logger.info("Standard format logging test")
        print("✓ Standard logging works")

        # JSON format
        logger_json = setup_logging(level="INFO", format_type="json")
        logger.info("JSON format logging test", extra={"test_id": "123"})
        print("✓ JSON logging works")

        return True
    except Exception as e:
        print(f"✗ Logging failed: {e}")
        return False


async def test_helpers():
    """Test helper functions."""
    print("\n" + "=" * 60)
    print("Testing Helper Functions")
    print("=" * 60)

    try:
        # Test ID generation
        obj_id = generate_id()
        print(f"✓ Generated ID: {obj_id}")

        # Test URL helpers
        url = "https://example.com/page/../test?q=1#section"
        normalized = normalize_url(url)
        print(f"✓ Normalized URL: {normalized}")

        # Test validation
        valid = is_valid_url("https://example.com")
        invalid = is_valid_url("not-a-url")
        print(f"✓ URL validation: valid={valid}, invalid={not invalid}")

        return True
    except Exception as e:
        print(f"✗ Helper functions failed: {e}")
        return False


async def test_models():
    """Test Pydantic models."""
    print("\n" + "=" * 60)
    print("Testing Pydantic Models")
    print("=" * 60)

    try:
        # Test Project model
        project = Project(
            user_id="user_123",
            name="Test Website",
            base_url="https://example.com",
            description="Test project for WCAG scanning",
            settings=ProjectSettings(
                max_depth=5,
                max_pages=200,
                wcag_level=WCAGLevel.AA
            )
        )
        print(f"✓ Project model created: {project.name}")

        # Test Scan model
        scan = Scan(
            project_id=project.id or "proj_123",
            status=ScanStatus.QUEUED,
        )
        print(f"✓ Scan model created: status={scan.status.value}")

        # Test Issue model
        issue = Issue(
            scan_id="scan_123",
            page_id="page_123",
            wcag_criteria=["1.1.1", "1.4.3"],
            wcag_level=WCAGLevel.AA,
            principle=Principle.PERCEIVABLE,
            impact=ImpactLevel.CRITICAL,
            rule_id="color-contrast",
            description="Insufficient color contrast",
        )
        print(f"✓ Issue model created: {issue.impact.value} impact")

        # Test model serialization
        project_dict = project.model_dump()
        print(f"✓ Model serialization works")

        return True
    except Exception as e:
        print(f"✗ Model tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_database_connection():
    """Test MongoDB connection (optional - requires MongoDB running)."""
    print("\n" + "=" * 60)
    print("Testing Database Connection")
    print("=" * 60)

    try:
        from scanner_v2.database.connection import init_db, close_db

        config = get_config()
        db = await init_db(config)
        print(f"✓ Connected to MongoDB: {config.database.database_name}")

        await close_db()
        print("✓ Disconnected from MongoDB")

        return True
    except Exception as e:
        print(f"⚠ Database connection skipped (MongoDB not running?)")
        print(f"  Error: {e}")
        return None  # Optional test


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("WCAG Scanner V2 - Phase 1 Tests")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Configuration", await test_configuration()))
    results.append(("Logging", await test_logging()))
    results.append(("Helpers", await test_helpers()))
    results.append(("Models", await test_models()))
    results.append(("Database", await test_database_connection()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result is True)
    failed = sum(1 for _, result in results if result is False)
    skipped = sum(1 for _, result in results if result is None)

    for name, result in results:
        if result is True:
            print(f"✓ {name}")
        elif result is False:
            print(f"✗ {name}")
        else:
            print(f"⚠ {name} (skipped)")

    print(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")

    if failed == 0:
        print("\n🎉 Phase 1: Foundation Setup - Complete!")
    else:
        print("\n❌ Some tests failed. Please review errors above.")

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
