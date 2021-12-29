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
    # Example: {'data': {'boards': [{'name': 'Subitems of Influencer Projects', 'id': '2019183913', 'description': None}]}, 'account_id': 8634050}
    primary_keys = ["id"]
    replication_key = None # update date, DateTimeType
    # graphql_query = ...
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
    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        resp_json = response.json()
        # print("BoardsStream resp_json")
        # print(resp_json)
        for row in resp_json["data"]["boards"]:
            yield row

# boards don't need to have state since the expectation is to grab all or specific ones
# groups need to be grabbed by creation date, don't see any indicator in the API to help with that

class GroupsStream(MondayStream):
    name = "groups"
    schema =  th.PropertiesList(
        th.Property("title", th.StringType),
        th.Property("id", th.StringType),
        th.Property("position", th.NumberType),
        # th.Property("__else__", None)
    ).to_dict()
    query = """
        boards(ids: 1554079540) {
            groups() {
                title
                position
                id
            }
        }
    """
    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        resp_json = response.json()
        # print("GroupsStream resp_json")
        # print(resp_json)
        for row in resp_json["data"]["boards"][0]["groups"]:
            yield row

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
