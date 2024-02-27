import platform
import sys
import multiprocessing
import colorama
from importlib.metadata import version

if not sys.version_info >= (3, 11, 0):
    sys.exit(f"Python 3.11.0 or later required, found {platform.python_version()}")


# Fix non-deterministic new process strategy behaviour between platforms
# multiprocessing.set_start_method("fork")

# Fix Windows terminal colors globally
colorama.just_fix_windows_console()

# Global package variables
__version__ = version("dorothy")
