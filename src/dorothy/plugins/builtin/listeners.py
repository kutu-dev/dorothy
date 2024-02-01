from typing import Any

import gi
from dorothy.models import Song
from dorothy.nodes import Listener, NodeInstancePath, NodeManifest

gi.require_version("Gst", "1.0")
from gi.repository import Gst


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
        self._logger = self.get_logger()

        Gst.init(None)

        self.player = Gst.ElementFactory.make("playbin", None)

        # TODO This should be handle gracefully
        if self.player is None:
            raise Exception("PANIC")

        self.bus = self.player.get_bus()

        # Disable video
        fakesink = Gst.ElementFactory.make("fakesink", "fakesink")
        self.player.set_property("video-sink", fakesink)

    def play(self, song: Song) -> None:
        # TODO This should be handle gracefully
        if self.player is None:
            raise Exception("PANIC")

        self.player.set_property("uri", song.uri)

        res = self.player.set_state(Gst.State.PLAYING)
        if res == Gst.StateChangeReturn.FAILURE:
            self._logger.error("Unable to start playing the song")

    def stop(self) -> None:
        # TODO This should be handle gracefully
        if self.player is None:
            raise Exception("PANIC")

        res = self.player.set_state(Gst.State.NULL)
        if res == Gst.StateChangeReturn.FAILURE:
            self._logger.error("Unable to stop the playing song")

    def cleanup(self) -> bool:
        self.stop()

        return True
