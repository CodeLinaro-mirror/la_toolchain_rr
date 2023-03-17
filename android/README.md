# Android build scripts for RR

To build rr for Android, run the `build.sh` file in this directory. The builder
assumes that it is run from the [rr-dev tree].

To clone the whole project:

```bash
mkdir rr-dev
cd rr-dev
repo init -c -u https://android.googlesource.com/platform/manifest -b rr-dev
repo sync -c -j8
```

Googlers: use sso://android/platform/manifest as the URL.

[rr-dev tree]:
  https://android.googlesource.com/platform/manifest/+/refs/heads/rr-dev

## Development

For first time set-up, install https://python-poetry.org/, then run
`poetry install` to install the project's dependencies.

This project uses mypy and pylint for linting, as well as black and isort for
auto-formatting. All of these tools will be installed automatically, but you may
want to configure editor integration for them.

To run any of the tools poetry installed, you can either prefix all your
commands with `poetry run` (as in `poetry run pytest`), or you can run
`poetry shell` to enter a shell with all the tools on the `PATH`. The following
instructions assume you've run `poetry shell` first.

To run the linters:

```bash
mypy rrbuild
pylint rrbuild
```

To auto-format the code (though it's best to configure your editor to do this
on save):

```bash
isort .
black .
```
