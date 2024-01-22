from dorothy.extensions import Provider
from dorothy.models import Song
from pathlib import Path


class FilesystemProvider(Provider):
    def __init__(self):
        super().__init__(__name__)

    def list_all_songs(self) -> list[Song]:
        foo = (Path.home() / Path("music")).glob('**/*')
        bar = []

        for song in foo:
            if not song.is_file():
                continue

            bar.append(Song(song.absolute(), song.name))

        return bar

    def get_uri(self, id_: Path) -> str:
        return f"file://{id_}"
