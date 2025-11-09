"""
Application custom errors.

:author: Max Milazzo
"""



from dataclasses import dataclass
from enum import Enum



class ErrorKind(str, Enum):
    """
    Domain error kinds.
    """

    VALIDATION = "validation"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    PERMISSION = "permission_denied"
    UNAVAILABLE = "unavailable"
    INTERNAL = "internal"



@dataclass
class DomainException(Exception):
    """
    Custom domain error.
    """

    kind: ErrorKind = ErrorKind.INTERNAL
    message: str = ""