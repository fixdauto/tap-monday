from singer_sdk.testing import get_standard_tap_tests

from tap_monday.tap import TapMonday
from tap_monday.streams import (
    BoardsStream,
    GroupsStream,
    ItemsStream,
    ColumnsStream,
    ColumnValuesStream,
)

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
    fixture_column_values,
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
    assert processed_row["name"] == "My board"
    assert processed_row["description"] == "My personal board"
    assert processed_row["state"] == "active"
    assert processed_row["updated_at"] == "2022-02-05T00:27:23Z"
    assert processed_row["owner_id"] == 21226602
    assert processed_row["owner_name"] == "Bat Man"
    assert processed_row["owner_email"] == "batman@batman.com"
    assert processed_row["workspace_id"] == 843701
    assert processed_row["workspace_name"] == "Main"


def test_board_parsing_empty_values(fixture_boards_some_empty):
    tap = TapMonday(config=SAMPLE_CONFIG)
    stream = BoardsStream(tap=tap)
    processed_row = stream.post_process(fixture_boards_some_empty["data"]["boards"][0])

    assert processed_row["id"] == 2389168662
    assert processed_row["name"] == "My board"
    assert processed_row["description"] is None
    assert processed_row["state"] == "active"
    assert processed_row["updated_at"] == "2022-02-05T00:27:23Z"
    assert processed_row["owner_id"] == 21226602
    assert processed_row["owner_name"] == "Bat Man"
    assert processed_row["owner_email"] == "batman@batman.com"
    assert processed_row["workspace_id"] == 0
    assert processed_row["workspace_name"] == ""


def test_group_parsing(fixture_groups):
    tap = TapMonday(config=SAMPLE_CONFIG)
    stream = GroupsStream(tap=tap)
    processed_row = stream.post_process(
        fixture_groups["data"]["boards"][0]["groups"][0], {"board_id": 2389168662}
    )

    assert processed_row["board_id"] == 2389168662
    assert processed_row["title"] == "My group name"
    assert processed_row["position"] == 512.0
    assert processed_row["id"] == "new_group23604"
    assert processed_row["color"] == "#fdab3d"
    assert processed_row["archived"] is False
    assert processed_row["deleted"] is False


def test_items_parsing(fixture_items):
    tap = TapMonday(config=SAMPLE_CONFIG)
    stream = ItemsStream(tap=tap)
    processed_row = stream.post_process(fixture_items["data"]["items"][0])

    assert processed_row["board_id"] == 2389168662
    assert processed_row["name"] == "My item name"
    assert processed_row["created_at"] == "2021-10-06T14:31:02Z"
    assert processed_row["updated_at"] == "2021-10-07T14:31:02Z"
    assert processed_row["creator_id"] == 21226602
    assert processed_row["creator_email"] == "batman@batman.com"
    assert processed_row["creator_name"] == "Bat Man"
    assert processed_row["state"] == "active"
    assert processed_row["parent_item_id"] == 2274512420
    assert processed_row["board_id"] == 2389168662
    assert processed_row["board_name"] == "My board"
    assert processed_row["group_id"] == "new_group8875"
    assert processed_row["group_title"] == "My group name"


def test_items_parsing_empty_values(fixture_items_some_empty):
    tap = TapMonday(config=SAMPLE_CONFIG)
    stream = ItemsStream(tap=tap)
    processed_row = stream.post_process(fixture_items_some_empty["data"]["items"][0])

    assert processed_row["id"] == 2274512428
    assert processed_row["name"] == "My item name"
    assert processed_row["created_at"] == "2021-10-06T14:31:02Z"
    assert processed_row["updated_at"] == "2021-10-07T14:31:02Z"
    assert processed_row["creator_id"] == 0
    assert processed_row["creator_email"] == ""
    assert processed_row["creator_name"] == ""
    assert processed_row["state"] == "active"
    assert processed_row["parent_item_id"] == 0
    assert processed_row["board_id"] == 2389168662
    assert processed_row["board_name"] == "My board"
    assert processed_row["group_id"] == "new_group8875"
    assert processed_row["group_title"] == "My group name"


def test_columns_parsing(fixture_columns):
    tap = TapMonday(config=SAMPLE_CONFIG)
    stream = ColumnsStream(tap=tap)
    processed_row = stream.post_process(
        fixture_columns["data"]["boards"][0]["columns"][0],
        {"board_id": fixture_columns["data"]["boards"][0]["id"]},
    )

    assert processed_row["board_id"] == 2389168662
    assert processed_row["id"] == "check"
    assert processed_row["title"] == "Approved"
    assert processed_row["archived"] is False
    assert processed_row["settings_str"] == "{}"
    assert processed_row["description"] is None
    assert processed_row["type"] == "boolean"
    assert processed_row["width"] == 120


def test_column_values_parsing(fixture_column_values):
    tap = TapMonday(config=SAMPLE_CONFIG)
    stream = ColumnValuesStream(tap=tap)
    processed_row = stream.post_process(
        fixture_column_values["data"]["items"][0]["column_values"][0],
        {"item_id": fixture_column_values["data"]["items"][0]["id"]},
    )

    assert processed_row["item_id"] == 2274512428
    assert processed_row["id"] == "status"
    assert processed_row["title"] == "Status"
    assert processed_row["type"] == "color"
    assert processed_row["text"] == "Done"
    assert (
        processed_row["value"] == '"{'
        '\\"index\\":1,'
        '\\"post_id\\":null,'
        '\\"changed_at\\":\\"2022-04-14T19:07:18.872Z\\'
        '"}"'
    )
    assert (
        processed_row["additional_info"] == '"{'
        '\\"label\\":\\"Done\\",'
        '\\"color\\":\\"#00c875\\",'
        '\\"changed_at\\":\\"2022-04-14T19:07:18.872Z\\'
        '"}"'
    )


def test_column_values_parsing_empty_values(fixture_column_values_some_empty):
    tap = TapMonday(config=SAMPLE_CONFIG)
    stream = ColumnValuesStream(tap=tap)
    processed_row = stream.post_process(
        fixture_column_values_some_empty["data"]["items"][0]["column_values"][0],
        {"item_id": fixture_column_values_some_empty["data"]["items"][0]["id"]},
    )

    assert processed_row["item_id"] == 2274512428
    assert processed_row["id"] == "status"
    assert processed_row["title"] == "Status"
    assert processed_row["type"] == "color"
    assert processed_row["text"] == "Done"
    assert processed_row["value"] == ""
    assert processed_row["additional_info"] == ""
