"""Stream type classes for tap-monday."""

import requests

from pathlib import Path
from typing import Any, Dict, Optional, Union, List, Iterable

from singer_sdk import typing as th  # JSON Schema typing helpers

from tap_monday.client import MondayStream

# TODO: Delete this is if not using json files for schema definition
SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")
# TODO: - Override `UsersStream` and `GroupsStream` with your own stream definition.
#       - Copy-paste as many times as needed to create multiple stream types.

class BoardsStream(MondayStream):
    name = "boards"
    # actually put in ./schemas since it's not dynamic
    schema = th.PropertiesList(
        th.Property("name", th.StringType),
        th.Property("id", th.IntegerType),
        th.Property("description", th.StringType),
        # th.Property("__else__", None)
    ).to_dict()

    primary_keys = ["id"]
    replication_key = None # update date, DateTimeType
    query = """
        boards(limit: 3) {
                name
                id
                description
            }
    """
    # More fields from https://api.developer.monday.com/docs/boards
    # updated_at ISO8601DateTime, singer needs RFC3339 2017-01-01T00:00:00Z
    # workspace_id
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
        # print('get_child_context')
        # print(f'context {context}')
        # print(f'record id {record["id"]}')
        return {
            "board_id": record["id"],
        }

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        resp_json = response.json()
        # print("BoardsStream resp_json")
        # print(resp_json)
        for row in resp_json["data"]["boards"]:
            yield row

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        row["id"] = int(row["id"])
        return row

# is it possible to get only "newly created" boards, what about renamed boards?
# groups need to be grabbed by creation date, don't see any indicator in the API to help with that

class GroupsStream(MondayStream):
    name = "groups"
    schema =  th.PropertiesList(
        th.Property("title", th.StringType),
        th.Property("id", th.StringType),
        th.Property("position", th.NumberType),
        # th.Property("__else__", None)
    ).to_dict()

    replication_key = None # update date, DateTimeType

    parent_stream_type = BoardsStream
    ignore_parent_replication_keys = True

    # boards(ids: 1554079540) {
    # print(f'requests: {requests}')
    # print(f'context: {context}')
    # print(f'board_id: {board_id}')
    query = ""

    def prepare_request_payload(self, context: Optional[dict], next_page_token: Optional[Any]) -> Optional[dict]:
        query = f"""
            boards(ids: {context["board_id"]}) {{
                groups() {{
                    title
                    position
                    id
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
        resp_json = response.json()
        # print("GroupsStream resp_json")
        # print(resp_json)
        for row in resp_json["data"]["boards"][0]["groups"]:
            yield row

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        row["position"] = float(row["position"])
        return row

# class ItemsStream(MondayStream):
#     name = "items"
#     schema =  th.PropertiesList(
#         th.Property("title", th.StringType),
#         th.Property("id", th.StringType),
#         th.Property("position", th.NumberType)
#     ).to_dict()

# class ColumnValuesStream(MondayStream):
#     name = "comlumn_values"
#     schema =  th.PropertiesList(
#         th.Property("title", th.StringType),
#         th.Property("id", th.StringType),
#         th.Property("position", th.NumberType)
#     ).to_dict()

# class UsersStream(MondayStream):
#     """Define custom stream."""
#     name = "users"
#     # Optionally, you may also use `schema_filepath` in place of `schema`:
#     # schema_filepath = SCHEMAS_DIR / "users.json"
#     schema = th.PropertiesList(
#         th.Property("name", th.StringType),
#         th.Property(
#             "id",
#             th.StringType,
#             description="The user's system ID"
#         ),
#         th.Property(
#             "age",
#             th.IntegerType,
#             description="The user's age in years"
#         ),
#         th.Property(
#             "email",
#             th.StringType,
#             description="The user's email address"
#         ),
#         th.Property(
#             "address",
#             th.ObjectType(
#                 th.Property("street", th.StringType),
#                 th.Property("city", th.StringType),
#                 th.Property(
#                     "state",
#                     th.StringType,
#                     description="State name in ISO 3166-2 format"
#                 ),
#                 th.Property("zip", th.StringType),
#             )
#         ),
#     ).to_dict()
#     primary_keys = ["id"]
#     replication_key = None
#     graphql_query = """
#         users {
#             name
#             id
#             age
#             email
#             address {
#                 street
#                 city
#                 state
#                 zip
#             }
#         }
#         """


# class GroupsStream(MondayStream):
#     """Define custom stream."""
#     name = "groups"
#     schema = th.PropertiesList(
#         th.Property("name", th.StringType),
#         th.Property("id", th.StringType),
#         th.Property("modified", th.DateTimeType),
#     ).to_dict()
#     primary_keys = ["id"]
#     replication_key = "modified"
#     graphql_query = """
#         groups {
#             name
#             id
#             modified
#         }
#         """
