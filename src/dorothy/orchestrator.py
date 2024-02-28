from typing import Iterator

from .logging import get_logger
from .nodes import Provider
from .channel import Channel, ChannelStates
from .models import Album, ResourceId, Song


class Orchestrator:
    """Abstraction between listeners and providers to the controllers"""

    def __init__(self) -> None:
        self._logger = get_logger(__name__)
        self._logger.info("Wiring up the orchestrator")

        self.providers: dict[str, dict[str, dict[str, Provider]]] = {}
        self.channels: dict[str, Channel] = {}

    def check_if_song_finished(self) -> None:
        for channel in self.channels.values():
            channel.check_if_song_finished()

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

    def get_all_albums(self) -> list[Album]:
        albums: list[Album] = []

        for provider in self.providers_generator():
            albums.extend(provider.get_all_albums())

        return albums

    def get_album(self, album_resource_id: ResourceId) -> Album | None:
        if album_resource_id.resource_type is not Album:
            return None

        plugin_name: str = album_resource_id.node_instance_path.plugin_name
        node_name: str = album_resource_id.node_instance_path.node_name
        instance_name: str = album_resource_id.node_instance_path.instance_name

        return self.providers[plugin_name][node_name][instance_name].get_album(
            album_resource_id.unique_id
        )

    def get_songs_from_album(self, album_resource_id: ResourceId):
        if album_resource_id.resource_type is not Album:
            return None

        plugin_name: str = album_resource_id.node_instance_path.plugin_name
        node_name: str = album_resource_id.node_instance_path.node_name
        instance_name: str = album_resource_id.node_instance_path.instance_name

        return self.providers[plugin_name][node_name][
            instance_name
        ].get_songs_from_album(album_resource_id.unique_id)

    # Listener methods
    def add_to_queue(self, channel: str, resource_id: ResourceId) -> None:
        self.insert_to_queue(channel, resource_id, 0)

    def insert_to_queue(
        self, channel: str, resource_id: ResourceId, insert_position: int
    ) -> None:
        songs: list[Song] = []

        if resource_id.resource_type is Song:
            song = self.get_song(resource_id)

            if song is not None:
                songs.append(song)

        elif resource_id.resource_type is Album:
            songs = self.get_songs_from_album(resource_id)

        for song in songs:
            self.channels[channel].insert(song, insert_position)

    def remove_from_queue(self, channel: str, remove_position: int) -> None:
        self.channels[channel].remove_from_queue(remove_position)

    def play(self, channel: str) -> None:
        self.channels[channel].play()

    def pause(self, channel: str) -> None:
        self.channels[channel].pause()

    def play_pause(self, channel: str) -> bool:
        return self.channels[channel].play_pause()

    def stop(self, channel: str) -> None:
        self.channels[channel].stop()

    def skip(self, channel: str) -> None:
        self.channels[channel].skip()

    def get_queue(self, channel: str) -> list[Song]:
        return self.channels[channel].queue

    def play_from_queue_given_index(self, channel: str, play_position: int) -> None:
        self.channels[channel].play_from_queue_given_index(play_position)

    def get_current_song(self, channel: str) -> Song | None:
        return self.channels[channel].current_song

    def get_channel_state(self, channel: str) -> ChannelStates:
        return self.channels[channel].channel_state

    def cleanup_nodes(self) -> None:
        self._logger.info("Cleaning nodes...")

        for provider in self.providers_generator():
            if not provider.cleanup():
                self._logger.warning(
                    f'Provider "{provider.node_instance_path}" has failed cleanup!'
                )

        for _, channel in self.channels.items():
            channel.cleanup_listeners()
