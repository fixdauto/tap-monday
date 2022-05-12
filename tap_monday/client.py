"""GraphQL client handling, including MondayStream base class."""

import requests
from typing import Any, Optional, Iterable, Callable, Generator
import backoff
from datetime import datetime, timezone

from singer_sdk.streams import GraphQLStream
from singer_sdk.exceptions import FatalAPIError, RetriableAPIError

class MondayStream(GraphQLStream):
    """Monday stream class."""

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        return self.config["api_url"]

    @property
    def http_headers(self) -> dict:
        """Authorise requests."""
        headers = {}
        headers["Authorization"] = self.config["auth_token"]
        headers["Content-Type"] = "application/json"
        headers["User-Agent"] = "Meltano"
        return headers

    def get_next_page_token(
        self, response: requests.Response, previous_token: Optional[Any]
    ) -> Any:
        """Returns the number of the next page."""
        self.logger.info("MAKSIM self.name: %s" % self.name)
        if self.name == 'items':
            limit_per_page = self.config["item_limit"]
        elif self.name == 'boards':
            limit_per_page = self.config["board_limit"]
        else:
            return None 
            # All other objects are queried by parent IDs

        self.logger.info("MAKSIM limit_per_page: %s" % limit_per_page)
        self.logger.info("MAKSIM data len: %s" % len(response.json()["data"][self.name]))
        self.logger.info("MAKSIM data previous_token: %s" % previous_token)
        current_page = previous_token if previous_token is not None else 1
        self.logger.info("MAKSIM data current_page: %s" % current_page)
        if len(response.json()["data"][self.name]) == limit_per_page:
            next_page_token = current_page + 1
        else:
            next_page_token = None
        self.logger.info("MAKSIM 2 data next_page_token: %s" % next_page_token)
        next_page_token = None if next_page_token == 5 else next_page_token
        return next_page_token

    # @property
    # def query(self) -> str:
    #     """Satisfy SDK complains. It's actually used only in child streams."""
    #     return ""

    def validate_response(self, response: requests.Response) -> None:
        """Check response for errors.

        Gracefully handles rate limits.

        """
        if response.status_code == 429: # Rate limit error
            msg = (
                f"{response.status_code} Server Error: "
                f"{response.reason}"
            )
            raise RetriableAPIError(msg)
        elif 400 <= response.status_code < 500:
            msg = (
                f"{response.status_code} Client Error: "
                f"{response.reason}"
            )
            raise FatalAPIError(msg)
        elif 500 <= response.status_code < 600:
            msg = (
                f"{response.status_code} Server Error: "
                f"{response.reason}"
            )
            raise RetriableAPIError(msg)

    def request_decorator(self, func: Callable) -> Callable:
        """Handle custom backoff.

        Exact copy from RESTStream so other methods can be overriden.
        
        """
        decorator: Callable = backoff.on_exception(
            self.backoff_wait_generator,
            (
                RetriableAPIError,
                requests.exceptions.ReadTimeout,
            ),
            max_tries=self.backoff_max_tries,
            on_backoff=self.backoff_handler,
        )(func)
        return decorator

    def backoff_handler(self, details: dict) -> None:
        """Log backoff status."""
        self.logger.error(
            "Backing off {wait:0.1f} seconds after {tries} tries "
            "calling function {target} with args {args} and kwargs "
            "{kwargs}".format(**details)
        )

    def backoff_wait_generator(self) -> Callable[..., Generator[int, Any, None]]:
        """Repeat in 70 seconds since Monday.com GraphQL limits are inforced per minute."""
        return backoff.constant(interval=70)

    def backoff_max_tries(self) -> int:
        """Try 3 times. More than that should require human investigation."""
        return 3

    def tapped_at(self) -> str: # what if no self?
        """Format current time for streams."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
