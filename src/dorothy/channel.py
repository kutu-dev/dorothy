from .extensions import Listener
from .models import Song
from . import logging, Colors


class Channel:
    def __init__(self, channel_id: str) -> None:
        self.logger = logging.get_logger(channel_id)
        self.queue: list[Song] = []
        self.listeners: list[Listener] = []

        self.logger.info(f'Instantiated channel {Colors.dim}"{channel_id}"{Colors.reset}')

    def add_to_queue(self, song: Song) -> None:
        self.queue.append(song)

    def play(self) -> None:
        for listener in self.listeners:
            listener.play(self.queue[0])

    def cleanup_listeners(self):
        for listener in self.listeners:
            if not listener.cleanup():
                self.logger.warning(f'Listener {Colors.dim}"{listener.instance_id}"{Colors.reset} has failed cleanup!')
