from __future__ import annotations

import argparse
import json
from pathlib import Path


def ttyrec_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for pattern in ("*.ttyrec", "*.ttyrec.xz"):
        files.extend(root.glob(f"recordings/**/{pattern}"))
        files.extend(root.glob(f"wins/**/{pattern}"))
    return sorted(set(files))


def build_index(root: Path) -> list[dict[str, object]]:
    entries = []
    for path in ttyrec_files(root):
        stat = path.stat()
        entries.append(
            {
                "id": str(path.relative_to(root)),
                "name": path.name,
                "group": path.relative_to(root).parts[0],
                "bytes": stat.st_size,
                "modified": int(stat.st_mtime),
            }
        )
    return entries


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="/lab")
    args = parser.parse_args()
    print(json.dumps(build_index(Path(args.root)), indent=2))


if __name__ == "__main__":
    main()
