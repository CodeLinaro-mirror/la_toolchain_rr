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

## Updating

Updating rr and its dependencies is automated by [external_updater]. The tool
itself is hosted in AOSP, so you'll need an AOSP platform tree (see
https://source.android.com/docs/setup/download/downloading if you don't already
have one) to run the updater. Assuming your AOSP platform tree's root directory
is `$AOSP`, run (from the root of your rr-dev tree):

```bash
$AOSP/tools/external_updater/updater.sh update --no-build \
  `realpath toolchain/rr`
```

TODO: capnproto should also be updated, but external_updater crashes on that
project, file a bug

There is no automated testing of rr for Android. To smoke test the update, run
(from the root of your rr-dev tree):

```bash
./toolchain/rr/android.build.sh
adb push out/rr/bin/rr /data/local/tmp/
adb push out/android-install/lib/*.so /data/local/tmp/
adb shell "LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/rr"
```

Note that rr is currently only supported for x86_64 Android. You will need to
use an emulator or a cuttlefish device.

[external_updater]: https://android.googlesource.com/platform/tools/external_updater/

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
