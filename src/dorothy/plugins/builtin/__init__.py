from dorothy.nodes import PluginManifest

from .controllers import RestController
from .listeners import PlaybinListener
from .providers import FilesystemProvider


def get_plugin_manifest() -> PluginManifest:
    """Well-known function that returns all the useful data that the plugin holds."""

    plugin_manifesto = PluginManifest()
    plugin_manifesto.controllers = {RestController}
    plugin_manifesto.providers = {FilesystemProvider}
    plugin_manifesto.listeners = {PlaybinListener}

    return plugin_manifesto
