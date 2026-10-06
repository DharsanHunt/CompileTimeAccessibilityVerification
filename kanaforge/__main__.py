"""Compatibility entry point pointing to a11ycc."""
import sys
from a11ycc.cli import cli_main

if __name__ == "__main__":
    sys.exit(cli_main())
