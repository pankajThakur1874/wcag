"""
Two-Phase Site Scanner - Fetch HTML first, then scan offline

Perfect for protected websites like Air India:
1. Phase 1: Fetch and save HTML from all pages
2. Phase 2: Scan the saved HTML files offline

Usage:
    python scan_fetch_first.py --urls url1 url2 url3
    python scan_fetch_first.py --sitemap https://example.com/sitemap.xml
    python scan_fetch_first.py --file urls.txt
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import List

from src.core.html_fetcher import HTMLFetcher
from src.core import ResultsAggregator
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def scan_with_fetch_first(
    urls: List[str],
    output_dir: str = None,
    scanners: List[str] = None,
    skip_fetch: bool = False
):
    """
    Two-phase scanning: fetch HTML first, then scan offline.
    
    Args:
        urls: List of URLs to scan
        output_dir: Directory to save HTML files
        scanners: List of scanners to use (None = all)
        skip_fetch: Skip fetching, just scan existing HTML files
    """
    
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  Two-Phase WCAG Scanner: Fetch First, Scan Offline        ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    # Phase 1: Fetch HTML
    if not skip_fetch:
        print("📥 PHASE 1: Fetching HTML from URLs...")
        print("─" * 70)
        
        fetcher = HTMLFetcher(output_dir=output_dir)
        
        print(f"URLs to fetch: {len(urls)}")
        print(f"Output directory: {fetcher.output_dir}")
        print()
        
        results = await fetcher.fetch_multiple(urls, use_browser=True, max_concurrent=2)
        
        successful_files = [path for path in results.values() if path is not None]
        failed_count = len(urls) - len(successful_files)
        
        print()
        print(f"✅ Successfully fetched: {len(successful_files)}/{len(urls)}")
        if failed_count > 0:
            print(f"❌ Failed: {failed_count}")
            print("   (You can manually save these pages and add to the folder)")
        
        metadata = fetcher.get_metadata()
        print(f"💾 Total size: {metadata['total_size_mb']} MB")
        print()
        
        html_dir = fetcher.output_dir
    else:
        print("⏭️  Skipping fetch phase (using existing HTML files)")
        html_dir = Path(output_dir) if output_dir else Path("html_cache")
    
    # Phase 2: Scan saved HTML files
    print()
    print("🔍 PHASE 2: Scanning saved HTML files...")
    print("─" * 70)
    
    html_files = list(html_dir.glob('*.html'))
    
    if not html_files:
        print("❌ No HTML files found to scan!")
        print(f"   Directory: {html_dir}")
        return
    
    print(f"HTML files to scan: {len(html_files)}")
    print(f"Scanners: {', '.join(scanners) if scanners else 'All (15 scanners)'}")
    print()
    
    results = []
    aggregator = ResultsAggregator(tools=scanners)
    
    for i, html_file in enumerate(html_files, 1):
        print(f"[{i}/{len(html_files)}] Scanning: {html_file.name}")
        
        # Convert to file:// URL
        file_url = html_file.absolute().as_uri()
        
        try:
            result = await aggregator.scan(file_url)
            results.append({
                'file': html_file.name,
                'url': file_url,
                'score': result.scores.overall,
                'violations': result.summary.total_violations,
                'result': result
            })
            
            print(f"   Score: {result.scores.overall}% | Violations: {result.summary.total_violations}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            logger.error(f"Scan failed for {html_file}: {e}")
    
    # Summary
    print()
    print("=" * 70)
    print("SCAN COMPLETE")
    print("=" * 70)
    
    if results:
        avg_score = sum(r['score'] for r in results) / len(results)
        total_violations = sum(r['violations'] for r in results)
        
        print(f"Files scanned: {len(results)}")
        print(f"Average score: {avg_score:.1f}%")
        print(f"Total violations: {total_violations}")
        print()
        
        # Show worst pages
        worst = sorted(results, key=lambda x: x['score'])[:5]
        print("Pages with lowest scores:")
        for r in worst:
            print(f"  {r['file']}: {r['score']}% ({r['violations']} issues)")
        
        # Save aggregate report
        report_file = html_dir / "aggregate_report.json"
        import json
        with open(report_file, 'w') as f:
            json.dump({
                'summary': {
                    'total_files': len(results),
                    'average_score': avg_score,
                    'total_violations': total_violations
                },
                'results': [
                    {
                        'file': r['file'],
                        'score': r['score'],
                        'violations': r['violations']
                    }
                    for r in results
                ]
            }, f, indent=2)
        
        print()
        print(f"📊 Aggregate report saved: {report_file}")
        print(f"📁 HTML files location: {html_dir}")


async def main():
    parser = argparse.ArgumentParser(
        description="Two-phase WCAG scanner: Fetch HTML first, then scan offline"
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--urls', nargs='+', help='List of URLs to fetch and scan')
    group.add_argument('--file', help='Text file with one URL per line')
    group.add_argument('--sitemap', help='URL to sitemap.xml')
    
    parser.add_argument('--output', '-o', help='Output directory for HTML files')
    parser.add_argument('--scanners', '-s', nargs='+', help='Scanners to use')
    parser.add_argument('--skip-fetch', action='store_true', help='Skip fetch, scan existing files')
    
    args = parser.parse_args()
    
    # Get URLs
    urls = []
    if args.urls:
        urls = args.urls
    elif args.file:
        with open(args.file) as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    elif args.sitemap:
        # Parse sitemap.xml
        import httpx
        import xml.etree.ElementTree as ET
        
        print(f"Fetching sitemap: {args.sitemap}")
        async with httpx.AsyncClient() as client:
            response = await client.get(args.sitemap)
            root = ET.fromstring(response.content)
            
        # Extract URLs from sitemap
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [elem.text for elem in root.findall('.//ns:loc', namespace)]
        
        print(f"Found {len(urls)} URLs in sitemap")
    
    if not urls and not args.skip_fetch:
        print("Error: No URLs provided!")
        parser.print_help()
        sys.exit(1)
    
    # Run scan
    await scan_with_fetch_first(
        urls=urls,
        output_dir=args.output,
        scanners=args.scanners,
        skip_fetch=args.skip_fetch
    )


if __name__ == "__main__":
    asyncio.run(main())
