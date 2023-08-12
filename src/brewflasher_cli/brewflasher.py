#!/usr/bin/env python

import contextlib
import os
import sys

if os.name != "nt":
    # Linux/macOS: remove current script directory to avoid importing this file
    # as a module; we want to import the installed esptool module instead
    with contextlib.suppress(ValueError):
        executable_dir = os.path.dirname(sys.executable)
        sys.path = [
            path
            for path in sys.path
            if not path.endswith(("/bin", "/sbin")) and path != executable_dir
        ]

    # Linux/macOS: delete imported module entry to force Python to load
    # the module from scratch; this enables importing esptool module in
    # other Python scripts
    with contextlib.suppress(KeyError):
        del sys.modules["brewflasher_cli"]

import brewflasher_cli


def main():
    brewflasher_cli.main()


if __name__ == "__main__":
    brewflasher_cli.main()