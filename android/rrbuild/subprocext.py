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
"""Extensions for the subprocess module."""
import logging
import os
import shlex
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


def run(
    cmd: Sequence[str],
    check: bool = False,
    extra_env: Mapping[str, str] | None = None,
    cwd: Path | None = None,
    **kwargs: Any,
) -> subprocess.CompletedProcess[str]:
    """Logging wrapper for subprocess.run.

    Text mode is automatically enabled to simplify type checking.
    """
    if cwd is None:
        real_cwd = Path(os.getcwd())
    else:
        real_cwd = cwd

    if extra_env is None:
        env_str = ""
        env = None
    else:
        env_str = " ".join(f"{k}={v}" for k, v in extra_env.items()) + " "
        env = dict(os.environ)
        env.update(extra_env)

    logging.debug("Running CWD=%s %s%s", real_cwd, env_str, shlex.join(cmd))
    return subprocess.run(cmd, check=check, env=env, cwd=cwd, text=True, **kwargs)
