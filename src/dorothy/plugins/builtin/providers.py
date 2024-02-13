from pathlib import Path
from typing import Any, Callable

from dorothy.models import Album, ResourceId, Song
from dorothy.nodes import NodeInstancePath, NodeManifest, Provider
from platformdirs import (
    user_desktop_dir,
    user_documents_dir,
    user_downloads_dir,
    user_music_dir,
    user_pictures_dir,
    user_videos_dir,
)
from tinytag import TinyTag
from tinytag.tinytag import TinyTagException


class FilesystemProvider(Provider):
    @classmethod
    def get_node_manifest(cls) -> NodeManifest:
        return NodeManifest(
            node_name="filesystem",
            default_config={"paths": ["$MUSIC"], "exclude_paths": []},
        )

    def __init__(
        self, config: dict[str, Any], node_instance_path: NodeInstancePath
    ) -> None:
        super().__init__(config, node_instance_path)

        self._logger.info("Parsing source paths in the config...")
        self.paths = self.parse_paths(self.config["paths"])
        self.remove_redundant_source_paths()

        self._logger.info("Parsing ignore paths in the config...")
        self.exclude_paths = self.parse_paths(self.config["exclude_paths"])

        self.songs_paths = self.get_songs_paths()

        self.albums: dict[str, list[Path]] = {}
        self.load_songs_metadata(self.songs_paths)

    def parse_paths(self, raw_paths: list[str]) -> list[Path]:
        special_words: dict[str, Callable[[], str]] = {
            "HOME": lambda: str(Path().home().absolute()),
            "MUSIC": user_music_dir,
            "DOCUMENTS": user_documents_dir,
            "DOWNLOADS": user_downloads_dir,
            "DESKTOP": user_desktop_dir,
            "PICTURES": user_pictures_dir,
            "VIDEOS": user_videos_dir,
        }

        parsed_paths: list[Path] = []

        for path in raw_paths:
            final_path = ""
            escape_next = False
            captured_word: str | None = None

            for char in path:
                if char == "&" and not escape_next:
                    escape_next = True
                    continue

                if char == "$" and not escape_next:
                    captured_word = ""
                    continue

                if captured_word is not None:
                    captured_word += char

                if captured_word in special_words:
                    final_path += special_words[captured_word]()
                    captured_word = None
                    continue

                if captured_word is None:
                    final_path += char
                    escape_next = False

            self._logger.info(f'Parsed path "{path}" to "{final_path}"')
            parsed_paths.append(Path(final_path))

        return parsed_paths

    def remove_redundant_source_paths(self) -> None:
        self._logger.info("Removing redundant source paths...")
        redundant_paths_indexes: set[int] = set()

        for check_index, path_to_check in enumerate(self.paths):
            if check_index in redundant_paths_indexes:
                continue

            for possible_index, possible_parent_path in enumerate(self.paths):
                if check_index == possible_index:
                    continue

                if path_to_check in possible_parent_path.parents:
                    redundant_paths_indexes.add(possible_index)
                    continue

                if possible_parent_path in path_to_check.parents:
                    redundant_paths_indexes.add(check_index)
                    continue

        for set_index, source_path_index in enumerate(redundant_paths_indexes):
            del self.paths[source_path_index - set_index]

    def is_file_ignored(self, file: Path) -> bool:
        for exclude_path in self.exclude_paths:
            if exclude_path in file.parents:
                return True

        return False

    def get_songs_paths(self) -> list[Path]:
        songs_paths: list[Path] = []

        for path in self.paths:
            for file in path.glob("**/*"):
                if not file.is_file():
                    continue

                if self.is_file_ignored(file):
                    continue

                songs_paths.append(file)

        return songs_paths

    def load_songs_metadata(self, songs_paths: list[Path]) -> None:
        for song_path in songs_paths:
            try:
                metadata = TinyTag.get(song_path)
            except TinyTagException:
                continue

            album_name = metadata.album if metadata.album is not None else "Unknown"

            self.albums.setdefault(album_name, []).append(song_path)

    def get_all_songs(self) -> list[Song]:
        songs: list[Song] = []

        for song_path in self.songs_paths:
            song_resource_id = ResourceId(
                Song, self.node_instance_path, str(song_path.absolute())
            )

            try:
                song_name = TinyTag.get(song_path).title
            except TinyTagException:
                song_name = song_path.name


            songs.append(
                Song(song_resource_id, song_path.absolute().as_uri(), song_name)
            )

        return songs

    def get_song(self, song_unique_id: str) -> Song | None:
        song_path = Path(song_unique_id)

        if not song_path.is_file():
            return None

        try:
            song_name = TinyTag.get(song_path).title
        except TinyTagException:
            song_name = song_path.name

        song_resource_id = ResourceId(Song, self.node_instance_path, song_name)

        return Song(
            song_resource_id,
            song_path.as_uri(),
            song_path.name,
        )

    def get_all_albums(self) -> list[Album]:
        albums: list[Album] = []

        for album_name, song_paths in self.albums.items():
            album_resource_id = ResourceId(Album, self.node_instance_path, album_name)

            albums.append(Album(album_resource_id, album_name, len(song_paths)))

        return albums

    def get_album(self, album_unique_id: str) -> Album:
        return Album(
            ResourceId(Album, self.node_instance_path, album_unique_id), album_unique_id, len(self.albums[album_unique_id])
        )

    def get_songs_from_album(self, album_unique_id: str) -> list[Song]:
        songs: list[Song] = []

        songs_paths = self.albums[album_unique_id]

        for song_path in songs_paths:
            song_resource_id = ResourceId(
                Song, self.node_instance_path, str(song_path.absolute())
            )

            try:
                song_name = TinyTag.get(song_path).title if TinyTag.get(song_path).title is not None else song_path.name
            except TinyTagException:
                song_name = song_path.name

            songs.append(
                Song(song_resource_id, song_path.absolute().as_uri(), song_name)
            )

        return songs
