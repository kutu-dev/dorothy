from .extensions import Listener
from .models import Song
from . import logging


class Channel:
    def __init__(self) -> None:
        self.logger = logging.get_logger(__name__)
        self.queue: list[Song] = []
        self.listeners: list[Listener] = []

        self.logger.info("Instantiated channel")

    def add_to_queue(self, song: Song) -> None:
        self.queue.append(song)

    def play(self) -> None:
        for listener in self.listeners:
            print(id(listener))
            listener.play(self.queue[0])

    def cleanup_listeners(self):
        for listener in self.listeners:
            listener.cleanup()
