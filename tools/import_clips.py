"""Verify and rename externally generated clips using a project's manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("inbox", type=Path, help="Folder containing downloaded generated videos")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    project = args.project.resolve()
    inbox = args.inbox.resolve()
    manifest_path = project / "clip_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    destination = project / "clips"
    destination.mkdir(parents=True, exist_ok=True)
    for entry in manifest["clips"]:
        source = inbox / entry["source_filename"]
        target = destination / entry["target_filename"]
        if not source.is_file():
            raise FileNotFoundError(f"Missing source clip: {source}")
        expected = entry.get("sha256")
        if expected:
            actual = sha256(source)
            if actual.casefold() != expected.casefold():
                raise ValueError(f"SHA-256 mismatch for {source.name}: {actual}")
        if target.exists() and not args.force:
            raise FileExistsError(f"{target} exists; pass --force to replace")
        shutil.copy2(source, target)
        print(f"{source.name} -> clips/{target.name}")
    print(f"READY: {len(manifest['clips'])} unique clips")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
