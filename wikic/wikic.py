"""wikic: Stage 1 compiler for the agent-wiki."""
import argparse
import json
import shutil
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


REPO = Path(__file__).resolve().parent.parent
JEKYLL_FILES = ("_config.yml", "Gemfile")
JEKYLL_DIRS = ("_plugins", "_layouts")


def copy_jekyll_project(out):
    """Copy the Jekyll project files next to the pages (no .git pointers)."""
    for name in JEKYLL_FILES:
        shutil.copy2(REPO / name, out / name)
    for name in JEKYLL_DIRS:
        dest = out / name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(
            REPO / name, dest, ignore=shutil.ignore_patterns(".git")
        )


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
    copy_jekyll_project(out)
    report = {"broken": [{"page": p, "target": t} for p, t in sorted(broken)]}
    (out / "report.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return manifest, broken


def run_ref(args, client=None):
    import refs

    client = client or refs.make_client()
    bucket = refs.bucket_name()
    if args.ref_cmd == "add":
        rel = refs.add(client, bucket, args.file, args.doc, args.kind)
        print(f"{args.doc}/{rel}")
    else:
        for rel in refs.list_objects(client, bucket, args.doc):
            print(rel)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="wikic")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("scan", "compile"):
        p = sub.add_parser(name)
        p.add_argument("--root", default=".")
        p.add_argument("--out", default="_stage1")
    ref = sub.add_parser("ref")
    rsub = ref.add_subparsers(dest="ref_cmd", required=True)
    radd = rsub.add_parser("add")
    radd.add_argument("file")
    radd.add_argument("--doc", required=True)
    radd.add_argument("--kind", choices=("pdf", "images", "md"))
    rlist = rsub.add_parser("list")
    rlist.add_argument("--doc", required=True)
    args = ap.parse_args(argv)
    if args.cmd == "ref":
        return run_ref(args)
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
