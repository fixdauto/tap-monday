import pytest

@pytest.fixture
def fixture_boards():
    return {
        "data": {
            "boards": [
                {
                    "name": "My board",
                    "id": "2389168662",
                    "description": "My personal board",
                    "state": "active",
                    "updated_at": "2022-02-05T00:27:23Z",
                    "owner": {
                        "id": 21226602,
                        "name": "Bat Man",
                        "email": "batman@batman.com",
                    },
                    "workspace": {
                        "id": 843701,
                        "name": "Main",
                        "kind": None,
                        "description": None,
                    }
                }
            ]
        }
    }


@pytest.fixture
def fixture_boards_some_empty():
    return {
        "data": {
            "boards": [
                {
                    "name": "My board",
                    "id": "2389168662",
                    "description": None,
                    "state": "active",
                    "updated_at": "2022-02-05T00:27:23Z",
                    "owner": {
                        "id": 21226602,
                        "name": "Bat Man",
                        "email": "batman@batman.com"
                    },
                    "workspace": None,
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
                    "id": "2389168662",
                    "groups": [
                        {
                            "title": "My group name",
                            "position": "512.0",
                            "id": "new_group23604",
                            "color": "#fdab3d",
                            "archived": False,
                            "deleted": False,
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
            "items": [
                {
                    "id": 2274512428,
                    "name": "My item name",
                    "created_at": "2021-10-06T14:31:02Z",
                    "updated_at": "2021-10-07T14:31:02Z",
                    "creator_id": 21226602,
                    "creator": {
                        "email": "batman@batman.com",
                        "name": "Bat Man",
                    },
                    "state": "active",
                    "parent_item": {
                        "id": 2274512420,
                    },
                    "board": {
                        "id": "2389168662",
                        "name": "My board",
                    },
                    "group": {
                        "title": "My group name",
                        "id": "new_group8875",
                    },
                }
            ],
        }
    }

@pytest.fixture
def fixture_items_some_empty():
    return {
        "data": {
            "items": [
                {
                    "id": 2274512428,
                    "name": "My item name",
                    "created_at": "2021-10-06T14:31:02Z",
                    "updated_at": "2021-10-07T14:31:02Z",
                    "creator_id": 0,
                    "creator": None,
                    "state": "active",
                    "parent_item": None,
                    "board": {
                        "id": "2389168662",
                        "name": "My board",
                    },
                    "group": {
                        "title": "My group name",
                        "id": "new_group8875",
                    },
                }
            ],
        }
    }


@pytest.fixture
def fixture_columns():
    return {
        "data": {
            "boards": [
                {
                    "id": 2389168662,
                    "columns": [
                        {
                            "id": "check",
                            "title": "Approved",
                            "archived": False,
                            "settings_str": "{}",
                            "description": None,
                            "type": "boolean",
                            "width": 120,
                        }
                    ],
                }
            ],
        }
    }


@pytest.fixture
def fixture_column_values():
    return {
        "data": {
            "items": [
                {
                    "id": 2274512428,
                    "column_values": [
                        {
                            "id": "status",
                            "title": "Status",
                            "type": "color",
                            "value": '{"index":1,"post_id":null,"changed_at":"2022-04-14T19:07:18.872Z"}',
                            "text": "Done",
                            "additional_info": '{"label":"Done","color":"#00c875","changed_at":"2022-04-14T19:07:18.872Z"}',
                        }
                    ],
                }
            ],
        }
    }


@pytest.fixture
def fixture_column_values_some_empty():
    return {
        "data": {
            "items": [
                {
                    "id": 2274512428,
                    "column_values": [
                        {
                            "id": "status",
                            "title": "Status",
                            "type": "color",
                            "value": None,
                            "text": "Done",
                            "additional_info": None,
                        }
                    ],
                }
            ],
        }
    }
