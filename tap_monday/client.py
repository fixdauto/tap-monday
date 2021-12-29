"""GraphQL client handling, including MondayStream base class."""

import requests
from pathlib import Path
from typing import Any, Dict, Optional, Union, List, Iterable

from singer_sdk.streams import GraphQLStream


class MondayStream(GraphQLStream):
    """Monday stream class."""

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        # print(self.config["api_url"])
        return self.config["api_url"]

    # Alternatively, use a static string for url_base:
    # url_base = "https://api.mysample.com"

    @property
    def http_headers(self) -> dict:
        headers = {}
        # print(self.config.get("auth_token"))
        headers["Authorization"] = self.config.get("auth_token")
        headers["Content-Type"]  = self.config.get("application/json")
        if "user_agent" in self.config:
            headers["User-Agent"] = self.config.get("user_agent")
        # If not using an authenticator, you may also provide inline auth headers:
        # headers["Private-Token"] = self.config.get("auth_token")
        return headers

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        resp_json = response.json()
        # print("MondayStream resp_json")
        # print(resp_json)
        for row in resp_json["data"]:
            yield row
        # dry? parent.parse_response(..., depth: '[0]["groups"]')

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """As needed, append or transform raw data to match expected structure."""
        # TODO: Delete this method if not needed.
        return row

    @property
    def query(self) -> str:
        graphql_query="""
            me {
                id
                name
                email
                is_admin
                created_at
                join_date
                account {
                    name
                    id
                }
            }
        """
        return graphql_query

    # def validate_response(self, response):
    #     # Still catch error status codes
    #     super().validate_response(response)

    #     data = response.json()
    #     if data["status"] == "ERROR":
    #         raise FatalAPIError("Error message found :(")
    #     if data["status"] == self."UNAVAILABLE":
    #         raise RetriableAPIError("API is unavailable")
