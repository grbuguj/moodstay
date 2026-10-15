"""Check local dependencies without reading or printing secret values."""

from __future__ import annotations

import importlib.util
import argparse
import json
import os
import shutil
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, help="Optional project folder whose render.json may provide voice_id")
    args = parser.parse_args()
    configured_voice = bool(os.environ.get("TYPECAST_VOICE_ID"))
    if args.project:
        config_path = args.project.resolve() / "render.json"
        if config_path.is_file():
            config = json.loads(config_path.read_text(encoding="utf-8-sig"))
            configured_voice = configured_voice or bool(config.get("typecast", {}).get("voice_id"))
    checks = {
        "Python 3.11+": sys.version_info >= (3, 11),
        "ffmpeg on PATH": bool(shutil.which("ffmpeg")),
        "ffprobe on PATH": bool(shutil.which("ffprobe")),
        "typecast-python installed": importlib.util.find_spec("typecast") is not None,
        "TYPECAST_API_KEY configured": bool(os.environ.get("TYPECAST_API_KEY")),
        "Typecast voice configured": configured_voice,
    }
    for label, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}  {label}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
