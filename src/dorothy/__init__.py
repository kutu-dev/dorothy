import platform
import sys
import colorama
from importlib.metadata import version
from ._orchestrator import Orchestrator
from .models._artist import ArtistResourceId, Artist
from .models._album import AlbumResourceId, Album
from .models._controller import Controller
from .models._listener import Listener
from .models._node import NodeInstancePath, NodeManifest
from .models._plugin_manifest import PluginManifest
from .models._provider import Provider
from .models._song import SongResourceId, Song
from ._deserializers import deserialize_resource_id, deserialize_node_instance_path

if sys.version_info < (3, 11, 0):
    sys.exit("Python 3.11.0 or later required, " +
             f"found {platform.python_version()}")

# Fix Windows terminal colors globally
colorama.just_fix_windows_console()

# Global package variables
__version__ = version("dorothy")

__all__ = [
    "Orchestrator",
    "ArtistResourceId",
    "Artist",
    "AlbumResourceId",
    "Album",
    "Controller",
    "Listener",
    "NodeInstancePath",
    "NodeManifest",
    "PluginManifest",
    "Provider",
    "SongResourceId",
    "Song",
    "deserialize_resource_id",
    "deserialize_node_instance_path",
]
