from . import logging
from . import __version__, Colors
from .extensions import load_extensions


def main() -> int:
    logger = logging.get_logger(__name__)

    logger.info(f"{Colors.purple}     ___              _   _        ")
    logger.info(f"{Colors.purple}    |   \\ ___ _ _ ___| |_| |_ _  _ ")
    logger.info(f"{Colors.purple}    | |) / _ \\ '_/ _ \\  _| ' \\ || |")
    logger.info(f"{Colors.purple}    |___/\\___/_| \\___/\\__|_||_\\_, |")
    logger.info(f"{Colors.purple}                               |__/ ")
    logger.info(f"     {Colors.dim}Version: {__version__}{Colors.reset}")
    logger.info(f"  Time to mix {Colors.blue}drinks{Colors.reset} and change {Colors.red}lives{Colors.reset}")
    logger.info("")

    providers = load_extensions()

    for song in providers[0].list_all_songs():
        print(providers[0].get_uri(song.id))

        import gi

        gi.require_version('Gst', '1.0')
        from gi.repository import Gst, GObject
        Gst.init(None)

        player = Gst.ElementFactory.make("playbin", None)

        # Disable video
        fakesink = Gst.ElementFactory.make("fakesink", "fakesink")
        player.set_property("video-sink", fakesink)

        player.set_property("uri", providers[0].get_uri(song.id))

        res = player.set_state(Gst.State.PLAYING)

        if res == Gst.StateChangeReturn.FAILURE:
            print("Unable to set the pipeline to the playing state.")

        bus = player.get_bus()

        msg = bus.timed_pop_filtered(
            Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)

        player.set_state(Gst.State.NULL)

    return 0
