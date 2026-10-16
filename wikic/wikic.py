"""wikic: Stage 1 compiler for the agent-wiki."""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from index import build_index, resolve  # noqa: E402
from links import DEFAULT_BLOB_BASE, compile_text  # noqa: E402
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
JEKYLL_FILES = ("_config.yml", "Gemfile", "Gemfile.lock")
JEKYLL_DIRS = ("_layouts", "assets")


def copy_jekyll_project(out):
    """Copy the Jekyll project files next to the pages (no .git pointers)."""
    for name in JEKYLL_FILES:
        if (REPO / name).is_file():
            shutil.copy2(REPO / name, out / name)
    for name in JEKYLL_DIRS:
        dest = out / name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(
            REPO / name, dest, ignore=shutil.ignore_patterns(".git")
        )


def page_title(path):
    """The title of a page is its file name without `.md`."""
    return Path(path).stem


def with_front_matter(text, title):
    """Jekyll only renders files with front matter; add `title:` when missing."""
    line = f"title: {json.dumps(title, ensure_ascii=False)}\n" if title else ""
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            if not line or re.search(r"^title:", text[4:end], re.M):
                return text
            return "---\n" + line + text[4:]
    return "---\n" + line + "---\n" + text


def blob_base():
    """Blob links always point at /blob/ on the site domain."""
    return DEFAULT_BLOB_BASE


def compile_wiki(root, out):
    """Write the compiled wiki to `out`; return (manifest, broken)."""
    root, out = Path(root), Path(out)
    manifest = write_manifest(root, out)
    index = build_index(manifest)
    broken = []
    base = blob_base()

    def res(target, from_path):
        return resolve(target, from_path, index, manifest)

    for path in manifest["pages"]:
        text = (root / path).read_text(encoding="utf-8")
        text, bad = compile_text(text, path, res, base)
        broken += [(path, name) for name in bad]
        dest = out / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(with_front_matter(text, page_title(path)), encoding="utf-8")
    copy_jekyll_project(out)
    report = {"broken": [{"page": p, "target": t} for p, t in sorted(broken)]}
    (out / "report.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return manifest, broken


def run_ref(args):
    import refs

    blob = Path(args.blob_dir)
    if args.ref_cmd == "add":
        print(f"{args.doc}/{refs.add(blob, args.file, args.doc, args.kind)}")
    else:
        for rel in refs.list_objects(blob, args.doc):
            print(rel)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="wikic")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("scan", "compile"):
        p = sub.add_parser(name)
        p.add_argument("--root", default="pages")
        p.add_argument("--out", default="_stage1")
    ref = sub.add_parser("ref")
    rsub = ref.add_subparsers(dest="ref_cmd", required=True)
    radd = rsub.add_parser("add")
    radd.add_argument("file")
    radd.add_argument("--doc", required=True)
    radd.add_argument("--kind", choices=("pdf", "images", "md"))
    radd.add_argument("--blob-dir", default="blob")
    rlist = rsub.add_parser("list")
    rlist.add_argument("--doc", required=True)
    rlist.add_argument("--blob-dir", default="blob")
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
