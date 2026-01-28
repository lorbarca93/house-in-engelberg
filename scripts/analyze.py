#!/usr/bin/env python
"""
Entry point script for running Engelberg property investment analyses.

This is a thin wrapper around engelberg.analysis that handles path resolution
and provides the CLI interface.
"""

import os
import sys

# Add project root to path so we can import engelberg package
# Note: We calculate this manually here because we need it before importing engelberg
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from engelberg.analysis import main

if __name__ == "__main__":
    main()
