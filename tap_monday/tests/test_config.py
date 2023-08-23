"""Streams tests."""

from tap_monday.tap import TapMonday
from tap_monday.streams import BoardsStream

SAMPLE_CONFIG = {
    "api_url": "mock://api.monday.test/v2",
    "auth_token": "mytoken",
    "board_limit": 10,
}

CONFIG_BOARD_IDS_LIST = {**SAMPLE_CONFIG, **{"board_ids": [2580307008, 1903379862]}}
CONFIG_BOARD_IDS_STR = {**SAMPLE_CONFIG, **{"board_ids": "2580307008"}}
CONFIG_BOARD_IDS_STR_LIST = {**SAMPLE_CONFIG, **{"board_ids": "2580307008,1903379862"}}
CONFIG_BOARD_IDS_STR_LIST_SPACE = {
    **SAMPLE_CONFIG,
    **{"board_ids": "2580307008, 1903379862"},
}


def test_board_ids_none():
    tap = TapMonday(config=SAMPLE_CONFIG)
    stream = BoardsStream(tap=tap)
    board_ids = stream.board_ids()
    assert board_ids is None


def test_board_ids_list():
    tap = TapMonday(config=CONFIG_BOARD_IDS_LIST)
    stream = BoardsStream(tap=tap)
    board_ids = stream.board_ids()
    assert board_ids == [2580307008, 1903379862]


def test_board_ids_str():
    tap = TapMonday(config=CONFIG_BOARD_IDS_STR)
    stream = BoardsStream(tap=tap)
    board_ids = stream.board_ids()
    assert board_ids == [2580307008]


def test_board_ids_str_list():
    tap = TapMonday(config=CONFIG_BOARD_IDS_STR_LIST)
    stream = BoardsStream(tap=tap)
    board_ids = stream.board_ids()
    assert board_ids == [2580307008, 1903379862]


def test_board_ids_str_list_space():
    tap = TapMonday(config=CONFIG_BOARD_IDS_STR_LIST_SPACE)
    stream = BoardsStream(tap=tap)
    board_ids = stream.board_ids()
    assert board_ids == [2580307008, 1903379862]
