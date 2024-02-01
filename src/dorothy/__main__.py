from .daemon import start_daemon


def main() -> None:
    start_daemon()

    # TODO CODE REFACTOR:
    #  - FIX MYPY IN THE WAY
    #  - Finish the IDs deserializers
    #  - Make a few prototypes and tests with a deserializer in daemon.py
    #  - Reduce duplicated code in PluginHandler

    # TODO Priority:
    #  - LOGGER OUTPUT TO STDERR(?)
    #  - DISABLE COLOR IN PIPING
    #  - Reduce repetition in post data validations on RestController
    #  - make a global config manager (in ConfigManager?)
    #     for Dorothy configs like (use_splash/skip_splash, colorless mode, goodbye message , etc)
    #  - URI transformers (when Discord bot is in the works)
    #  - Refactor load_plugins and node_factory

    # TODO Exception overhaul:
    #  - Invalid config checker
    #  - When a Exception occurs loading a plugin
    #  - When cleanup instead of return bool (?)


if __name__ == "__main__":
    main()
