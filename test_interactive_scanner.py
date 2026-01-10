"""
Test Interactive Element Scanner

This demonstrates scanning for interactive elements like:
- Tabs
- Accordions  
- Modals/Dialogs
- Dropdowns

The scanner automatically discovers and tests these elements.
"""

import asyncio
from src.core import ResultsAggregator

async def test_interactive_elements():
    """Test a website with interactive elements."""
    
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  Interactive Element Scanner Test                         ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print("")
    
    # Test with a site that has tabs, modals, accordions
    # Bootstrap documentation is a good test case
    test_urls = [
        "https://getbootstrap.com/docs/5.3/components/modal/",
        "https://getbootstrap.com/docs/5.3/components/accordion/",
        "https://www.britishairways.com/"  # Likely has interactive elements
    ]
    
    for url in test_urls:
        print(f"Testing: {url}")
        print("-" * 70)
        
        # Run scanner with interactive element detection
        aggregator = ResultsAggregator(tools=['interactive'])
        result = await aggregator.scan(url)
        
        # Show results
        print(f"Overall Score: {result.scores.overall}%")
        print(f"Interactive Issues Found: {result.summary.total_violations}")
        
        if result.violations:
            print(f"\nInteractive Element Violations:")
            for v in result.violations:
                print(f"  • [{v.impact.value.upper()}] {v.description}")
                print(f"    Help: {v.help_text}")
        else:
            print("\n✅ No interactive element issues found!")
        
        print("")
    
    print("="*70)
    print("Test complete!")


if __name__ == "__main__":
    asyncio.run(test_interactive_elements())
