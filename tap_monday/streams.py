"""Stream type classes for tap-monday."""

import requests
import json
import hashlib

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
    replication_key = "updated_at" # ISO8601/RFC3339, example: 2022-01-07T15:56:08Z
    # records_jsonpath = "$.records[*]"
    # records_jsonpath: str = "$.data.boards[0].groups[*]"

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        return {
            "page": next_page_token or 1,
            "board_limit": self.config["board_limit"]
        }

    @property
    def query(self) -> str:
        """Form Boards query"""
        return """
            query Boards($board_limit: Int!, $page: Int!) {
                boards(
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

    # def get_next_page_token(
    #     self, response: requests.Response, previous_token: Optional[Any]
    # ) -> Any:
    #     self.logger.info("MAKSIM self.name: %s" % self.name)
    #     self.logger.info("MAKSIM data len: %s" % len(response.json()["data"][self.name]))
    #     self.logger.info("MAKSIM data previous_token: %s" % previous_token)
    #     current_page = previous_token if previous_token is not None else 1
    #     self.logger.info("MAKSIM data current_page: %s" % current_page)
    #     if len(response.json()["data"][self.name]) == self.config["board_limit"]:
    #         next_page_token = current_page + 1
    #     else:
    #         next_page_token = None
    #     self.logger.info("MAKSIM data next_page_token: %s" % next_page_token)
    #     next_page_token = None if next_page_token == 3 else next_page_token
    #     return next_page_token

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Allow GroupsStream to query by board_id."""
        return {
            "board_id": record["id"], # does it need int(record["id"])
        }

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse boards response."""
        resp_json = response.json()
        for row in resp_json["data"]["boards"]:
            yield row

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """Convert types."""
        row["id"] = int(row["id"])
        # row["description"] = str(row["description"])
        row["tapped_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") # dry calling parent?
        row["board_id"] = row["id"]  # dry calling parent?
        workspace = row.pop("workspace")

        if (workspace is not None):
            row["workspace_id"] = int(workspace["id"])
            row["workspace_name"] = workspace["name"]
        else:
            row["workspace_id"] = 0
            row["workspace_name"] = ""
        # del row["workspace"]

        owner = row.pop("owner")
        row["owner_id"] = owner["id"]
        row["owner_name"] = owner["name"]
        row["owner_email"] = owner["email"]

        return row
        # return {**row, "board_id": context["board_id"]}

class GroupsStream(MondayStream):
    """Loads board groups."""

    name = "groups"
    schema_filepath = SCHEMAS_DIR / "groups.json"

    primary_keys = ["id", "board_id"]
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
                groups {{
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
        return request_data

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse groups response."""
        resp_json = response.json()
        for row in resp_json["data"]["boards"]:
            for group in row["groups"]:
                yield group

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """Convert types."""
        ctx: dict = cast(dict, context)
        row["position"] = float(row["position"])
        row["board_id"] = ctx["board_id"]
        row["tapped_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") # dry calling parent?
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
            items(limit: {self.config["item_limit"]}) {{
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
        return request_data

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Allow ColumnValuesStream to query by item_id."""
        return {
            "item_id": record["id"],
        }

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse items response."""
        resp_json = response.json()
        for row in resp_json["data"]["items"]:
            yield row

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """Add and convert fields."""
        row["id"] = int(row["id"])
        row["item_id"] = int(row["id"])
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

    primary_keys = ["id", "board_id"]
    replication_key = None

    parent_stream_type = BoardsStream
    ignore_parent_replication_keys = True

    # query = ""

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        return {
            "board_ids": context["board_id"],
        }
        # return {
        #     "board_limit": self.config.get("board_limit")
        # }

    # @property
    # def query(self) -> str:
    #     return """
    #         query($board_limit: Int!) {
    #             boards(limit: $board_limit) {
    #                 id
    #                 columns {
    #                     id
    #                     title
    #                     archived
    #                     settings_str
    #                     description
    #                     type
    #                     width
    #                 }    
    #             }
    #         }
    #     """

    @property
    def query(self) -> str:
        return """
            query($board_ids: [Int]) {
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

    # def prepare_request_payload(
    #     self, context: Optional[dict], next_page_token: Optional[Any]
    # ) -> Optional[dict]:
    #     """Prepare custom query."""
    #     ctx: dict = cast(dict, context)
    #     query = f"""
    #         boards(ids: {ctx["board_id"]}) {{
    #             id
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
    #     return request_data

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse groups response."""
        resp_json = response.json()
        for row in resp_json["data"]["boards"]:
            for column in row["columns"]:
                # column["board_id"] = int(row["id"])
                # column["id"] = str(column["board_id"]) + "_" + column["id"]
                yield column

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """Convert types."""
        ctx: dict = cast(dict, context)
        row["board_id"] = ctx["board_id"]
        # row["id"] = str(row["board_id"]) + "_" + row["id"]
        # row["id"] = int(hashlib.sha256((str(row["board_id"]) + row["id"]).encode('utf-8')).hexdigest(), 16) % 10**8
        # if (row["width"] is None):
        #     row["width"] = 0
        # else:
        #     row["width"] = int(row["width"])
        # row["description"] = str(row["description"])
        row["tapped_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") # dry calling parent?
        return row
        # return {**row, "board_id": context["board_id"]}

class ColumnValuesStream(MondayStream):
    """Loads column values."""

    name = "column_values"
    schema_filepath = SCHEMAS_DIR / "column_values.json"

    primary_keys = ["id", "item_id"]
    replication_key = None

    parent_stream_type = ItemsStream
    ignore_parent_replication_keys = True

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        # return {
        #     "board_limit": self.config.get("board_limit")
        # }
        return {
            "item_ids": context["item_id"]
        }

    # That exceeds what Monday.com can respond to.
    # Whether it explicitly rejects it saying that it's too many records to ask at one time
    # or it never responds at all.
    # @property
    # def query(self) -> str:
    #     return """
    #         query($board_limit: Int!) {
    #             boards(limit: $board_limit, order_by: created_at) {
    #                 id
    #                 items {
    #                     id
    #                     column_values {
    #                         id
    #                         title
    #                         text
    #                         type
    #                         value
    #                         additional_info
    #                     }
    #                 }
    #             }
    #         }
    #     """

    @property
    def query(self) -> str:
        return """
            query ($item_ids: [Int]) {
                items (ids: $item_ids) {
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
    #     return request_data

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse groups response."""
        resp_json = response.json()
        for row in resp_json["data"]["items"]:
            for column_value in row["column_values"]:
                # column_value["item_id"] = row["id"]
                # column_value["id"] = row["id"] + "_" + column_value["id"]
                yield column_value

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """Convert types."""
        ctx: dict = cast(dict, context)
        row["item_id"] = ctx["item_id"]
        # row["id"] = str(row["item_id"]) + "_" + row["id"]

        if(row["value"] is None):
            row["value"] = ""
        else:
            row["value"] = json.dumps(row["value"])

        if(row["additional_info"] is None):
            row["additional_info"] = ""
        else:
            row["additional_info"] = json.dumps(row["additional_info"])

        # row["text"] = str(row["text"])
        row["tapped_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") # dry calling parent?
        return row
