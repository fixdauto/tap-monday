"""Stream type classes for tap-monday."""

import requests
import json
import re

from pathlib import Path
from typing import Any, Optional, Dict, Iterable, cast, List

from tap_monday.client import MondayStream

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class BoardsStream(MondayStream):
    """Loads boards."""

    name = "boards"
    schema_filepath = SCHEMAS_DIR / "boards.json"
    primary_keys = ["id"]
    replication_key = "updated_at"  # ISO8601/RFC3339, example: 2022-01-07T15:56:08Z

    def board_ids(self) -> Optional[List[int]]:
        """Ensure that board_ids is a list of ints."""
        board_ids_conf = self.config.get("board_ids")
        if board_ids_conf and type(board_ids_conf) is str:
            board_ids = list(map(int, re.split(r",\s*", board_ids_conf)))
            return board_ids

        return board_ids_conf

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        """Set pagination and limit."""
        return {
            "page": next_page_token or 1,
            "board_limit": self.config["board_limit"],
            "board_ids": self.board_ids(),
        }

    @property
    def query(self) -> str:
        """Form Boards query."""
        if self.board_ids():
            ql_string = """
                query Boards($board_limit: Int!, $page: Int!, $board_ids:[Int]) {
                    boards(
                        ids: $board_ids,
            """
        else:
            ql_string = """
                query Boards($board_limit: Int!, $page: Int!) {
                    boards(
            """

        ql_string += """
                        limit: $board_limit,
                        page: $page,
                        order_by: created_at
            ) {
                    id
                    name
                    description
                    state
                    updated_at
                    workspace {
                        id
                        name
                        kind
                        description
                    }
                    owner {
                        id
                        name
                        email
                    }
                }
            }
        """

        return ql_string

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Allow GroupsStream and ItemsStream to query by board_id."""
        return {"board_id": record["id"]}

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """Convert types."""
        row["id"] = int(row["id"])
        row["tapped_at"] = self.tapped_at()

        workspace = row.pop("workspace")
        if workspace is not None:
            row["workspace_id"] = int(workspace["id"])
            row["workspace_name"] = workspace["name"]
        else:
            row["workspace_id"] = 0
            row["workspace_name"] = ""

        owner = row.pop("owner")
        row["owner_id"] = owner["id"]
        row["owner_name"] = owner["name"]
        row["owner_email"] = owner["email"]

        return row


class GroupsStream(MondayStream):
    """Loads board groups."""

    name = "groups"
    schema_filepath = SCHEMAS_DIR / "groups.json"

    primary_keys = ["id", "board_id"]
    replication_key = None

    parent_stream_type = BoardsStream
    ignore_parent_replication_key = True

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        """Get board_ids from the context."""
        ctx: dict = cast(dict, context)
        return {
            "board_ids": ctx["board_id"],
        }

    @property
    def query(self) -> str:
        """Form Groups query."""
        return """
            query Groups($board_ids: [Int]) {
                boards(ids: $board_ids) {
                    id
                    groups {
                        id
                        title
                        position
                        color
                        deleted
                    }
                }
            }
        """

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse groups response."""
        resp_json = response.json()
        for row in resp_json["data"]["boards"]:
            for group in row["groups"]:
                yield group

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """Convert types."""
        ctx: dict = cast(dict, context)
        row["board_id"] = ctx["board_id"]
        row["position"] = float(row["position"])
        row["tapped_at"] = self.tapped_at()
        return row


class ItemsStream(MondayStream):
    """Loads items."""

    name = "items"
    schema_filepath = SCHEMAS_DIR / "items.json"

    primary_keys = ["id"]
    replication_key = "updated_at"

    parent_stream_type = BoardsStream
    ignore_parent_replication_key = True

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        """Get board_ids from the context."""
        ctx: dict = cast(dict, context)
        return {
            "board_ids": ctx["board_id"],
        }

    @property
    def query(self) -> str:
        """Form Items query."""
        return """
            query Items($board_ids: [Int]) {
                boards(ids: $board_ids) {
                    id
                    items {
                        id
                        name
                        state
                        created_at
                        updated_at
                        creator_id
                        creator {
                            email
                            name
                        }
                        group {
                            id
                        }
                        parent_item {
                            id
                        }
                    }
                }
            }
        """

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse groups response."""
        resp_json = response.json()
        for row in resp_json["data"]["boards"]:
            for item in row["items"]:
                yield item

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """Add and convert fields."""
        row["id"] = int(row["id"])

        ctx: dict = cast(dict, context)
        row["board_id"] = ctx["board_id"]

        row["group_id"] = row["group"]["id"]

        parent_item = row.pop("parent_item")
        row["parent_item_id"] = 0 if parent_item is None else int(parent_item["id"])

        row["creator_id"] = int(row["creator_id"])
        creator = row.pop("creator")
        if creator is not None:
            row["creator_email"] = creator["email"]
            row["creator_name"] = creator["name"]
        else:
            row["creator_email"] = ""
            row["creator_name"] = ""

        row["tapped_at"] = self.tapped_at()
        return row

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Allow ColumnValuesStream to query by item_id."""
        return {"item_id": int(record["id"])}


class ColumnsStream(MondayStream):
    """Loads columns."""

    name = "columns"
    schema_filepath = SCHEMAS_DIR / "columns.json"
    primary_keys = ["id", "board_id"]
    replication_key = None

    parent_stream_type = BoardsStream
    ignore_parent_replication_key = True

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        """Get board_ids from the context."""
        ctx: dict = cast(dict, context)
        return {
            "board_ids": ctx["board_id"],
        }

    @property
    def query(self) -> str:
        """Form Columns query."""
        return """
            query Columns($board_ids: [Int]) {
                boards(ids: $board_ids) {
                    id
                    columns {
                        id
                        title
                        archived
                        settings_str
                        description
                        type
                        width
                    }
                }
            }
        """

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse groups response."""
        resp_json = response.json()
        for row in resp_json["data"]["boards"]:
            for column in row["columns"]:
                yield column

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """Convert types."""
        ctx: dict = cast(dict, context)

        row["board_id"] = ctx["board_id"]
        row["tapped_at"] = self.tapped_at()
        return row


class ColumnValuesStream(MondayStream):
    """Loads column values."""

    name = "column_values"
    schema_filepath = SCHEMAS_DIR / "column_values.json"

    primary_keys = ["id", "item_id"]
    replication_key = None

    parent_stream_type = ItemsStream
    ignore_parent_replication_key = True

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        """Get board_ids from the context."""
        ctx: dict = cast(dict, context)
        return {
            "item_ids": ctx["item_id"],
        }

    @property
    def query(self) -> str:
        """Form ColumnValues query."""
        return """
            query ColumnValues($item_ids: [Int]) {
                items(ids: $item_ids) {
                    id
                    column_values {
                        id
                        title
                        text
                        type
                        value
                        additional_info
                        description
                    }
                }
            }
        """

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse groups response."""
        resp_json = response.json()
        for row in resp_json["data"]["items"]:
            for column_value in row["column_values"]:
                yield column_value

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """Convert types."""
        ctx: dict = cast(dict, context)
        row["item_id"] = ctx["item_id"]

        if row["value"] is None:
            row["value"] = ""
        else:
            row["value"] = json.dumps(row["value"])

        if row["additional_info"] is None:
            row["additional_info"] = ""
        else:
            row["additional_info"] = json.dumps(row["additional_info"])

        row["tapped_at"] = self.tapped_at()
        return row
