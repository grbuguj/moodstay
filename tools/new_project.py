"""Create a new Moodstay Reel project from projects/_template."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug", help="lowercase project folder name, for example riverside-stay")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    source = root / "projects" / "_template"
    target = root / "projects" / args.slug
    if target.exists():
        raise FileExistsError(f"Project already exists: {target}")
    shutil.copytree(source, target)
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
