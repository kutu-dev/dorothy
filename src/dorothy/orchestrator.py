from . import Colors
from .channel import Channel
from .logging import get_logger
from .models import Id, Listener, Provider, Song


class Orchestrator:
    """Abstraction between listeners and providers to the controllers"""

    def __init__(
        self, providers: dict[str, Provider], listeners: list[Listener]
    ) -> None:
        self.logger = get_logger(__name__)
        self.logger.info("Wiring up the orchestrator")

        self.start_nodes(providers, listeners)

        self.providers = providers
        self.channels: dict[str, Channel] = {}

        self.initialize_channels(listeners)

    @staticmethod
    def start_nodes(providers: dict[str, Provider], listeners: list[Listener]) -> None:
        for _, provider in providers.items():
            provider.start()

        for listener in listeners:
            listener.start()

    def initialize_channels(self, listeners: list[Listener]) -> None:
        for listener in listeners:
            # A listener after being loaded by the node_factory in the ConfigManager
            # should only have one channel registered in its config
            registered_channel = listener.instance_config["channels"][0]

            if registered_channel not in self.channels:
                self.channels[registered_channel] = Channel(registered_channel)

            self.channels[registered_channel].listeners.append(listener)

    # Provider methods

    def get_all_songs(self) -> list[Song]:
        songs: list[Song] = []

        for _, provider in self.providers.items():
            songs.extend(provider.get_all_songs())

        return songs

    def get_song(self, song_id: Id) -> Song:
        return self.providers[song_id.provider_id].get_song(song_id.item_id)

    # Listener methods

    def add_to_queue(self, channel: str, song_id: Id) -> None:
        song = self.get_song(song_id)

        self.channels[channel].add_to_queue(song)

    def play(self, channel: str) -> None:
        self.channels[channel].play()

    def stop(self, channel: str) -> None:
        self.channels[channel].stop()

    def cleanup_nodes(self) -> None:
        self.logger.info("Cleaning nodes...")

        for _, provider in self.providers.items():
            if not provider.cleanup():
                self.logger.warning(
                    f'Provider {Colors.dim}"{provider.instance_id}"{Colors.reset} has failed cleanup!'
                )

        for _, channel in self.channels.items():
            channel.cleanup_listeners()
