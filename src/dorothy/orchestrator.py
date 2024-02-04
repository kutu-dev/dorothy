from typing import Iterator

from .channel import Channel
from .logging import get_logger
from .models import ResourceId, Song
from .nodes import Provider


class Orchestrator:
    """Abstraction between listeners and providers to the controllers"""

    def __init__(self) -> None:
        self._logger = get_logger(__name__)
        self._logger.info("Wiring up the orchestrator")

        self.providers: dict[str, dict[str, dict[str, Provider]]] = {}
        self.channels: dict[str, Channel] = {}

    def providers_generator(self) -> Iterator[Provider]:
        for _, provider in self.providers.items():
            for _, instance in provider.items():
                for _, provider_object in instance.items():
                    yield provider_object

    # Provider methods
    def get_all_songs(self) -> list[Song]:
        songs: list[Song] = []

        for provider in self.providers_generator():
            songs.extend(provider.get_all_songs())

        return songs

    def get_song(self, song_resource_id: ResourceId) -> Song | None:
        if song_resource_id.resource_type is not Song:
            return None

        plugin_name: str = song_resource_id.node_instance_path.plugin_name
        node_name: str = song_resource_id.node_instance_path.node_name
        instance_name: str = song_resource_id.node_instance_path.instance_name

        return self.providers[plugin_name][node_name][instance_name].get_song(
            song_resource_id.unique_id
        )

    # Listener methods
    def add_to_queue(self, channel: str, song_resource_id: ResourceId) -> None:
        song = self.get_song(song_resource_id)

        if song is None:
            return

        self.channels[channel].add_to_queue(song)

    def play(self, channel: str) -> None:
        self.channels[channel].play()

    def stop(self, channel: str) -> None:
        self.channels[channel].stop()

    def cleanup_nodes(self) -> None:
        self._logger.info("Cleaning nodes...")

        for provider in self.providers_generator():
            if not provider.cleanup():
                self._logger.warning(
                    f'Provider "{provider.node_instance_path}" has failed cleanup!'
                )

        for _, channel in self.channels.items():
            channel.cleanup_listeners()
