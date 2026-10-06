"""Entry point for python -m a11ycc."""

import sys
from .cli import cli_main

if __name__ == "__main__":
    sys.exit(cli_main())
