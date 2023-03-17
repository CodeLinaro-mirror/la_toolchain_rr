#
# Copyright (C) 2023 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Builder for rr and its dependencies."""
import logging
import os
import shutil
from pathlib import Path

from rrbuild.paths import DIST_DIR, OUT_DIR

from .cmake import HostLinuxCMakeBuilder, NdkCMakeBuilder
from .toolchain import HostLinuxToolchain, NdkToolchain


class Builder:
    """Builder for rr and its dependencies."""

    def __init__(self, top_dir: Path, build_id: str) -> None:
        self.top_dir = top_dir
        self.build_id = build_id

    def build(self) -> None:
        """Builds and packages rr.

        This also builds rr's dependencies: the capnproto compiler for the host and the
        capnproto libraries for Android.
        """
        host_install_dir = OUT_DIR / "host-install"
        android_install_dir = OUT_DIR / "android-install"

        # Build capnproto for the host. We need the proto compiler.
        host_toolchain = HostLinuxToolchain()
        HostLinuxCMakeBuilder(
            self.top_dir / "toolchain/capnproto/c++",
            OUT_DIR / "capnproto",
            host_install_dir,
            host_toolchain,
            additional_env={
                # The capnproto compiler is linked against the libc++ from the
                # toolchain, and the compiler is run during the build. libc++ isn't
                # copied to the out or install directory, so the RUNPATH won't work.
                "LD_LIBRARY_PATH": os.pathsep.join(
                    str(p) for p in host_toolchain.runtime_library_paths
                )
            },
        ).build({"WITH_OPENSSL": "OFF"}, install=True)

        # Build again for the device, where we need the runtime libraries.
        ndk_toolchain = NdkToolchain(min_sdk_version=28)
        NdkCMakeBuilder(
            self.top_dir / "toolchain/capnproto/c++",
            OUT_DIR / "capnproto-android",
            android_install_dir,
            ndk_toolchain,
            additional_env={
                # Same as for the host.
                "LD_LIBRARY_PATH": os.pathsep.join(
                    str(p) for p in host_toolchain.runtime_library_paths
                ),
                # Need the host proto compiler on the PATH.
                "PATH": os.pathsep.join(
                    [str(host_install_dir / "bin"), os.environ["PATH"]]
                ),
            },
        ).build(
            {
                "EXTERNAL_CAPNP": "ON",
                "BUILD_SHARED_LIBS": "ON",
            },
            install=True,
        )

        # Finally, build rr.
        rr_out = OUT_DIR / "rr"
        NdkCMakeBuilder(
            self.top_dir / "toolchain/rr",
            rr_out,
            android_install_dir,
            ndk_toolchain,
            additional_env={
                # Same as above.
                "PATH": os.pathsep.join(
                    [str(host_install_dir / "bin"), os.environ["PATH"]]
                ),
                "LD_LIBRARY_PATH": os.pathsep.join(
                    str(p) for p in host_toolchain.runtime_library_paths
                ),
            },
        ).build(
            {
                "BUILD_TESTS": "OFF",
                "CMAKE_FIND_ROOT_PATH": str(android_install_dir),
                "disable32bit": "ON",
                "EXTRA_VERSION_STRING": self.build_id,
                "SKIP_PKGCONFIG": "ON",
                "ZLIB_LDFLAGS": "-lz",
            },
            pack=True,
        )

        DIST_DIR.mkdir(exist_ok=True, parents=True)
        for dist_artifact in (rr_out / "dist").iterdir():
            logging.info("Copying %s to %s", dist_artifact, DIST_DIR)
            shutil.copy(dist_artifact, DIST_DIR)
