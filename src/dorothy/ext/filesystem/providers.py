from dorothy.config import ConfigSchema
from dorothy.extensions import Provider
from dorothy.models import Song
from pathlib import Path


class FilesystemProvider(Provider):
    config_schema = ConfigSchema(
        node_id="filesystem-provider",
        node_type=Provider
    )

    def __init__(self):
        super().__init__()

    def get_all_songs(self) -> list[Song]:
        foo = (Path.home() / Path("music")).glob('**/*')
        bar = []

        for song in foo:
            if not song.is_file():
                continue

            bar.append(Song(song.absolute(), f"file://{song.absolute()}", song.name))

        return bar
