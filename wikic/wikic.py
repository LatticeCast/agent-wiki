"""wikic: Stage 1 compiler for the agent-wiki."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan import scan  # noqa: E402


def write_manifest(root, out) -> dict:
    manifest = scan(root)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="wikic")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("scan", "compile"):
        p = sub.add_parser(name)
        p.add_argument("--root", default=".")
        p.add_argument("--out", default="_stage1")
    args = ap.parse_args(argv)
    # compile is a stub for now: it only runs scan.
    manifest = write_manifest(args.root, args.out)
    print(f"{len(manifest['pages'])} pages -> {Path(args.out) / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
