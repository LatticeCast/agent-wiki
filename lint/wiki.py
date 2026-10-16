"""Knowledge-quality checks for a Markdown wiki."""
import re
from datetime import date
from pathlib import Path

from index import build_index, resolve
from links import compile_text
from scan import scan

FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---(?:\n|\Z)", re.S)
UPDATED_AT = re.compile(r"^updated_at:\s*(.+?)\s*$", re.M)


def _updated_at(text):
    match = FRONT_MATTER.match(text)
    if not match:
        return None, "missing_front_matter"
    value = UPDATED_AT.search(match.group(1))
    if not value:
        return None, "missing_updated_at"
    raw = value.group(1).strip().strip('"\'')
    try:
        date.fromisoformat(raw)
    except ValueError:
        return None, "invalid_updated_at"
    return raw, None


def lint_wiki(root) -> dict:
    """Return deterministic, machine-readable wiki quality findings."""
    root = Path(root)
    manifest = scan(root)
    index = build_index(manifest)
    report = {
        "missing_front_matter": [],
        "missing_updated_at": [],
        "invalid_updated_at": [],
        "broken_links": [],
        "invalid_references": [],
    }

    def res(target, from_path):
        return resolve(target, from_path, index, manifest)

    for path in manifest["pages"]:
        text = (root / path).read_text(encoding="utf-8")
        _, issue = _updated_at(text)
        if issue:
            report[issue].append(path)
        broken = []

        def on_broken(kind, target):
            broken.append((kind, target))

        compile_text(text, path, res, on_broken=on_broken)
        for kind, target in broken:
            key = "invalid_references" if kind == "reference" else "broken_links"
            report[key].append({"page": path, "target": target})
    return report


def has_findings(report) -> bool:
    return any(report[key] for key in report)
