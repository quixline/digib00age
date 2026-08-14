"""
start_server.py — dev-convenience wrapper around backend.cli.main().

Run from the project root:
    python start_server.py

Also the source `digib00age-server` (pyproject.toml [project.scripts])
gets installed from — see src/backend/cli.py for the real implementation.
"""

import os
import sys

# Make backend importable as a package — it lives under src/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from backend.cli import main

if __name__ == "__main__":
    main()
