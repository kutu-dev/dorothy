from typing import Any


class Song:
    def __init__(self, id_: Any, title: str | None = None) -> None:
        self.id: Any = id_
        self.title = title
