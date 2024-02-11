import platform
import sys
from multiprocessing import set_start_method

if not sys.version_info >= (3, 11, 0):
    sys.exit(f"Python 3.11.0 or later required, found {platform.python_version()}")

from importlib.metadata import version

# Global package variables
__version__ = version("dorothy")

import colorama

# Fix Windows terminal colors globally
colorama.just_fix_windows_console()
