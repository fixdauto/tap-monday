# tap-monday

`tap-monday` is a Singer tap for Monday.com.

Built with the [Meltano Tap SDK](https://sdk.meltano.com) for Singer Taps.

## Install in Meltano

```
meltano install extractor tap-monday
meltano invoke tap-monday
meltano elt tap-monday your-target
```

## Config Examples

### Tap

```
{
  "api_url": "https://api.monday.com/v2",
  "auth_token": "yourauthenticationtoken",
  "board_limit": 10, # limit per page
  "item_limit": 10, # limit per page
  "column_value_limit": 10 # limit per page for items, then the tap grabs all the column values for the selected items
}
```

### Meltano

In meltano.yml:

```
plugins:
  extractors:
...
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
      decription: Authentication token you should generate in your monday.com acccunt.
        Look under Admin setting.
    - name: api_url
      kind: string
      value: https://api.monday.com/v2
      label: Monday.com web-API endpoint
      description: Monday.com web-API endpoint URL
    - name: board_limit
      kind: integer
      value: 50
      label: Maximum number of boards to return per page/query
      description: Maximum number of boards to return per page/query.
    - name: item_limit
      kind: integer
      value: 500
      label: Maximum number of items to return per page/query
      description: Maximum number of items to return per page/query. Per documentation, Item queries are limited to 1 per 2 minutes. It's possible to make them faster if they are not run back-to-back. It can be achieved setting max_batch_rows to a value less than item_limit causes Meltano to spend some time inserting values in a database and slow down query rate enough to avoid hitting rate limits.
    - name: column_value_limit
      kind: integer
      value: 200
      label: Maximum number of items to return per page/query in column value query
      description: Column values is a child object of items. So this value limits number of items per page while query is going to return all the column values for the items. The same rules apply here as for the item_limit.
    select:
    - boards.*
    - items.*
    - columns.*
    - groups.*
    - column_values.*
    metadata:
      boards:
        replication-method: INCREMENTAL
        replication-key: updated_at
      items:
        replication-method: INCREMENTAL
        replication-key: updated_at
```


With [target-snowflake](https://github.com/fixdauto/target-snowflake) and under 4GB total RAM use these settings for the loader so the process won't exceed the available memory:
```
loaders:
...
  - name: target-snowflake
    pip_url: git+https://github.com/fixdauto/target-snowflake@fixd
...
    config:
...
      max_batch_rows: 250
```
Low max_batch_rows work well with low rate limits because Meltano spends some time inserting values between API calls.


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
poetry run pydocstyle tap_monday
poetry run mypy tap_monday
poetry run black
poetry run flake8 tap_monday
poetry run pytest
```

## Limitations

Monday.com API in most cases doesn't have record timestamps neither a way to query by timestamps. So full dataset is being queried on every run.

The tap adds tapped_at field so it's easier to track down the line (in Meltano) when records were added or updated.
