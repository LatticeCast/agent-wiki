"""Stage 1 scan: collect wiki pages and hash them."""
import hashlib
from pathlib import Path

EXCLUDED_FILES = {"README.md", "AGENTS.md", "CLAUDE.md"}
EXCLUDED_ROOT_DIRS = {"tests", "wikic", "node_modules", "vendor", "assets"}


def is_page(rel: Path) -> bool:
    parts = rel.parts
    if rel.suffix != ".md":
        return False
    if any(p.startswith((".", "_")) for p in parts):
        return False
    if len(parts) > 1 and parts[0] in EXCLUDED_ROOT_DIRS:
        return False
    if rel.name in EXCLUDED_FILES or (rel.name.startswith("llm") and rel.name.endswith(".md")):
        return False
    return True


def page_name(rel: Path) -> str:
    if rel.stem == "index":
        return (rel.parent.name or "index").lower()
    return rel.stem.lower()


def page_url(rel: Path) -> str:
    if rel.name == "index.md":
        return "/" if rel.parent == Path(".") else "/" + rel.parent.as_posix() + "/"
    return "/" + rel.with_suffix("").as_posix() + "/"


def scan(root) -> dict:
    root = Path(root)
    pages = {}
    for f in sorted(root.rglob("*.md")):
        if not f.is_file():
            continue
        rel = f.relative_to(root)
        if not is_page(rel):
            continue
        pages[rel.as_posix()] = {
            "name": page_name(rel),
            "hash": "sha256:" + hashlib.sha256(f.read_bytes()).hexdigest(),
            "url": page_url(rel),
        }
    return {"pages": pages}
