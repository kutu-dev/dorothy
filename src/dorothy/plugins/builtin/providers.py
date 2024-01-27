from pathlib import Path

from dorothy.config import ConfigSchema
from dorothy.models import Id, Provider, Song


class FilesystemProvider(Provider):
    config_schema = ConfigSchema(
        node_id="filesystem-provider",
        node_type=Provider,
    )

    def __init__(self) -> None:
        super().__init__()

    def get_all_songs(self) -> list[Song]:
        foo = (Path.home() / Path("music")).glob("**/*")
        bar = []

        for song in foo:
            if not song.is_file():
                continue

            song_id = Id(str(song.absolute()), self.instance_id)
            bar.append(Song(song_id, f"file://{song.absolute()}", song.name))

        return bar

    def get_song(self, song_id: str) -> Song:
        song_path = Path(song_id)

        return Song(
            Id(self.instance_id, song_path),
            f"file://{song_path.absolute()}",
            song_path.name,
        )
