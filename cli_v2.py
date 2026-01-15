#!/usr/bin/env python3
"""Entry point for WCAG Scanner V2 CLI."""

import sys
from pathlib import Path

# Add scanner_v2 to path
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    from scanner_v2.cli.main import cli
    cli()
