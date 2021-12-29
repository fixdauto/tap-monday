# tap-monday

`tap-monday` is a Singer tap for Monday.com.

Built with the [Meltano Tap SDK](https://sdk.meltano.com) for Singer Taps.

## Installation

- [ ] `Developer TODO:` Update the below as needed to correctly describe the install procedure. For instance, if you do not have a PyPi repo, or if you want users to directly install from your git repo, you can modify this step as appropriate.

```bash
pipx install tap-monday
```

## Configuration

### Accepted Config Options

- [ ] `Developer TODO:` Provide a list of config options accepted by the tap.

A full list of supported settings and capabilities for this
tap is available by running:

```bash
tap-monday --about
```

```
{
  "api_url": "https://api.monday.com/v2",
  "auth_token": "yourauthenticationtoken"
}
```

### Executing the Tap Directly

```bash
tap-monday --version
tap-monday --help
tap-monday --config CONFIG --discover > ./catalog.json
```

## Developer Resources

- [ ] `Developer TODO:` As a first step, scan the entire project for the text "`TODO:`" and complete any recommended steps, deleting the "TODO" references once completed.

### Initialize your Development Environment

```bash
pipx install poetry
poetry install
```

### Create and Run Tests

Create tests within the `tap_monday/tests` subfolder and
  then run:

```bash
poetry run pytest
```

You can also test the `tap-monday` CLI interface directly using `poetry run`:

```bash
poetry run tap-monday --help
```

