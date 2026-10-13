"""wikic: Stage 1 compiler for the agent-wiki."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from index import build_index, resolve  # noqa: E402
from links import compile_text  # noqa: E402
from scan import scan  # noqa: E402


def write_manifest(root, out) -> dict:
    manifest = scan(root)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def compile_wiki(root, out):
    """Write the compiled wiki to `out`; return (manifest, broken)."""
    root, out = Path(root), Path(out)
    manifest = write_manifest(root, out)
    index = build_index(manifest)
    broken = []

    def res(target, from_path):
        return resolve(target, from_path, index, manifest)

    for path in manifest["pages"]:
        text = (root / path).read_text(encoding="utf-8")
        text, bad = compile_text(text, path, res)
        broken += [(path, name) for name in bad]
        dest = out / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
    report = {"broken": [{"page": p, "target": t} for p, t in sorted(broken)]}
    (out / "report.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return manifest, broken


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="wikic")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("scan", "compile"):
        p = sub.add_parser(name)
        p.add_argument("--root", default=".")
        p.add_argument("--out", default="_stage1")
    args = ap.parse_args(argv)
    if args.cmd == "compile":
        manifest, broken = compile_wiki(args.root, args.out)
        for path, name in broken:
            print(f"broken link: {path}: [[{name}]]", file=sys.stderr)
        print(f"{len(manifest['pages'])} pages, {len(broken)} broken links")
        return 0
    else:
        manifest = write_manifest(args.root, args.out)
    print(f"{len(manifest['pages'])} pages -> {Path(args.out) / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
