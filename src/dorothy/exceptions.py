class NodeFailureException(Exception):
    """Exception raised by any node during normal operation to inform that
    it has been destabilized and should no longer be used
    """

    pass
