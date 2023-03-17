#
# Copyright (C) 2020 The Android Open Source Project
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
"""APIs for dealing with cmake scripts."""

import shutil
from pathlib import Path
from typing import Generic, TypeVar

from .paths import ANDROID_DIR
from .subprocext import run
from .toolchain import ClangToolchain, HostLinuxToolchain, NdkToolchain

ToolchainT = TypeVar("ToolchainT", bound=ClangToolchain)


class CMakeBuilder(Generic[ToolchainT]):
    """Builder for a CMake project."""

    def __init__(
        self,
        src_path: Path,
        build_dir: Path,
        install_dir: Path,
        toolchain: ToolchainT,
        additional_env: dict[str, str] | None = None,
    ) -> None:
        """Initializes a CMake builder.

        Args:
            src_path: Path to the cmake project.
            build_dir: Directory to use for building. If the directory exists, it will
                be deleted and recreated to ensure the build is correct.
            install_dir: Directory in which outputs should be installed. This directory
                will not be automatically removed between builds, as it may be shared
                with other builders.
            toolchain: The Clang toolchain used for the build.
            additional_env: Additional environment to set, used during configure, build,
                and install.
        """
        self.src_path = src_path
        self.build_directory = build_dir
        self.install_directory = install_dir
        self.toolchain = toolchain
        self.additional_env = additional_env
        self._cmake = ANDROID_DIR / "prebuilts/cmake/linux-x86/bin/cmake"
        self._cpack = self._cmake.with_stem("cpack")
        self._ninja = ANDROID_DIR / "prebuilts/ninja/linux-x86/ninja"

    @property
    def cmake_defines(self) -> dict[str, str]:
        """The -D arguments that should be passed to CMake."""
        return {
            "CMAKE_BUILD_TYPE": "Release",
            "CMAKE_INSTALL_PREFIX": str(self.install_directory),
            "CMAKE_MAKE_PROGRAM": str(self._ninja),
        }

    def clean(self) -> None:
        """Cleans output directory.

        If necessary, existing output directory will be removed. After
        removal, the inner directories (working directory, install directory,
        and toolchain directory) will be created.
        """
        if self.build_directory.exists():
            shutil.rmtree(self.build_directory)

        self.build_directory.mkdir(parents=True)
        self.install_directory.mkdir(parents=True, exist_ok=True)

    def _run(self, cmd: list[str]) -> None:
        run(cmd, check=True, extra_env=self.additional_env, cwd=self.build_directory)

    def configure(self, additional_defines: dict[str, str]) -> None:
        """Invokes cmake configure."""
        cmake_cmd = [str(self._cmake), "-GNinja"]
        defines = self.cmake_defines
        defines.update(additional_defines)
        cmake_cmd.extend(f"-D{key}={val}" for key, val in defines.items())
        cmake_cmd.append(str(self.src_path))

        self._run(cmake_cmd)

    def make(self) -> None:
        """Builds the project."""
        self._run([str(self._cmake), "--build", "."])

    def install(self) -> None:
        """Installs the project."""
        self._run([str(self._cmake), "--install", ".", "--strip"])

    def pack(self) -> None:
        """Packs the project."""
        self._run([str(self._cpack), "-G", "TGZ"])

    def build(
        self,
        additional_defines: dict[str, str] | None = None,
        install: bool = False,
        pack: bool = False,
    ) -> None:
        """Configures and builds an cmake project.

        Args:
            configure_args: List of arguments to be passed to configure. Does
                not need to include --prefix, --build, or --host. Those are set
                up automatically.
        """
        self.clean()
        self.configure({} if additional_defines is None else additional_defines)
        self.make()
        if install:
            self.install()
        if pack:
            self.pack()


class HostLinuxCMakeBuilder(CMakeBuilder[HostLinuxToolchain]):
    """CMake builder targeting host Linux."""

    @property
    def cmake_defines(self) -> dict[str, str]:
        """CMake defines."""
        asmflags = " ".join(self.toolchain.asmflags)
        cflags = " ".join(self.toolchain.cflags)
        cxxflags = " ".join(self.toolchain.cxxflags)
        ldflags = " ".join(self.toolchain.ldflags(include_common=False))
        defines = super().cmake_defines
        defines.update(
            {
                "CMAKE_C_COMPILER": str(self.toolchain.cc),
                "CMAKE_CXX_COMPILER": str(self.toolchain.cxx),
                "CMAKE_AR": str(self.toolchain.ar),
                "CMAKE_RANLIB": str(self.toolchain.ranlib),
                "CMAKE_NM": str(self.toolchain.nm),
                "CMAKE_STRIP": str(self.toolchain.strip),
                "CMAKE_LINKER": str(self.toolchain.ld),
                "CMAKE_ASM_FLAGS": asmflags,
                "CMAKE_C_FLAGS": cflags,
                "CMAKE_CXX_FLAGS": cxxflags,
                "CMAKE_EXE_LINKER_FLAGS": ldflags,
                "CMAKE_SHARED_LINKER_FLAGS": ldflags,
                "CMAKE_MODULE_LINKER_FLAGS": ldflags,
                "CMAKE_BUILD_TYPE": "Release",
                "CMAKE_INSTALL_PREFIX": str(self.install_directory),
                "CMAKE_MAKE_PROGRAM": str(self._ninja),
                "CMAKE_SYSTEM_NAME": "Linux",
                "CMAKE_SYSTEM_PROCESSOR": "x86_64",
                "CMAKE_FIND_ROOT_PATH_MODE_INCLUDE": "ONLY",
                "CMAKE_FIND_ROOT_PATH_MODE_LIBRARY": "ONLY",
                "CMAKE_FIND_ROOT_PATH_MODE_PACKAGE": "ONLY",
                "CMAKE_FIND_ROOT_PATH_MODE_PROGRAM": "NEVER",
                "CMAKE_C_COMPILER_TARGET": self.toolchain.llvm_target,
                "CMAKE_CXX_COMPILER_TARGET": self.toolchain.llvm_target,
            }
        )
        return defines


class NdkCMakeBuilder(CMakeBuilder[NdkToolchain]):
    """CMake builder using the NDK."""

    def __init__(
        self,
        src_path: Path,
        build_dir: Path,
        install_dir: Path,
        toolchain: NdkToolchain,
        additional_env: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            src_path,
            build_dir,
            install_dir,
            toolchain,
            additional_env,
        )

    @property
    def cmake_defines(self) -> dict[str, str]:
        defines = super().cmake_defines
        defines.update(
            {
                "CMAKE_TOOLCHAIN_FILE": str(
                    self.toolchain.ndk_path / "build/cmake/android.toolchain.cmake"
                ),
                "ANDROID_ABI": "x86_64",
                "ANDROID_PLATFORM": f"android-{self.toolchain.min_sdk_version}",
            }
        )
        return defines
