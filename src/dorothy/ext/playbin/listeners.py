from dorothy.config import ConfigSchema
from dorothy.extensions import Listener
from multiprocessing import Process
from dorothy.models import Song

import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject


class PlaybinListener(Listener):
    config_schema = ConfigSchema(
        node_id="playbin-listener",
        node_type=Listener
    )

    def __init__(self) -> None:
        super().__init__()

    def start(self) -> None:
        Gst.init(None)

        self.player = Gst.ElementFactory.make("playbin", None)
        self.bus = self.player.get_bus()

        # Disable video
        fakesink = Gst.ElementFactory.make("fakesink", "fakesink")
        self.player.set_property("video-sink", fakesink)

    def play(self, song: Song) -> None:
        self.player.set_property("uri", song.uri)
        res = self.player.set_state(Gst.State.PLAYING)

        if res == Gst.StateChangeReturn.FAILURE:
            self.logger.error("Unable to start playing the song")

    def stop(self) -> None:
        res = self.player.set_state(Gst.State.NULL)

        if res == Gst.StateChangeReturn.FAILURE:
            self.logger.error("Unable to stop the playing song")

    def cleanup(self) -> bool:
        self.stop()

        return True
