from dorothy.exceptions import NodeFailureException


class FailedCreatePlaybinPlayer(NodeFailureException):
    """Raised when starting the Playbin playback player fails."""

    ...
