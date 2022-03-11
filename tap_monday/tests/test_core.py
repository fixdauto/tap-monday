import pytest

from singer_sdk.testing import get_standard_tap_tests

from tap_monday.tap import TapMonday
from tap_monday.streams import BoardsStream, GroupsStream

SAMPLE_CONFIG = {
    "api_url": "mock://api.monday.test/v2",
    "auth_token": "mytoken",
    "board_limit": 10,
}


@pytest.fixture
def fixture_boards():
    return {
        "data": {
            "boards": [
                {
                    "name": "My board name",
                    "id": "2389168662",
                    "description": None,
                    "state": "active",
                    "updated_at": "2022-02-05T00:27:23Z",
                }
            ]
        }
    }


@pytest.fixture
def fixture_groups():
    return {
        "data": {
            "boards": [
                {
                    "groups": [
                        {
                            "title": "My group name",
                            "position": "512.0",
                            "id": "new_group23604",
                        }
                    ]
                }
            ]
        }
    }


@pytest.fixture
def fixture_items():
    return {
        "data": {
            "boards": [
                {
                    "groups": [
                        {
                            "title": "My group name",
                            "position": "65536.0",
                            "id": "new_group8875",
                            "items": [
                                {
                                    "name": "My item name",
                                    "created_at": "2021-10-07T14:31:02Z",
                                    "column_values": [
                                        {
                                            "id": "subitems",
                                            "title": "Subitems",
                                            "type": "subtasks",
                                            "value": None,
                                            "text": "",
                                        }
                                    ],
                                }
                            ],
                        }
                    ]
                }
            ]
        }
    }


def test_tap_standard(requests_mock, fixture_boards, fixture_groups, fixture_items):
    requests_mock.register_uri(
        "POST",
        SAMPLE_CONFIG["api_url"],
        [
            {"json": fixture_boards, "status_code": 200},
            {"json": fixture_groups, "status_code": 200},
            {"json": fixture_items, "status_code": 200},
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
    assert processed_row["description"] == "None"


def test_group_parsing(fixture_groups):
    tap = TapMonday(config=SAMPLE_CONFIG)
    stream = GroupsStream(tap=tap)
    processed_row = stream.post_process(
        fixture_groups["data"]["boards"][0]["groups"][0], {"board_id": 2389168662}
    )
    assert processed_row["position"] == 512.0
    assert processed_row["board_id"] == 2389168662
