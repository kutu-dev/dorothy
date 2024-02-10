from .logging import get_logger
from .models import Song
from .nodes import Listener


class Channel:
    def __init__(self, channel_name: str) -> None:
        self.listeners: list[Listener] = []
        self._logger = get_logger(channel_name)
        self.queue: list[Song] = []

        self._logger.info(f'Instantiated channel "{channel_name}"')

    def add_to_queue(self, song: Song) -> None:
        self._logger.info(f'Adding song "{song.title}" to queue')

        self.queue.append(song)

    def play(self) -> None:
        for listener in self.listeners:
            listener.play(self.queue[0])

    def stop(self) -> None:
        for listener in self.listeners:
            listener.stop()

    def cleanup_listeners(self) -> None:
        for listener in self.listeners:
            if not listener.cleanup():
                self._logger.warning(
                    f'Listener "{str(listener.node_instance_path)}" has failed cleanup!'
                )
