"""Monday tap class."""

from typing import List

from singer_sdk import Tap, Stream
from singer_sdk import typing as th  # JSON schema typing helpers

# TODO: Import your custom stream types here:
from tap_monday.streams import (
    BoardsStream,
    GroupsStream,
    ItemsStream,
    # ColumnValuesStream,
)

# TODO: Compile a list of custom stream types here
#       OR rewrite discover_streams() below with your custom logic.
STREAM_TYPES = [
    BoardsStream,
    GroupsStream,
    ItemsStream,
    # ColumnValuesStream,
]


class TapMonday(Tap):
    """Monday tap class."""

    name = "tap-monday"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "auth_token",
            th.StringType,
            required=True,
            description="The token to authenticate against the API service",
        ),
        th.Property(
            "api_url",
            th.StringType,
            default="https://api.mysample.com",
            description="The url for the API service",
        ),
        th.Property(
            "board_limit",
            th.NumberType,
            default=10,
            description="Amount of boards to request",
        ),
    ).to_dict()

    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]
