"""Monday tap class."""

from typing import List

from singer_sdk import Tap, Stream
from singer_sdk import typing as th  # JSON schema typing helpers

from tap_monday.streams import (
    BoardsStream,
    GroupsStream,
    ItemsStream,
    ColumnsStream,
    ColumnValuesStream,
)

STREAM_TYPES = [
    BoardsStream,
    GroupsStream,
    ItemsStream,
    ColumnsStream,
    ColumnValuesStream,
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
        th.Property(
            "item_limit",
            th.NumberType,
            default=10,
            description="Amount of items to request",
        ),
    ).to_dict()

    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]
