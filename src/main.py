"""Main entry point for WCAG Scanner."""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cli import main

if __name__ == "__main__":
    main()
