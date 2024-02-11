from .logging import get_logger
from .models import Song
from .nodes import Listener


class Channel:
    def __init__(self, channel_name: str) -> None:
        self.listeners: list[Listener] = []
        self._logger = get_logger(channel_name)
        self.queue: list[Song] = []
        self.now_playing: Song | None = None
        self.is_paused = True

        self._logger.info(f'Instantiated channel "{channel_name}"')

    def insert(self, song: Song, insert_position: int) -> None:
        self._logger.info(f'Adding song "{song.title}" to queue in position "{insert_position}"')

        self.queue.insert(insert_position if insert_position <= len(self.queue) else len(self.queue), song)

    def play(self) -> None:
        for listener in self.listeners:
            if self.now_playing is not None:
                next_song = self.now_playing
            elif len(self.queue) > 0:
                next_song = self.queue[0]
            else:
                return

            listener.play(next_song)

        self.is_paused = False

        if self.now_playing is None:
            self.now_playing = self.queue[0]
            self.queue.pop(0)

    def pause(self) -> None:
        for listener in self.listeners:
            listener.pause()

        self.is_paused = True

    def play_pause(self) -> None:
        if self.is_paused:
            self.play()
        else:
            self.pause()

    def stop(self) -> None:
        for listener in self.listeners:
            listener.stop()

        self.now_playing = None
        self.is_paused = False

    def skip(self) -> None:
        self.now_playing = None
        self.play()

    def remove_from_queue(self, remove_position: int) -> None:
        if remove_position > len(self.queue) - 1:
            return

        self.queue.pop(remove_position)

    def play_from_queue_given_index(self, play_position: int) -> None:
        if play_position > len(self.queue):
            return

        if play_position == 0:
            self.skip()
            return

        self.now_playing = self.queue[play_position]
        self.remove_from_queue(play_position)
        self.play()

    def cleanup_listeners(self) -> None:
        for listener in self.listeners:
            if not listener.cleanup():
                self._logger.warning(
                    f'Listener "{str(listener.node_instance_path)}" has failed cleanup!'
                )
