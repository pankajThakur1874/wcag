"""
HTML Fetcher - Downloads and saves HTML from pages before scanning.

This two-phase approach:
1. Phase 1: Fetch and save HTML from all pages
2. Phase 2: Scan the saved HTML files offline

Benefits:
- Bypasses bot protection (save manually if needed)
- Allows retry without re-fetching
- Works offline after initial download
- Perfect for Air India and protected sites
"""

import asyncio
import httpx
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict
from urllib.parse import urlparse

from src.utils.browser import BrowserManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class HTMLFetcher:
    """Fetches and saves HTML from URLs with adaptive anti-bot strategies."""

    def __init__(self, output_dir: Optional[str] = None, max_retries: int = 3):
        """
        Initialize HTML fetcher.

        Args:
            output_dir: Directory to save HTML files (default: ./html_cache)
            max_retries: Maximum retry attempts per URL (default: 3)
        """
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_dir = Path(f"html_cache_{timestamp}")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_retries = max_retries
        logger.info(f"HTML will be saved to: {self.output_dir}")
    
    def _url_to_filename(self, url: str) -> str:
        """Convert URL to a safe filename."""
        parsed = urlparse(url)
        
        # Use path or "index" for homepage
        path = parsed.path.strip('/').replace('/', '_') or 'index'
        
        # Add query params if present
        if parsed.query:
            query_part = parsed.query[:50].replace('&', '_').replace('=', '-')
            path = f"{path}_{query_part}"
        
        # Clean filename
        safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in path)
        
        return f"{safe_name}.html"
    
    async def _fetch_with_browser(self, url: str, browser_manager: BrowserManager, attempt: int = 1) -> str:
        """
        Fetch HTML using browser with adaptive retry.

        Args:
            url: URL to fetch
            browser_manager: Browser manager instance
            attempt: Current attempt number

        Returns:
            HTML content as string

        Raises:
            Exception if all strategies fail
        """
        strategies = [
            ("Browser automation (standard)", {}),
            ("Browser automation (extra delay)", {"extra_delay": 5}),
            ("Browser automation (max stealth)", {"extra_delay": 10}),
        ]

        for strategy_name, options in strategies:
            try:
                logger.info(f"  Strategy: {strategy_name} (attempt {attempt})")

                # Add extra delay if specified
                if options.get("extra_delay"):
                    logger.info(f"  Adding {options['extra_delay']}s delay for anti-bot evasion...")
                    await asyncio.sleep(options["extra_delay"])

                html = await browser_manager.get_page_content(url)

                # Verify we got actual content (not just error page)
                if len(html) > 1000:  # Reasonable minimum for a real page
                    logger.info(f"  ✅ Success with {strategy_name}")
                    return html
                else:
                    logger.warning(f"  ⚠️ Content too small ({len(html)} bytes), trying next strategy")

            except Exception as e:
                logger.warning(f"  ❌ {strategy_name} failed: {str(e)[:100]}")
                continue

        raise Exception(f"All browser strategies failed for {url}")

    async def fetch_and_save(self, url: str, use_browser: bool = True, browser_manager: Optional[BrowserManager] = None) -> Optional[str]:
        """
        Fetch HTML from URL and save to file with smart retry logic.

        Args:
            url: URL to fetch
            use_browser: Use browser automation (handles JS) vs simple HTTP (faster)
            browser_manager: Reusable browser manager instance (optional)

        Returns:
            Path to saved HTML file, or None if failed
        """
        filename = self._url_to_filename(url)
        filepath = self.output_dir / filename

        logger.info(f"📥 Fetching: {url}")

        for attempt in range(1, self.max_retries + 1):
            try:
                if use_browser:
                    # Use browser automation (handles JS and bot protection)
                    if browser_manager:
                        html = await self._fetch_with_browser(url, browser_manager, attempt)
                    else:
                        # Create temporary browser
                        browser = BrowserManager()
                        await browser.start()
                        try:
                            html = await self._fetch_with_browser(url, browser, attempt)
                        finally:
                            await browser.stop()
                else:
                    # Try simple HTTP first (fast but no JS)
                    logger.info(f"  Trying HTTP fetch (attempt {attempt})...")
                    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                        response = await client.get(url, headers={
                            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                            "Accept-Language": "en-US,en;q=0.9",
                        })
                        response.raise_for_status()
                        html = response.text

                # Validate content
                if len(html) < 500:
                    logger.warning(f"  ⚠️ Content seems too small ({len(html)} bytes)")
                    if attempt < self.max_retries:
                        logger.info(f"  Retrying in 2 seconds...")
                        await asyncio.sleep(2)
                        continue

                # Save to file
                filepath.write_text(html, encoding='utf-8')
                logger.info(f"✅ Saved: {filepath} ({len(html):,} bytes)")

                return str(filepath)

            except Exception as e:
                logger.error(f"❌ Attempt {attempt} failed: {str(e)[:100]}")
                if attempt < self.max_retries:
                    wait_time = attempt * 3  # Progressive backoff: 3s, 6s, 9s
                    logger.info(f"  Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"❌ All {self.max_retries} attempts failed for {url}")

        return None
    
    async def fetch_multiple(
        self,
        urls: List[str],
        use_browser: bool = True,
        max_concurrent: int = 1,
        auto_detect: bool = True
    ) -> Dict[str, Optional[str]]:
        """
        Fetch HTML from multiple URLs with smart adaptation.

        Args:
            urls: List of URLs to fetch
            use_browser: Use browser automation (recommended for all sites)
            max_concurrent: Maximum concurrent fetches (1 for browser mode)
            auto_detect: Automatically detect if site needs browser (True recommended)

        Returns:
            Dict mapping URL to saved filepath (or None if failed)
        """
        results = {}

        print(f"\n{'='*70}")
        print(f"  Fetching HTML from {len(urls)} URL(s)")
        print(f"{'='*70}\n")

        if use_browser:
            # Create single browser instance for all fetches
            logger.info(f"🌐 Starting browser for {len(urls)} URLs...")
            print(f"🌐 Starting browser (this may take a moment)...\n")

            browser = BrowserManager()
            await browser.start()

            try:
                # Fetch sequentially to avoid browser conflicts and reduce detection
                for i, url in enumerate(urls, 1):
                    print(f"[{i}/{len(urls)}] {url}")
                    print(f"{'─'*70}")

                    try:
                        result = await self.fetch_and_save(url, use_browser=True, browser_manager=browser)
                        results[url] = result

                        if result:
                            print(f"✅ Success!\n")
                        else:
                            print(f"❌ Failed (see logs for details)\n")

                    except Exception as e:
                        logger.error(f"Error fetching {url}: {e}")
                        results[url] = None
                        print(f"❌ Error: {str(e)[:100]}\n")

                    # Delay between fetches (important for bot protection)
                    if i < len(urls):
                        delay = 3
                        print(f"⏳ Waiting {delay}s before next URL...\n")
                        await asyncio.sleep(delay)

            finally:
                await browser.stop()
                logger.info("Browser stopped")
                print(f"🛑 Browser closed\n")

        else:
            # HTTP mode - try simple fetch first, fall back to browser if needed
            print(f"📡 Using HTTP mode (fast but limited JavaScript support)\n")

            for i, url in enumerate(urls, 1):
                print(f"[{i}/{len(urls)}] {url}")
                print(f"{'─'*70}")

                try:
                    result = await self.fetch_and_save(url, use_browser=False)

                    # If HTTP fails and auto-detect is on, try browser
                    if not result and auto_detect:
                        print(f"  ⚠️ HTTP failed, trying browser automation...")
                        browser = BrowserManager()
                        await browser.start()
                        try:
                            result = await self.fetch_and_save(url, use_browser=True, browser_manager=browser)
                        finally:
                            await browser.stop()

                    results[url] = result

                    if result:
                        print(f"✅ Success!\n")
                    else:
                        print(f"❌ Failed\n")

                except Exception as e:
                    logger.error(f"Error fetching {url}: {e}")
                    results[url] = None
                    print(f"❌ Error: {str(e)[:100]}\n")

        # Summary
        successful = sum(1 for v in results.values() if v is not None)
        failed = len(urls) - successful

        print(f"{'='*70}")
        print(f"  FETCH SUMMARY")
        print(f"{'='*70}")
        print(f"✅ Successful: {successful}/{len(urls)}")
        if failed > 0:
            print(f"❌ Failed: {failed}")
        print(f"{'='*70}\n")

        logger.info(f"Fetch complete: {successful}/{len(urls)} successful")

        return results
    
    def get_saved_files(self) -> List[Path]:
        """Get list of all saved HTML files."""
        return list(self.output_dir.glob('*.html'))
    
    def get_metadata(self) -> Dict:
        """Get metadata about saved files."""
        files = self.get_saved_files()
        total_size = sum(f.stat().st_size for f in files)
        
        return {
            'output_dir': str(self.output_dir),
            'total_files': len(files),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'files': [
                {
                    'name': f.name,
                    'size_bytes': f.stat().st_size,
                    'modified': datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                }
                for f in files
            ]
        }


async def fetch_html_batch(urls: List[str], output_dir: Optional[str] = None) -> Dict[str, Optional[str]]:
    """
    Convenience function to fetch HTML from multiple URLs.
    
    Args:
        urls: List of URLs to fetch
        output_dir: Directory to save files
    
    Returns:
        Dict mapping URL to saved filepath
    """
    fetcher = HTMLFetcher(output_dir=output_dir)
    results = await fetcher.fetch_multiple(urls, use_browser=True)
    
    # Print summary
    metadata = fetcher.get_metadata()
    print(f"\n✅ Fetched {metadata['total_files']} files")
    print(f"📁 Saved to: {metadata['output_dir']}")
    print(f"💾 Total size: {metadata['total_size_mb']} MB")
    
    return results
