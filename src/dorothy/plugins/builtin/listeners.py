from typing import Any

import gi
from dorothy.models import Song
from dorothy.nodes import Listener, NodeInstancePath, NodeManifest
from dorothy.plugins.builtin.exceptions import FailedCreatePlaybinPlayer

gi.require_version("Gst", "1.0")
# Ignore the lint error raised by having a statement before an import
from gi.repository import Gst  # noqa: E402


class PlaybinListener(Listener):
    @classmethod
    def get_node_manifest(cls) -> NodeManifest:
        return NodeManifest(
            node_name="playbin",
        )

    def __init__(
        self, config: dict[str, Any], node_instance_path: NodeInstancePath
    ) -> None:
        super().__init__(config, node_instance_path)

        Gst.init(None)

        player = Gst.ElementFactory.make("playbin", None)
        if player is None:
            raise FailedCreatePlaybinPlayer("The player could not be created")

        self.player = player
        self.bus = self.player.get_bus()

        # Disable video
        fakesink = Gst.ElementFactory.make("fakesink", "fakesink")
        self.player.set_property("video-sink", fakesink)

    def play(self, song: Song) -> None:
        self.player.set_property("uri", song.uri)

        res = self.player.set_state(Gst.State.PLAYING)
        if res == Gst.StateChangeReturn.FAILURE:
            self._logger.error("Unable to start playing the song")

    def stop(self) -> None:
        res = self.player.set_state(Gst.State.NULL)
        if res == Gst.StateChangeReturn.FAILURE:
            self._logger.error("Unable to stop the playing song")

    def cleanup(self) -> bool:
        self.stop()

        return True
