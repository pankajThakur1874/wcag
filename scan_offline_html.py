"""
Manual HTML Scanner for Protected Websites

This script scans locally saved HTML files, bypassing bot protection.

Usage:
1. Open Air India in your browser
2. Complete CAPTCHA, accept cookies, interact with page
3. Save page: Right-click → Save As → "Webpage, Complete"
4. Run: python scan_offline_html.py path/to/saved_page.html
"""

import asyncio
import sys
import json
from pathlib import Path
from src.core import ResultsAggregator
from src.models import ScanResult
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def scan_local_html(html_path: str, output_path: str = None):
    """
    Scan a locally saved HTML file.
    
    Args:
        html_path: Path to saved HTML file
        output_path: Optional output path for report
    """
    html_file = Path(html_path)
    
    if not html_file.exists():
        print(f"❌ Error: File not found: {html_path}")
        return None
    
    if not html_file.suffix in ['.html', '.htm']:
        print(f"⚠️  Warning: File doesn't appear to be HTML: {html_path}")
    
    print(f"╔════════════════════════════════════════════════════════════╗")
    print(f"║  Offline HTML Scanner                                      ║")
    print(f"╚════════════════════════════════════════════════════════════╝")
    print(f"")
    print(f"📄 File: {html_file.name}")
    print(f"📁 Path: {html_file.parent}")
    print(f"📊 Size: {html_file.stat().st_size / 1024:.1f} KB")
    print(f"")
    print(f"🔍 Starting scan with all 14 scanners...")
    print(f"")
    
    # Convert to file:// URL
    file_url = html_file.absolute().as_uri()
    
    try:
        # Scan with all scanners
        aggregator = ResultsAggregator(tools=None)  # None = all scanners
        result = await aggregator.scan(file_url)
        
        # Print summary
        print(f"")
        print(f"{'='*70}")
        print(f"SCAN COMPLETE")
        print(f"{'='*70}")
        print(f"Overall Score: {result.scores.overall}%")
        print(f"Total Violations: {result.summary.total_violations}")
        print(f"")
        print(f"Violations by Impact:")
        print(f"  🔴 Critical: {result.summary.critical}")
        print(f"  🟠 Serious:  {result.summary.serious}")
        print(f"  🟡 Moderate: {result.summary.moderate}")
        print(f"  🔵 Minor:    {result.summary.minor}")
        print(f"")
        print(f"Tests:")
        print(f"  ✅ Passed: {result.scores.total_rules_passed}/{result.scores.total_rules_checked}")
        print(f"  ❌ Failed: {result.scores.total_rules_failed}")
        print(f"")
        
        # Show scanners used
        print(f"Scanners executed:")
        for tool_name, tool_result in result.tools.items():
            status = "✅" if tool_result.status == "success" else "❌"
            print(f"  {status} {tool_name}: {tool_result.duration}ms")
        print(f"")
        
        # Save report
        if output_path is None:
            output_path = html_file.stem + "_wcag_report.html"
        
        from src.core import ReportGenerator
        generator = ReportGenerator()
        
        # Save HTML report
        html_report = generator.to_html(result)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        # Save JSON report
        json_path = output_path.replace('.html', '.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2, default=str)
        
        print(f"📊 Reports saved:")
        print(f"   - {output_path} (HTML report)")
        print(f"   - {json_path} (JSON data)")
        print(f"")
        print(f"Open report: open {output_path}")
        
        return result
        
    except Exception as e:
        print(f"")
        print(f"❌ Error during scan: {e}")
        logger.error(f"Scan failed: {e}", exc_info=True)
        return None


async def scan_multiple_html_files(html_dir: str):
    """
    Scan all HTML files in a directory.
    
    Args:
        html_dir: Directory containing saved HTML files
    """
    dir_path = Path(html_dir)
    
    if not dir_path.exists():
        print(f"❌ Error: Directory not found: {html_dir}")
        return
    
    html_files = list(dir_path.glob('*.html')) + list(dir_path.glob('*.htm'))
    
    if not html_files:
        print(f"❌ No HTML files found in: {html_dir}")
        return
    
    print(f"")
    print(f"Found {len(html_files)} HTML files")
    print(f"")
    
    results = []
    for i, html_file in enumerate(html_files, 1):
        print(f"[{i}/{len(html_files)}] Scanning {html_file.name}...")
        result = await scan_local_html(str(html_file))
        if result:
            results.append({
                'file': html_file.name,
                'score': result.scores.overall,
                'violations': result.summary.total_violations
            })
        print(f"")
    
    # Summary
    if results:
        print(f"")
        print(f"{'='*70}")
        print(f"BATCH SCAN SUMMARY")
        print(f"{'='*70}")
        avg_score = sum(r['score'] for r in results) / len(results)
        total_violations = sum(r['violations'] for r in results)
        print(f"Files scanned: {len(results)}")
        print(f"Average score: {avg_score:.1f}%")
        print(f"Total violations: {total_violations}")
        print(f"")
        print(f"Results by file:")
        for r in sorted(results, key=lambda x: x['score']):
            print(f"  {r['file']}: {r['score']}% ({r['violations']} issues)")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Scan single file:")
        print("    python scan_offline_html.py path/to/file.html")
        print("")
        print("  Scan all files in directory:")
        print("    python scan_offline_html.py path/to/directory/")
        print("")
        print("Example:")
        print("  python scan_offline_html.py ~/Downloads/airindia.html")
        sys.exit(1)
    
    path = sys.argv[1]
    path_obj = Path(path)
    
    if path_obj.is_file():
        # Scan single file
        asyncio.run(scan_local_html(path))
    elif path_obj.is_dir():
        # Scan directory
        asyncio.run(scan_multiple_html_files(path))
    else:
        print(f"❌ Error: Not a valid file or directory: {path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
