from .config import ConfigManager
from .extensions import Extensions


class Orchestrator:
    def __init__(self, config_manager: ConfigManager, extensions: Extensions) -> None:
        ...
