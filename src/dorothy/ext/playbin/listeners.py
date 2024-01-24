from dorothy.config import ConfigSchema
from dorothy.extensions import Listener
from multiprocessing import Process
from dorothy.models import Song


class PlaybinListener(Listener):
    config_schema = ConfigSchema(
        node_id="playbin-listener",
        node_type=Listener
    )

    def __init__(self) -> None:
        super().__init__()

        self.player_process: Process | None = None
        self.uri = None

    def foo(self, uri: str) -> None:
        import gi

        gi.require_version('Gst', '1.0')
        from gi.repository import Gst, GObject

        Gst.init(None)

        player = Gst.ElementFactory.make("playbin", None)

        # Disable video
        fakesink = Gst.ElementFactory.make("fakesink", "fakesink")
        player.set_property("video-sink", fakesink)

        player.set_property("uri", uri)

        res = player.set_state(Gst.State.PLAYING)

        if res == Gst.StateChangeReturn.FAILURE:
            print("Unable to set the pipeline to the playing state.")

        bus = player.get_bus()

        msg = bus.timed_pop_filtered(
            Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)

        player.set_state(Gst.State.NULL)

    def play(self, song: Song) -> None:
        print(self.instance_id + ": " + song.uri)
        # self.song = song
        # self.player_process = Process(target=self.foo, args=(song,))
        # self.player_process.start()

    def clean(self) -> None:
        self.logger.debug(self.uri)
        self.player_process.terminate()
        self.player_process.close()
