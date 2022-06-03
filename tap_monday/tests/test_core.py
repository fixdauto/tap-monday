import pytest

from singer_sdk.testing import get_standard_tap_tests

from tap_monday.tap import TapMonday
from tap_monday.streams import BoardsStream, GroupsStream, ItemsStream

SAMPLE_CONFIG = {
    "api_url": "mock://api.monday.test/v2",
    "auth_token": "mytoken",
    "board_limit": 10,
}


def test_tap_standard(
    requests_mock,
    fixture_boards,
    fixture_groups,
    fixture_items,
    fixture_columns,
    fixture_column_values
):
    requests_mock.register_uri(
        "POST",
        SAMPLE_CONFIG["api_url"],
        [
            {"json": fixture_boards, "status_code": 200},
            {"json": fixture_columns, "status_code": 200},
            {"json": fixture_items, "status_code": 200},
            {"json": fixture_column_values, "status_code": 200},
            {"json": fixture_groups, "status_code": 200},
        ],
    )
    tests = get_standard_tap_tests(TapMonday, config=SAMPLE_CONFIG)
    for test in tests:
        test()


def test_board_parsing(fixture_boards):
    tap = TapMonday(config=SAMPLE_CONFIG)
    stream = BoardsStream(tap=tap)
    processed_row = stream.post_process(fixture_boards["data"]["boards"][0])
    assert processed_row["id"] == 2389168662
    assert processed_row["description"] == None


def test_group_parsing(fixture_groups):
    tap = TapMonday(config=SAMPLE_CONFIG)
    stream = GroupsStream(tap=tap)
    processed_row = stream.post_process(
        fixture_groups["data"]["boards"][0]["groups"][0], {"board_id": 2389168662}
    )
    assert processed_row["position"] == 512.0
    assert processed_row["board_id"] == 2389168662

def test_items_parsing(fixture_items):
    tap = TapMonday(config=SAMPLE_CONFIG)
    stream = ItemsStream(tap=tap)
    processed_row = stream.post_process(
        fixture_items["data"]["items"][0]
    )
    assert processed_row["board_id"] == 2389168662
    assert processed_row["parent_item_id"] == 0

# columns
# column values
