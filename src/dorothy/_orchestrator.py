from logging import getLogger
from typing import Iterator, Callable, Any

from .exceptions import NodeFailureException
from .models._provider import Provider
from ._channel import Channel, ChannelStates
from .models._album import Album, AlbumResourceId
from .models._resource_id import ResourceId
from .models._song import Song, SongResourceId
from .models._artist import Artist, ArtistResourceId
from .models._node import NodeInstancePath


class Orchestrator:
    """Facade object used to abstract interactions between listeners and
    providers to the controllers.
    """

    def __init__(self) -> None:
        self._logger = getLogger(__name__)
        self._logger.info("Wiring up the orchestrator")

        self._providers: dict[str, dict[str, dict[str, Provider]]] = {}
        self._channels: dict[str, Channel] = {}

    def check_if_song_finished(self) -> None:
        """Call the check song finished method in all available channels."""

        for channel in self._channels.values():
            channel.check_if_song_finished()

    def get_channels_names(self) -> list[str]:
        """Returns a list with all the available channels by its name.

        Returns:
            The list of available channels given their names.
        """

        return list(self._channels.keys())

    def _providers_generator(self) -> Iterator[Provider]:
        """Generator used to iterate over providers with ease
        using python for loops."""

        for _, provider in self._providers.items():
            for _, instance in provider.items():
                for _, provider_object in instance.items():
                    yield provider_object

    def _access_provider(self, resource_id: ResourceId) -> Provider:
        """Route and returns a provider given the resource id of a resource of its own.

        Args:
            resource_id: The ID of the resource to get its provider.

        Returns:
            The provider where the resource is from.
        """

        plugin_name: str = resource_id.node_instance_path.plugin_name
        node_name: str = resource_id.node_instance_path.node_name
        instance_name: str = resource_id.node_instance_path.instance_name

        return self._providers[plugin_name][node_name][instance_name]

    def _delete_provider(self, node_instance_path: NodeInstancePath) -> None:
        """Remove a provider from the orchestrator given its node instance path.

        Args:
            node_instance_path: The route to the node instance of the node
                to be deleted.
        """

        plugin_name: str = node_instance_path.plugin_name
        node_name: str = node_instance_path.node_name
        instance_name: str = node_instance_path.instance_name

        self._logger.info(
            f'Removing provider "{node_instance_path}" from the orchestrator'
        )

        del self._providers[plugin_name][node_name][instance_name]

    def _delete_providers(self, node_instance_paths: list[NodeInstancePath]) -> None:
        """Remove any number of providers from the orchestrator given their
        node instance path.

        Args:
            node_instance_paths: The routes to the nodes instances in the
                orchestrator to delete.
        """

        for node_instance_path in node_instance_paths:
            self._delete_provider(node_instance_path)

    def get_song(self, song_resource_id: SongResourceId) -> Song | None:
        """Get a song object given its resource id.

        Args:
            song_resource_id: The ID of the resource of the song to get.

        Returns:
            Object that holds all the info about the requested song or `None`
                if no song was found.
        """

        try:
            return self._access_provider(song_resource_id).get_song(
                song_resource_id.unique_id
            )
        except NodeFailureException:
            self._delete_provider(song_resource_id.node_instance_path)
            return None

    def get_all_songs(self) -> list[Song]:
        """Return all songs of all providers registered in this orchestrator.

        Returns:
            List that holds all the info about all the songs reported
                by the providers.
        """

        songs: list[Song] = []

        failed_nodes: list[NodeInstancePath] = []
        for provider in self._providers_generator():
            try:
                songs.extend(provider.get_all_songs())
            except NodeFailureException:
                failed_nodes.append(provider.node_instance_path)

        self._delete_providers(failed_nodes)

        return songs

    def get_album(self, album_resource_id: AlbumResourceId) -> Album | None:
        """Get an album object given its resource id.

        Args:
            album_resource_id: The ID of the resource of the album to get.

        Returns:
            Object that holds all the info about the requested album or `None`
                if no song was found.
        """

        try:
            return self._access_provider(album_resource_id).get_album(
                album_resource_id.unique_id
            )
        except NodeFailureException:
            self._delete_provider(album_resource_id.node_instance_path)

        return None

    def get_all_albums(self) -> list[Album]:
        """Return all albums of all providers registered in this orchestrator.

        Returns:
            A list of all the albums given by the providers.
        """

        albums: list[Album] = []

        failed_nodes: list[NodeInstancePath] = []
        for provider in self._providers_generator():
            try:
                albums.extend(provider.get_all_albums())
            except NodeFailureException:
                failed_nodes.append(provider.node_instance_path)

        return albums

    def get_artist(self, artist_resource_id: ArtistResourceId) -> Artist | None:
        """Get an artist object given its resource id.

        Args:
            album_resource_id: The ID of the resource of the artist to get.

        Returns:
            Object that holds all the info about the requested artist or `None`
                if no song was found.
        """

        try:
            return self._access_provider(artist_resource_id).get_artist(
                artist_resource_id.unique_id
            )
        except NodeFailureException:
            return None

    def get_all_artists(self) -> list[Artist]:
        """Return all artists of all providers registered in this orchestrator.

        Returns:
            A list of all the artists given by the providers.
        """

        artists: list[Artist] = []

        failed_nodes: list[NodeInstancePath] = []
        for provider in self._providers_generator():
            try:
                artists.extend(provider.get_all_artists())
            except NodeFailureException:
                failed_nodes.append(provider.node_instance_path)

        return artists

    def add_to_queue(self, channel: str, resource_id: ResourceId) -> None:
        """Add to the queue of a channel all the songs related to the
        given resource id.

        If a song resource id is given then a song is added, if it's an album
        then all the songs on that album are added and if it's an artist then
        all the songs created by that artist are added to the queue.

        Args:
            channel: The channel to add the songs.
            resource_id: The resource id to add the songs from.
        """

        self.insert_to_queue(channel, resource_id, 0)

    def insert_to_queue(
        self, channel: str, resource_id: ResourceId, insert_position: int
    ) -> None:
        """Add to the queue of a channel all the songs related to the given
        resource id in the desired position.

        If a song resource id is given then a song is added, if it's an album
        then all the songs on that album are added and if it's an artist then
        all the songs created by that artist are added to the queue.

        If the insert position is greater than the queue size the call is ignored.

        Args:
            channel: The channel to add the songs.
            resource_id: The resource id to add the songs from.
                (Either a song, an album or an artist).
            insert_position: The position where the songs should be added.

        Raises:
            ValueError: Raised if the given resource ID is not
                a valid one to get songs from.
        """

        songs: list[Song] = []

        match resource_id:
            case SongResourceId():
                song = self.get_song(resource_id)

                if song is not None:
                    songs.append(song)

            case AlbumResourceId():
                album = self.get_album(resource_id)

                if album is None:
                    return

                if album.songs is None:
                    return

                songs = album.songs

            case ArtistResourceId():
                artist = self.get_artist(resource_id)

                if artist is None:
                    return

                if artist.albums is None:
                    return

                for album in artist.albums:
                    if album.songs is None:
                        continue

                    songs.extend(album.songs)

            case _:
                raise ValueError(
                    f'The type of the resource id "{resource_id}"'
                    + "is not valid for be added to the queue."
                )

        for song in songs:
            self._channels[channel].insert(song, insert_position)

    def remove_from_queue(self, channel: str, remove_position: int) -> None:
        """Remove a song from the queu of a channel given its index position.

        If the index position is greater than the queue size the call is ignored.


        Args:
            channel: The channel to remove the song.
            remove_position: The index position of the song to be removed
                from the queue.
        """

        self._channels[channel].remove_from_queue(remove_position)

    def play(self, channel: str) -> None:
        """Starts the playback in the desired channel.

        Args:
            channel: The channel to start the playback.
        """

        self._channels[channel].play()

    def pause(self, channel: str) -> None:
        """Pauses the playback in the desired channel.

        Args:
            channel: The channel to pause the playback.
        """

        self._channels[channel].pause()

    def play_pause(self, channel: str) -> bool:
        """Play or pause the playback in the desired channel inverting
        its current state.

        Args:
            channel: The channel to play or pause the playback.

        Returns:
            If the state was changed or not.
        """

        return self._channels[channel].play_pause()

    def stop(self, channel: str) -> None:
        """Stops the playback in the desired channel.

        Args:
            channel: The channel to stop the playback.
        """

        self._channels[channel].stop()

    def skip(self, channel: str) -> None:
        """Skips the current playing song in the desired channel.

        Args:
            channel: The channel to skip the current song.
        """

        self._channels[channel].skip()

    def get_queue(self, channel: str) -> list[Song]:
        """Returns a list of all the songs currently set in the queue of
        the given channel.

        Args:
            channel: The channel to get its songs from its queue.

        Returns:
            The songs currently set in the queue.
        """

        return self._channels[channel]._queue

    def play_from_queue_given_index(self, channel: str, play_position: int) -> None:
        """Start playing in the given index position in the queue in
        the desired channel.

        If the index position is greater than the queue size the call is ignored.

        Args:
            channel: The channel to play its queue.
            play_position: The position in the queue to start the playback.
        """

        self._channels[channel].play_from_queue_given_index(play_position)

    def get_current_song(self, channel: str) -> Song | None:
        """Get the current playing song in the desired channel.

        Args:
            channel: The channel to get its current playing song.

        Returns:
            The current playing song of the given channel
                or None if the channel's playback is stopped.
        """

        return self._channels[channel].current_song

    def get_channel_state(self, channel: str) -> ChannelStates:
        """Get the current state of the given channel.

        Args:
            channel: The channel to get its current state.

        Returns:
            The current state of the given channel.
        """

        return self._channels[channel].channel_state

    def _cleanup_nodes(self) -> None:
        """Start the cleanup process for all the nodes inside the orchestrator.

        This method should only be called once at the end of the current
        program execution.

        Interacting with the orchestrator after running this method is not
        safe and will probably fail if done.
        """

        self._logger.info("Cleaning provider nodes...")
        for provider in self._providers_generator():
            try:
                cleanup_message = provider.cleanup()
                if cleanup_message is not None:
                    self._logger.warning(
                        f'Provider "{provider.node_instance_path}"'
                        + 'has failed cleanup with error "{cleanup_message}"'
                    )
            except NodeFailureException:
                # Just ignore it as the "raise_failure_node_exception"
                # function that raised the exception should already have
                # informed the user about the exception.

                pass

        self._logger.info("Cleaning channels...")
        for _, channel in self._channels.items():
            channel.cleanup_listeners()
