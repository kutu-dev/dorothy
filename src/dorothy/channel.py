import time
from enum import Enum

from .logging import get_logger
from .nodes import Listener
from .models import Song


class ChannelStates(Enum):
    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"


class Channel:
    def __init__(self, channel_name: str) -> None:
        self.listeners: list[Listener] = []
        self._logger = get_logger(channel_name)
        self.queue: list[Song] = []
        self.channel_state = ChannelStates.STOPPED
        self.current_song: Song | None = None

        self.song_start_timestamp: int = 0

        self._logger.info(f'Instantiated channel "{channel_name}"')

    def insert(self, song: Song, insert_position: int) -> None:
        self._logger.info(
            f'Adding song "{song.title}" to queue in position "{insert_position}"'
        )

        self.queue.insert(
            insert_position if insert_position <= len(self.queue) else len(self.queue),
            song,
        )

    def check_if_song_finished(self) -> None:
        if self.channel_state != ChannelStates.PLAYING:
            return

        if time.time() - self.song_start_timestamp > self.current_song.duration:
            self.skip()

    def play(self) -> None:
        if self.channel_state == ChannelStates.PLAYING:
            return

        for listener in self.listeners:
            if self.channel_state == ChannelStates.PAUSED:
                listener.play(self.current_song)
                continue

            if len(self.queue) > 0:
                self.current_song = self.queue[0]
                listener.play(self.current_song)
                self.queue.pop(0)

        self.channel_state = ChannelStates.PLAYING
        self.song_start_timestamp = time.time()

    def pause(self) -> None:
        for listener in self.listeners:
            listener.pause()

        self.channel_state = ChannelStates.PAUSED

    def play_pause(self) -> bool:
        queue_changed = False
        if self.channel_state == ChannelStates.STOPPED:
            queue_changed = True

        if self.channel_state != ChannelStates.PLAYING:
            self.play()
        else:
            self.pause()

        return queue_changed

    def stop(self) -> None:
        for listener in self.listeners:
            listener.stop()

        self.current_song = None
        self.channel_state = ChannelStates.STOPPED

    def skip(self) -> None:
        self.stop()
        self.play()

    def remove_from_queue(self, remove_position: int) -> None:
        if remove_position > len(self.queue) - 1:
            return

        self.queue.pop(remove_position)

    def play_from_queue_given_index(self, play_position: int) -> None:
        if play_position > len(self.queue):
            return

        self.queue = self.queue[play_position:]
        self.skip()

    def cleanup_listeners(self) -> None:
        for listener in self.listeners:
            if not listener.cleanup():
                self._logger.warning(
                    f'Listener "{str(listener.node_instance_path)}" has failed cleanup!'
                )
