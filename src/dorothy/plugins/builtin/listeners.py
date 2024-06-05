from multiprocessing import set_start_method
from typing import Any

import gi

from dorothy import Listener, NodeInstancePath, NodeManifest, Song

from .exceptions import FailedCreatePlaybinPlayer

gi.require_version("Gst", "1.0")
# Ignore the lint error raised by having a statement before an import
from gi.repository import Gst  # noqa: E402


def ensure_player_is_available(method):
    """
    Ensure that the player has been started, this shouldn't be done at the __init__ of the class
    because that will break creating new process using the multiprocessing package
    in systems that use "spawn" as start method (Windows and macOS)
    """

    def inner(self, *args, **kwargs):
        if self.player is None:
            self.start_the_player()

        method(self, *args, **kwargs)

    return inner


class PlaybinListener(Listener):
    """Player that enables music playback using the `GStreamer` C library."""

    @classmethod
    def get_node_manifest(cls) -> NodeManifest:
        """Generate the node manifest of the listener.

        Returns:
            The node manifest.
        """

        return NodeManifest(
            name="playbin",
        )

    def __init__(
        self, config: dict[str, Any], node_instance_path: NodeInstancePath
    ) -> None:
        super().__init__(config, node_instance_path)

        self.player = None
        self.current_song_uri: str = ""

    def start_the_player(self):
        """Start the Playbin player.

        Raises:
            FailedCreatePlaybinPlayer: Raised if the library fails
                to create a player instance.
        """

        Gst.init(None)

        player = Gst.ElementFactory.make("playbin", None)
        if player is None:
            raise FailedCreatePlaybinPlayer("The player could not be created")

        self.player = player

        # Disable video
        fakesink = Gst.ElementFactory.make("fakesink", "fakesink")
        self.player.set_property("video-sink", fakesink)

    @ensure_player_is_available
    def play(self, song: Song) -> None:
        """Play the given song.

        Args:
            song: The song to play.
        """

        if song.uri != self.current_song_uri:
            self.stop()
            self.player.set_property("uri", song.uri)
            self.current_song_uri = song.uri

        res = self.player.set_state(Gst.State.PLAYING)
        if res == Gst.StateChangeReturn.FAILURE:
            self.logger().error("Unable to play the song")

    @ensure_player_is_available
    def pause(self) -> None:
        """Pause the current playing song."""

        res = self.player.set_state(Gst.State.PAUSED)
        if res == Gst.StateChangeReturn.FAILURE:
            self.logger().error("Unable to pause the song")

    @ensure_player_is_available
    def stop(self) -> None:
        """Stop the song playback."""

        res = self.player.set_state(Gst.State.NULL)
        if res == Gst.StateChangeReturn.FAILURE:
            self.logger().error("Unable to stop the playing song")

    def cleanup(self) -> None | str:
        """Stop the player and clean up it.

        Returns:
            None or a string with a error message if something goes wrong.
        """

        self.stop()

        return None
