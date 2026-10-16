"""Blob references: external documents kept in the git-ignored `blob/` folder.

Layout: blob/<doc>/<kind>/<file>, kind = pdf | images | md. The built site
serves the folder at /blob/*, so a file is reachable at /blob/<doc>/<kind>/<file>.
"""
import hashlib
import json
import shutil
from pathlib import Path

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".avif", ".bmp"}


def infer_kind(name):
    ext = Path(name).suffix.lower()
    if ext == ".pdf":
        return "pdf"
    if ext in IMAGE_EXTS:
        return "images"
    if ext == ".md":
        return "md"
    raise ValueError(f"cannot infer kind for {name!r}; pass --kind pdf|images|md")


def read_meta(blob, doc):
    meta = Path(blob) / doc / "meta.json"
    if not meta.is_file():
        return {"title": doc, "objects": {}}
    return json.loads(meta.read_text(encoding="utf-8"))


def add(blob, file, doc, kind=None):
    """Copy `file` to `blob/<doc>/<kind>/<basename>` and update `<doc>/meta.json`."""
    src = Path(file)
    kind = kind or infer_kind(src.name)
    rel = f"{kind}/{src.name}"
    dest = Path(blob) / doc / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)
    data = dest.read_bytes()
    meta = read_meta(blob, doc)
    meta["objects"][rel] = {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
    (Path(blob) / doc / "meta.json").write_text(
        json.dumps(meta, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return rel


def list_objects(blob, doc):
    return sorted(read_meta(blob, doc)["objects"])
