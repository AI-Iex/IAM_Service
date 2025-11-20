from enum import Enum


class AccessTokenType(str, Enum):
    """Enum for access token types."""

    USER = "user"
    CLIENT = "client"
