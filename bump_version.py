#!/usr/bin/env python3

import sys
import re
from pathlib import Path

VERSION_FILE = Path("src/momentum/__version__.py")


def get_current_version():
    content = VERSION_FILE.read_text()
    match = re.search(r'__version__\s*=\s*["\']([\d.]+)["\']', content)
    if not match:
        raise ValueError("Version string not found")
    return match.group(1)


def bump(version, part):
    major, minor, patch = map(int, version.split("."))
    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "patch":
        patch += 1
    else:
        raise ValueError("part must be one of: major, minor, patch")
    return f"{major}.{minor}.{patch}"


def set_version(new_version):
    content = VERSION_FILE.read_text()
    new_content = re.sub(
        r'__version__\s*=\s*["\']([\d.]+)["\']',
        f'__version__ = "{new_version}"',
        content,
    )
    VERSION_FILE.write_text(new_content)


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"major", "minor", "patch"}:
        print("Usage: bump_version.py [major|minor|patch]")
        sys.exit(1)
    part = sys.argv[1]
    current = get_current_version()
    new = bump(current, part)
    set_version(new)
    print(f"Bumped version: {current} → {new}")


if __name__ == "__main__":
    main()
