"""Stream type classes for tap-monday."""

import requests

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Iterable, cast

# from singer_sdk import typing as th  # JSON Schema typing helpers

from tap_monday.client import MondayStream

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class BoardsStream(MondayStream):
    """Loads boards."""

    name = "boards"
    # put in ./schemas since it's not dynamic
    # schema = th.PropertiesList(
    #     th.Property("name", th.StringType),
    #     th.Property("id", th.IntegerType),
    #     th.Property("description", th.StringType),
    #     th.Property("state", th.StringType),
    #     th.Property("updated_at", th.DateTimeType),
    # ).to_dict()
    schema_filepath = SCHEMAS_DIR / "boards.json"

    primary_keys = ["id"]
    replication_key = "updated_at"
    # updated_at, DateTimeType, ISO 8601 / RFC3339, 2022-01-07T15:56:08Z

    @property
    def query(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        # print(self.config["api_url"])
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
            }}
        """

    # might be limited to 25, might need to pageInt and order_by: created_at
    # paginate - not clear total number of pages
    # or selected ids: boards(ids: [1, 2, 3]) { ... }
    # state.json for partial extraction, after specific date if possible
    # query {
    #   boards {
    #     workspace {
    #       id
    #       name
    #       kind
    #       description
    #     }
    #   }
    # }

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Allow GroupsStream to query by board_id."""
        # print(f'get_child_context context {context}')
        # print(f'record id {record["id"]}')
        return {
            "board_id": record["id"],
        }

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse boards response."""
        resp_json = response.json()
        # print("BoardsStream resp_json")
        # print(resp_json)
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
        return row

    # To paginate form query in prepare_request_payload and get_next_page_token
    # Monday returns "boards:[]" when out of pages


# is it possible to get only "newly created" boards,
# what about renamed boards?
# groups need to be grabbed by creation date,
# don't see any indicator in the API to help with that


class GroupsStream(MondayStream):
    """Loads board groups."""

    name = "groups"
    schema_filepath = SCHEMAS_DIR / "groups.json"

    primary_keys = ["id"]
    replication_key = None  # update date, DateTimeType

    parent_stream_type = BoardsStream
    ignore_parent_replication_keys = True

    query = ""

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
        # self.query = ...
        # super().prepare_request_payload ... doesn't get new query value
        query = "query { " + query + " }"
        # query = query.lstrip()
        request_data = {
            "query": (" ".join([line.strip() for line in query.splitlines()])),
            "variables": {},
        }
        self.logger.debug(f"Attempting query:\n{query}")
        return request_data

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse groups response."""
        resp_json = response.json()
        # print("GroupsStream resp_json")
        # print(resp_json)
        for row in resp_json["data"]["boards"][0]["groups"]:
            yield row

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """Convert types."""
        ctx: dict = cast(dict, context)
        row["position"] = float(row["position"])
        row["board_id"] = ctx["board_id"]
        row["tapped_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") # dry calling parent?
        row["group_id"] = row["id"]
        return row


# class ItemsStream(MondayStream):
#     name = "items"
#     schema =  th.PropertiesList(
#         th.Property("title", th.StringType),
#         th.Property("id", th.StringType),
#         th.Property("position", th.NumberType)
#     ).to_dict()

class ItemsStream(MondayStream):
    """Loads items."""

    name = "items"
    schema_filepath = SCHEMAS_DIR / "items.json"

    primary_keys = ["id"]
    replication_key = "updated_at"

    # query = ""

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
            }}
        """

        # self.query = ...
        # super().prepare_request_payload ... doesn't get new query value
        query = "query { " + query + " }"
        # query = query.lstrip()
        request_data = {
            "query": (" ".join([line.strip() for line in query.splitlines()])),
            "variables": {},
        }
        self.logger.info(f"Attempting query:\n{query}")
        return request_data

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse items response."""
        resp_json = response.json()
        # print("ItemsStream resp_json")
        # print(resp_json)
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
        creator = row.pop("creator")
        if (creator is not None):
            row["creator_email"] = creator["email"]
            row["creator_name"] = creator["name"]
        else:
            row["creator_email"] = ""
            row["creator_name"] = ""
        row["tapped_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") # dry calling parent?
        return row

# class ColumnValuesStream(MondayStream):
#     name = "comlumn_values"
#     schema =  th.PropertiesList(
#         th.Property("title", th.StringType),
#         th.Property("id", th.StringType),
#         th.Property("position", th.NumberType)
#     ).to_dict()


