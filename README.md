# tap-monday

`tap-monday` is a Singer tap for Monday.com.

Built with the [Meltano Tap SDK](https://sdk.meltano.com) for Singer Taps.

## Install in Meltano

In meltano.yml:

```
plugins:
  extractors:
  - name: tap-monday
    namespace: tap_monday
    pip_url: git+https://github.com/fixdauto/tap-monday.git
    executable: tap-monday
    capabilities:
    - discover
    - state
    - catalog
    settings:
    - name: auth_token
      env: MONDAY_AUTH_TOKEN
      kind: password
      label: Authentication Token
      documentation: https://support.monday.com/hc/en-us/articles/360005144659-Does-monday-com-have-an-API-
      decription: Authentication token you should generate in your monday.com acccount.
        Look under Admin setting.
    - name: api_url
      kind: string
      value: https://api.monday.com/v2
      label: Monday.com web-API endpoint
      description: Monday.com web-API endpoint URL
    - name: board_limit
      kind: integer
      value: 1000
      label: Maximum number of boards to return
      description: Usually accounts don't have that many boards to bother with pagination.
        Setting limit to high enough value returns all the boards anyway.
    - name: item_limit
      kind: integer
      value: 1000
      label: Maximum number of items to return
      description: Usually Monday.com have more items than boards. Try a high value to see if you get all the items without pagination.
    select:
    - boards.name
    - boards.updated_at
    metadata:
      boards:
        replication-method: INCREMENTAL
        replication-key: updated_at
```

```
meltano install extractor tap-monday
meltano invoke tap-monday
meltano elt tap-monday your-target
```

## Config Example

```
{
  "api_url": "https://api.monday.com/v2",
  "auth_token": "yourauthenticationtoken",
  "board_limit": 10, # limit per page/query, it will query all pages
  "item_limit": 10 # limit per page/query, it will query all pages
}
```

Meltano extractor configuration example is in `meltano.yml`

## When you change the code

Setup
```
git clone
cd tap-monday
poetry install
```

Manual check, use the config from above
```
poetry run tap-monday --config ../tap-monday-config.json --test
poetry run tap-monday --config ../tap-monday-config.json
```

Test and lint before committing. It should pass MyPy, Black, Falke8 and PyDocStyle.
```
poetry run pytest
poetry run mypy tap_monday
poetry run black
poetry run flake8 tap_monday
poetry run pydocstyle tap_monday
```

## Limitations

Monday.com API in most cases doesn't have record timestamps neither a way to query by timestamps. So full dataset is being queried on every run.

The tap adds tapped_at field so it's easier to track down the line (in Meltano) when records were added or updated.
