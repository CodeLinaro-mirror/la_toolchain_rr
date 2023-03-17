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
"""Application for Android rr builder."""
from __future__ import annotations

import argparse
import logging

from .builder import Builder
from .paths import ANDROID_DIR


class App:
    """Application entry point for Android's rr builder."""

    def __init__(self, build_id: str, verbosity: int) -> None:
        self.build_id = build_id
        self.verbosity = verbosity

    @staticmethod
    def from_args(argv: list[str]) -> App:
        """Creates a new App with the given command-line arguments."""
        args = App.parse_args(argv[1:])
        return App(args.build_id, args.verbose)

    @staticmethod
    def parse_args(argv: list[str]) -> argparse.Namespace:
        """Parses command line arguments."""
        parser = argparse.ArgumentParser()
        parser.add_argument("-v", "--verbose", action="count", default=0)
        parser.add_argument("--build-id", default="dev")
        return parser.parse_args(argv)

    def run(self) -> None:
        """Runs the builder application."""
        log_levels = [logging.WARNING, logging.INFO, logging.DEBUG]
        level = log_levels[min(self.verbosity, len(log_levels) - 1)]
        logging.basicConfig(level=level)
        Builder(ANDROID_DIR, self.build_id).build()
