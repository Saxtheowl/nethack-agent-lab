#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiment_runner import run
from policy import install

if __name__ == "__main__":
    raise SystemExit(run("JEV_SHADOW", install, extra_files=(
        Path(__file__), Path(__file__).with_name("policy.py"),
        ROOT / "JEV_PRIMITIVES" / "policy.py")))
