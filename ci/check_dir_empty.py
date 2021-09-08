#!/usr/bin/env python3
#
# SPDX-License-Identifier: MIT

"""Trivial script to check if a passed directory exists and is not empty."""

import sys
from pathlib import Path

DIR_PATH = Path(sys.argv[1])
if not DIR_PATH.exists():
    sys.exit(f"Output directory {DIR_PATH.as_posix()!r} does not exist")
dir_empty = not any(DIR_PATH.iterdir())
if dir_empty:
    sys.exit(f"Output directory {DIR_PATH.as_posix()!r} was empty")
