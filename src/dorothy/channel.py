import time
from enum import Enum
from logging import getLogger

from .exceptions import NodeFailureException
from .nodes import Listener
from .models import Song


class ChannelStates(Enum):
    """A enumeration that holds all the states that a channel can be."""

    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"


class Channel:
    """Channel that holds and manages all the listeners associated with itself."""

    def __init__(self, channel_name: str) -> None:
        self._logger = getLogger(channel_name)

        self._listeners: list[Listener] = []

        self._queue: list[Song] = []
        self._song_start_timestamp: int = 0

        self.channel_state = ChannelStates.STOPPED
        self.current_song: Song | None = None

        self._logger.info(f'Instantiated channel "{channel_name}"')

    def insert(self, song: Song, insert_position: int) -> None:
        """Insert a song into the queue in the given position.

        If the insert position is greater than the queue size the call is ignored.

        :param song: The song to insert.
        :param insert_position: The position in the queue to insert the song.
        """

        self._logger.info(
            f'Adding song "{song.title}" to queue in position "{insert_position}"'
        )

        if insert_position > len(self._queue):
            return

        self._queue.insert(
            insert_position if insert_position <= len(self._queue) else len(self._queue),
            song,
        )

    def check_if_song_finished(self) -> None:
        """Check if the song has finished and change to the next one if so."""

        if self.channel_state != ChannelStates.PLAYING:
            return

        if time.time() - self._song_start_timestamp > self.current_song.duration:
            self.skip()

    def play(self) -> None:
        """Start playing the current song or the next one if the channel was stopped."""

        if self.channel_state == ChannelStates.PLAYING:
            return

        for index, listener in enumerate(self._listeners):
            try:
                if self.channel_state == ChannelStates.PAUSED:
                    listener.play(self.current_song)
                    continue

                if len(self._queue) > 0:
                    self.current_song = self._queue[0]
                    listener.play(self.current_song)
                    self._queue.pop(0)
            except NodeFailureException:
                del self._listeners[index]

        self.channel_state = ChannelStates.PLAYING
        self._song_start_timestamp = time.time()

    def pause(self) -> None:
        """Pause the current playing song."""

        if self.channel_state == ChannelStates.PAUSED:
            return

        for index, listener in enumerate(self._listeners):
            try:
                listener.pause()
            except NodeFailureException:
                del self._listeners[index]

        self.channel_state = ChannelStates.PAUSED

    def play_pause(self) -> bool:
        """Play or pause the playback inverting the current channel state."""

        queue_changed = False
        if self.channel_state == ChannelStates.STOPPED:
            queue_changed = True

        if self.channel_state != ChannelStates.PLAYING:
            self.play()
        else:
            self.pause()

        return queue_changed

    def stop(self) -> None:
        """Stop the playback in the channel."""

        if self.channel_state == ChannelStates.STOPPED:
            return

        for index, listener in enumerate(self._listeners):
            try:
                listener.stop()
            except NodeFailureException:
                del self._listeners[index]

        self.current_song = None
        self.channel_state = ChannelStates.STOPPED

    def skip(self) -> None:
        """Skip the current playing song and start the next one in the queue."""

        self.stop()
        self.play()

    def remove_from_queue(self, remove_position: int) -> None:
        """Remove from the queue the desired song given its position in it.

        If the insert position is greater than the queue size the call is ignored.

        :param remove_position: The position in the queue of the song to be removed.
        """

        if remove_position > len(self._queue) - 1:
            return

        self._queue.pop(remove_position)

    def play_from_queue_given_index(self, play_position: int) -> None:
        """Start the playback of the specified song by its position in the queue,
        removing any song before it in the queue.

        If the insert position is greater than the queue size the call is ignored.

        :param play_position: The position in the queue of the song to start the playback with.
        """

        if play_position > len(self._queue):
            return

        self._queue = self._queue[play_position:]
        self.skip()

    def cleanup_listeners(self) -> None:
        """Start the cleanup process for all the listeners inside the channel.

        This method should only be called once at the end of the current program execution.
        Interacting with the channel after running this method is not safe and will probably fail if done.
        """

        for listener in self._listeners:
            try:
                if not listener.cleanup():
                    self._logger.warning(
                        f'Listener "{str(listener.node_instance_path)}" has failed cleanup'
                )
            except NodeFailureException:
                # Just ignore it as the "raise_failure_node_exception" function that raised the exception
                # should already have informed the user about the exception.
                pass
