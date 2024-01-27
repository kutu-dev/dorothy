import platform
import sys

if not sys.version_info >= (3, 11, 0):
    sys.exit(f"Python 3.11.0 or later required, found {platform.python_version()}")

from dataclasses import dataclass
from importlib.metadata import version

import colorama

# Global package variables
__version__ = version("dorothy")


@dataclass
class Colors:
    cyan = colorama.Fore.CYAN + colorama.Style.BRIGHT
    blue = colorama.Fore.BLUE + colorama.Style.BRIGHT
    green = colorama.Fore.GREEN + colorama.Style.BRIGHT
    yellow = colorama.Fore.YELLOW + colorama.Style.BRIGHT
    red = colorama.Fore.RED + colorama.Style.BRIGHT
    magenta = colorama.Fore.MAGENTA + colorama.Style.BRIGHT
    purple = colorama.Fore.LIGHTMAGENTA_EX + colorama.Style.BRIGHT
    reset = colorama.Style.RESET_ALL
    dim = colorama.Style.DIM


# Fix Windows terminal colors globally
colorama.just_fix_windows_console()
