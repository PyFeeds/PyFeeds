class FeedsException(Exception):
    """
    Base exception class for all exceptions thrown by Feeds.
    """


class DropResponse(FeedsException):
    def __init__(self, message, transient=False):
        self.transient = transient
        super().__init__(message)
