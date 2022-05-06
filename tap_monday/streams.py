"""Stream type classes for tap-monday."""

import requests
import json

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Dict, Iterable, cast

from tap_monday.client import MondayStream

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class BoardsStream(MondayStream):
    """Loads boards."""

    name = "boards"
    schema_filepath = SCHEMAS_DIR / "boards.json"
    primary_keys = ["id"]
    replication_key = "updated_at"
    # updated_at, DateTimeType, ISO 8601 / RFC3339, 2022-01-07T15:56:08Z

    @property
    def query(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        return f"""
            boards(
                limit: {self.config.get("board_limit")},
                order_by: created_at
            ) {{
                id
                name
                description
                state
                updated_at
                workspace {{
                    id
                    name
                    kind
                    description
                }}
                owner {{
                    id
                    name
                    email
                }}
            }}
        """

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Allow GroupsStream to query by board_id."""
        return {
            "board_id": record["id"],
        }

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse boards response."""
        resp_json = response.json()
        self.logger.info("MAKSIM >>>> boards response size:\n%s" % len(resp_json["data"]["boards"]))
        for row in resp_json["data"]["boards"]:
            yield row

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """Convert types."""
        row["id"] = int(row["id"])
        row["description"] = str(row["description"])
        row["tapped_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") # dry calling parent?
        row["board_id"] = row["id"]  # dry calling parent?
        workspace = row["workspace"]

        if (workspace is not None):
            row["workspace_id"] = int(workspace["id"])
            row["workspace_name"] = workspace["name"]
        else:
            row["workspace_id"] = 0
            row["workspace_name"] = ""
        del row["workspace"]

        owner = row.pop("owner")
        row["owner_id"] = owner["id"]
        row["owner_name"] = owner["name"]
        row["owner_email"] = owner["email"]

        return row

class GroupsStream(MondayStream):
    """Loads board groups."""

    name = "groups"
    schema_filepath = SCHEMAS_DIR / "groups.json"

    primary_keys = ["id"]
    replication_key = None

    parent_stream_type = BoardsStream
    ignore_parent_replication_keys = True

    # query = ""

    def prepare_request_payload(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Optional[dict]:
        """Prepare custom query."""
        ctx: dict = cast(dict, context)
        query = f"""
            boards(ids: {ctx["board_id"]}) {{
                groups() {{
                    id
                    title
                    position
                    color
                }}
            }}
        """

        # Using partially `super().prepare_request_payload` code
        # Can't simply set query=... because `context` is not available in the class,
        # only passed into `prepare_request_payload`
        query = "query { " + query + " }"
        request_data = {
            "query": (" ".join([line.strip() for line in query.splitlines()])),
            "variables": {},
        }
        self.logger.debug(f"Attempting query:\n{query}")
        return request_data

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse groups response."""
        resp_json = response.json()
        self.logger.info("MAKSIM >>>> groups response size:\n%s" % len(resp_json["data"]["boards"]))
        for row in resp_json["data"]["boards"]:
            self.logger.info(f"MAKSIM >>>> groups in board response size:\n{len(row)}")
            for group in row["groups"]:
                yield group

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """Convert types."""
        ctx: dict = cast(dict, context)
        row["position"] = float(row["position"])
        row["board_id"] = ctx["board_id"]
        row["tapped_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") # dry calling parent?
        row["group_id"] = row["id"]
        return row

class ItemsStream(MondayStream):
    """Loads items."""

    name = "items"
    schema_filepath = SCHEMAS_DIR / "items.json"
    primary_keys = ["id"]
    replication_key = "updated_at"

    def prepare_request_payload(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Optional[dict]:
        """Prepare custom query."""
        ctx: dict = cast(dict, context)
        query = f"""
            items(limit: {self.config.get("item_limit")}) {{
                id
                name
                state
                created_at
                updated_at
                creator_id
                creator {{
                    email
                    name
                }}
                board {{
                    id
                    name
                }}
                group {{
                    id
                    title
                }}
                parent_item {{
                    id
                }}
            }}
        """

        # DRY
        query = "query { " + query + " }"
        request_data = {
            "query": (" ".join([line.strip() for line in query.splitlines()])),
            "variables": {},
        }
        self.logger.info(f"Attempting query:\n{query}")
        return request_data

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Allow ColumnValuesStream to query by item_id."""
        return {
            "item_id": record["id"],
        }

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse items response."""
        resp_json = response.json()
        self.logger.info("MAKSIM >>>> items response size:\n%s" % len(resp_json["data"]["items"]))
        for row in resp_json["data"]["items"]:
            yield row

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """Add and convert fields."""
        row["id"] = int(row["id"])
        row["creator_id"] = int(row["creator_id"])

        board = row.pop("board")
        row["board_id"] = int(board["id"])
        row["board_name"] = board["name"]

        group = row.pop("group")
        row["group_id"] = group["id"]
        row["group_title"] = group["title"]

        parent_item = row.pop("parent_item")
        row["parent_item_id"] = 0 if parent_item is None else int(parent_item["id"])

        creator = row.pop("creator")
        if (creator is not None):
            row["creator_email"] = creator["email"]
            row["creator_name"] = creator["name"]
        else:
            row["creator_email"] = ""
            row["creator_name"] = ""

        row["tapped_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") # dry calling parent?
        return row

class ColumnsStream(MondayStream):
    """Loads columns."""

    name = "columns"
    schema_filepath = SCHEMAS_DIR / "columns.json"

    primary_keys = ["id"]
    replication_key = None

    parent_stream_type = BoardsStream
    ignore_parent_replication_keys = True

    # query = ""

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        return {
            "board_id": context["board_id"],
        }

    @property
    def query(self) -> str:
        return """
            query ($board_id: [Int]) {
                boards(ids: $board_id) {
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

    # def prepare_request_payload(
    #     self, context: Optional[dict], next_page_token: Optional[Any]
    # ) -> Optional[dict]:
    #     """Prepare custom query."""
    #     ctx: dict = cast(dict, context)
    #     query = f"""
    #         boards(ids: {ctx["board_id"]}) {{
    #             columns {{
    #                 id
    #                 title
    #                 archived
    #                 settings_str
    #                 description
    #                 type
    #                 width
    #             }}
    #         }}
    #     """

    #     # DRY
    #     query = "query { " + query + " }"
    #     request_data = {
    #         "query": (" ".join([line.strip() for line in query.splitlines()])),
    #         "variables": {},
    #     }
    #     self.logger.debug(f"Attempting query:\n{query}")
    #     return request_data

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse groups response."""
        resp_json = response.json()
        self.logger.info("MAKSIM >>>> columns response size:\n%s" % len(resp_json["data"]["boards"]))
        for row in resp_json["data"]["boards"]:
            self.logger.info(f"MAKSIM >>>> columns for board response size:\n{len(row)}")
            for column in row["columns"]:
                yield column

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """Convert types."""
        ctx: dict = cast(dict, context)
        row["board_id"] = ctx["board_id"]
        row["id"] = str(row["board_id"]) + "_" + row["id"]

        if (row["width"] is None):
            row["width"] = 0
        else:
            row["width"] = int(row["width"])

        row["description"] = str(row["description"] )
        row["tapped_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") # dry calling parent?

        return row

class ColumnValuesStream(MondayStream):
    """Loads column values."""

    name = "column_values"
    schema_filepath = SCHEMAS_DIR / "column_values.json"

    primary_keys = ["id"]
    replication_key = None

    # parent_stream_type = ItemsStream
    # ignore_parent_replication_keys = True

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        return {
            "board_limit": self.config.get("board_limit")
        }

    @property
    def query(self) -> str:
        return """
            query ($board_limit: Int!) {
                boards(limit: $board_limit, order_by: created_at) {
                    id
                    items {
                        id
                        column_values {
                            id
                            title
                            text
                            type
                            value
                            additional_info
                        }
                    }
                }
            }
        """

    # def prepare_request_payload(
    #     self, context: Optional[dict], next_page_token: Optional[Any]
    # ) -> Optional[dict]:
    #     """Prepare custom query."""
    #     ctx: dict = cast(dict, context)
    #     query = f"""
    #         items(ids: {ctx["item_id"]}) {{
    #             column_values {{
    #                 id
    #                 title
    #                 text
    #                 value
    #                 type
    #                 additional_info
    #             }}
    #         }}
    #     """

    #     # DRY
    #     query = "query { " + query + " }"
    #     request_data = {
    #         "query": (" ".join([line.strip() for line in query.splitlines()])),
    #         "variables": {},
    #     }
    #     self.logger.debug(f"Attempting query:\n{query}")
    #     return request_data

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse groups response."""
        resp_json = response.json()
        self.logger.info("MAKSIM >>>> column values response size:\n%s" % len(resp_json["data"]["boards"]))
        for row in resp_json["data"]["boards"]:
            self.logger.info(f"MAKSIM >>>> column values for board response size:\n{len(row)}")
            for item in row["items"]:
                self.logger.info(f"MAKSIM >>>> column values for item response size:\n{len(row)}")
                for column_value in item["column_values"]:
                    column_value["board_id"] = row["id"]
                    column_value["item_id"] = item["id"]
                    column_value["id"] = row["id"] + "_" + item["id"] + "_" + column_value["id"]
                    yield column_value

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """Convert types."""
        # ctx: dict = cast(dict, context)
        # row["item_id"] = ctx["item_id"]
        # row["id"] = str(row["item_id"]) + "_" + row["id"]

        if(row["value"] is None):
            row["value"] = ""
        else:
            row["value"] = json.dumps(row["value"])

        if(row["additional_info"] is None):
            row["additional_info"] = ""
        else:
            row["additional_info"] = json.dumps(row["additional_info"])

        row["text"] = str(row["text"])
        row["tapped_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") # dry calling parent?
        return row
