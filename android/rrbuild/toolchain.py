#
# Copyright (C) 2019 The Android Open Source Project
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
"""APIs for accessing toolchains."""
from __future__ import annotations

from pathlib import Path

from .paths import ANDROID_DIR
from .target import Target

CLANG_VERSION = "clang-r487747"
NDK_VERSION = "r25"


class ClangToolchain:
    """A compiler toolchain.

    Describes the directories, executables, and default flags needed to use a
    toolchain.
    """

    def __init__(self, path: Path, target: Target) -> None:
        self.path = path
        self.target = target

    def clang_tool(self, tool_name: str) -> Path:
        """Returns the path to the Clang tool for the build host."""
        return self.path / "bin" / tool_name

    @property
    def bin_paths(self) -> list[Path]:
        """The path to the toolchain binary directories for use with PATH."""
        return [self.path / "bin"]

    @property
    def ar(self) -> Path:  # pylint: disable=invalid-name
        """The path to the archiver."""
        return self.clang_tool("llvm-ar")

    @property
    def asm(self) -> Path:
        """The path to the assembler."""
        return self.cc

    @property
    def cc(self) -> Path:  # pylint: disable=invalid-name
        """The path to the C compiler."""
        return self.clang_tool("clang")

    @property
    def cxx(self) -> Path:
        """The path to the C++ compiler."""
        return self.clang_tool("clang++")

    @property
    def ld(self) -> Path:  # pylint: disable=invalid-name
        """The path to the linker."""
        return self.clang_tool("ld.lld")

    @property
    def nm(self) -> Path:  # pylint: disable=invalid-name
        """The path to nm."""
        return self.clang_tool("llvm-nm")

    @property
    def ranlib(self) -> Path:
        """The path to ranlib."""
        return self.clang_tool("llvm-ranlib")

    @property
    def strip(self) -> Path:
        """The path to strip."""
        return self.clang_tool("llvm-strip")

    @property
    def strings(self) -> Path:
        """The path to strings."""
        return self.clang_tool("llvm-strings")

    @property
    def llvm_target(self) -> str:
        """The LLVM --target argument for the given target."""
        return self.target.value


class HostLinuxToolchain(ClangToolchain):
    """A toolchain targeting host (GNU) Linux.

    Will use the prebuilt Clang and GNU sysroot in prebuilts/clang and prebuilts/gcc to
    improve hermeticity and portability.
    """

    def __init__(self) -> None:
        super().__init__(
            ANDROID_DIR / "prebuilts/clang/host/linux-x86" / CLANG_VERSION,
            Target.GNU_X86_64,
        )
        self.gcc_path = (
            ANDROID_DIR / "prebuilts/gcc/linux-x86/host/x86_64-linux-glibc2.17-4.8"
        )

    @property
    def lib_dirs(self) -> list[Path]:
        """Additional library directories that must be included manually with -L/-B.

        --sysroot and -gcc-toolchain arne't completely effective with this sysroot
        because it's missing some components that cause Clang to ignore it.
        """
        return [
            # CRT objects
            self.gcc_path / "lib/gcc/x86_64-linux/4.8.3",
            # libgcc
            self.gcc_path / "x86_64-linux/lib64",
            # libc++
            self.path / "lib64",
        ]

    @property
    def common_flags(self) -> list[str]:
        """Flags that should be passed during both compiling and linking."""
        return [
            f"--target={self.llvm_target}",
            f"--sysroot={self.gcc_path / 'sysroot'}",
        ]

    @property
    def asmflags(self) -> list[str]:
        """Flags that should be passed to Clang for assembler sources."""
        return self.common_flags

    @property
    def cflags(self) -> list[str]:
        """Flags that should be passed to Clang for C sources."""
        return self.common_flags

    @property
    def cxxflags(self) -> list[str]:
        """Flags that should be passed to Clang for C++ sources."""
        return self.common_flags + ["-stdlib=libc++"]

    def ldflags(self, include_common: bool = True) -> list[str]:
        """Flags that should be passed to Clang when linking."""
        flags = []
        if include_common:
            flags.extend(self.common_flags)

        flags.append("-fuse-ld=lld")

        for lib_dir in self.lib_dirs:
            # Both -L and -B because Clang only searches for CRT
            # objects in -B directories.
            flags.extend(
                [
                    f"-L{lib_dir}",
                    f"-B{lib_dir}",
                ]
            )

        return flags

    @property
    def runtime_library_paths(self) -> list[Path]:
        """LD_LIBRARY_PATH directories for running programs built by this toolchain."""
        return [self.path / "lib"]


class NdkToolchain(ClangToolchain):
    """An NDK toolchain."""

    def __init__(self, min_sdk_version: int) -> None:
        self.ndk_path = ANDROID_DIR / "toolchain/prebuilts/ndk" / NDK_VERSION
        super().__init__(
            self.ndk_path / "toolchains/llvm/prebuilt/linux-x86_64",
            Target.ANDROID_X86_64,
        )
        self.min_sdk_version = min_sdk_version

    @property
    def llvm_target(self) -> str:
        return f"{self.target.value}{self.min_sdk_version}"
