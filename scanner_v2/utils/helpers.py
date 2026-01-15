"""Helper utility functions for WCAG Scanner V2."""

import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlparse, urljoin
from bson import ObjectId


def generate_id() -> str:
    """
    Generate a new MongoDB ObjectId.

    Returns:
        String representation of ObjectId
    """
    return str(ObjectId())


def is_valid_object_id(id_str: str) -> bool:
    """
    Check if string is a valid MongoDB ObjectId.

    Args:
        id_str: String to check

    Returns:
        True if valid ObjectId, False otherwise
    """
    try:
        ObjectId(id_str)
        return True
    except Exception:
        return False


def utc_now() -> datetime:
    """
    Get current UTC datetime.

    Returns:
        Current UTC datetime
    """
    return datetime.now(timezone.utc)


def format_timestamp(dt: datetime) -> str:
    """
    Format datetime to ISO 8601 string.

    Args:
        dt: Datetime object

    Returns:
        ISO 8601 formatted string
    """
    return dt.isoformat()


def parse_timestamp(timestamp_str: str) -> datetime:
    """
    Parse ISO 8601 timestamp string to datetime.

    Args:
        timestamp_str: ISO 8601 timestamp string

    Returns:
        Datetime object
    """
    return datetime.fromisoformat(timestamp_str)


def normalize_url(url: str, base_url: Optional[str] = None) -> str:
    """
    Normalize URL by removing fragments and ensuring consistent format.

    Args:
        url: URL to normalize
        base_url: Base URL for relative URLs

    Returns:
        Normalized URL
    """
    # Handle relative URLs
    if base_url and not url.startswith(("http://", "https://")):
        url = urljoin(base_url, url)

    # Parse URL
    parsed = urlparse(url)

    # Rebuild without fragment
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    # Add query string if present
    if parsed.query:
        normalized += f"?{parsed.query}"

    # Remove trailing slash for consistency (except root)
    if normalized.endswith("/") and normalized.count("/") > 3:
        normalized = normalized[:-1]

    return normalized


def is_same_domain(url1: str, url2: str) -> bool:
    """
    Check if two URLs are from the same domain.

    Args:
        url1: First URL
        url2: Second URL

    Returns:
        True if same domain, False otherwise
    """
    domain1 = urlparse(url1).netloc
    domain2 = urlparse(url2).netloc
    return domain1 == domain2


def is_valid_url(url: str) -> bool:
    """
    Check if URL is valid.

    Args:
        url: URL to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def hash_string(text: str) -> str:
    """
    Generate SHA-256 hash of string.

    Args:
        text: Text to hash

    Returns:
        Hex digest of hash
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_dict(data: dict) -> str:
    """
    Generate hash of dictionary (for deduplication).

    Args:
        data: Dictionary to hash

    Returns:
        Hex digest of hash
    """
    import orjson

    # Sort keys for consistent hashing
    json_str = orjson.dumps(data, option=orjson.OPT_SORT_KEYS)
    return hashlib.sha256(json_str).hexdigest()


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.

    Args:
        filename: Filename to sanitize

    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)

    # Remove leading/trailing spaces and dots
    filename = filename.strip(". ")

    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        name = name[:250]
        filename = f"{name}.{ext}" if ext else name

    return filename


def calculate_duration_ms(start_time: datetime, end_time: Optional[datetime] = None) -> int:
    """
    Calculate duration in milliseconds between two timestamps.

    Args:
        start_time: Start timestamp
        end_time: End timestamp (defaults to now)

    Returns:
        Duration in milliseconds
    """
    if end_time is None:
        end_time = utc_now()

    duration = end_time - start_time
    return int(duration.total_seconds() * 1000)


def bytes_to_kb(bytes_size: int) -> float:
    """
    Convert bytes to kilobytes.

    Args:
        bytes_size: Size in bytes

    Returns:
        Size in KB
    """
    return round(bytes_size / 1024, 2)


def deep_merge_dicts(dict1: dict, dict2: dict) -> dict:
    """
    Deep merge two dictionaries.

    Args:
        dict1: First dictionary
        dict2: Second dictionary

    Returns:
        Merged dictionary
    """
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def extract_domain(url: str) -> str:
    """
    Extract domain from URL.

    Args:
        url: URL

    Returns:
        Domain name
    """
    return urlparse(url).netloc


def is_absolute_url(url: str) -> bool:
    """
    Check if URL is absolute.

    Args:
        url: URL to check

    Returns:
        True if absolute, False otherwise
    """
    return bool(urlparse(url).netloc)


def make_serializable(obj: Any) -> Any:
    """
    Make object JSON serializable by converting special types.

    Args:
        obj: Object to make serializable

    Returns:
        Serializable version of object
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_serializable(item) for item in obj]
    else:
        return obj
