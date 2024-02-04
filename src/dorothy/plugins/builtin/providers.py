from pathlib import Path
from typing import Any, Callable

from dorothy.models import ResourceId, Song
from dorothy.nodes import NodeInstancePath, NodeManifest, Provider
from platformdirs import (
    user_desktop_dir,
    user_documents_dir,
    user_downloads_dir,
    user_music_dir,
    user_pictures_dir,
    user_videos_dir,
)


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
        self._logger = self.get_logger()

        self._logger.info("Parsing source paths in the config...")
        self.paths = self.parse_paths(self.config["paths"])
        self.remove_redundant_source_paths()

        self._logger.info("Parsing ignore paths in the config...")
        self.exclude_paths = self.parse_paths(self.config["exclude_paths"])

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

    def get_all_songs(self) -> list[Song]:
        songs: list[Song] = []

        for path in self.paths:
            for file in path.glob("**/*"):
                if not file.is_file():
                    continue

                if self.is_file_ignored(file):
                    continue

                song_resource_id = ResourceId(
                    Song, self.node_instance_path, str(file.absolute())
                )
                songs.append(
                    Song(song_resource_id, f"file://{file.absolute()}", file.name)
                )

        return songs

    def get_song(self, song_unique_id: str) -> Song | None:
        song_path = Path(song_unique_id)

        if not song_path.is_file():
            return None

        song_resource_id = ResourceId(Song, self.node_instance_path, str(song_path))

        return Song(
            song_resource_id,
            song_path.as_uri(),
            song_path.name,
        )
