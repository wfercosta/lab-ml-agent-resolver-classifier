class PermanentError(Exception):
    """Do not retry; message is invalid or irrecoverable."""


class TransientError(Exception):
    """Retryable; external dependency or temporary issue."""