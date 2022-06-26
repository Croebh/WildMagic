class WildException(Exception):
    """A base exception class."""

    def __init__(self, msg):
        super().__init__(msg)


class InvalidArgument(WildException):
    """Raised when an argument is invalid."""

    pass


class NotAllowed(WildException):
    """Raised when a user tries to do something they are not allowed to do by role or dependency."""

    pass


class SelectionException(WildException):
    """A base exception for message awaiting exceptions to stem from."""

    pass


class NoSelectionElements(SelectionException):
    """Raised when get_selection() is called with no choices."""

    def __init__(self, msg=None):
        super().__init__(msg or "There are no choices to select from.")


class SelectionCancelled(SelectionException):
    """Raised when get_selection() is cancelled or times out."""

    def __init__(self):
        super().__init__("Selection timed out or was cancelled.")
