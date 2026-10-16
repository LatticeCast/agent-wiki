"""Stage 1 name index: map wikilink targets to page urls."""
from pathlib import PurePosixPath


def _pages(manifest) -> dict:
    return manifest.get("pages", manifest)


def build_index(manifest) -> dict:
    index = {}
    for path, page in _pages(manifest).items():
        index.setdefault(page["name"], []).append(path)
    return {name: sorted(paths) for name, paths in sorted(index.items())}


def _candidates(target, index, manifest):
    target = target.strip().strip("/").lower()
    if target.endswith(".md"):
        target = target[:-3]
    if not target:
        return []
    if "/" not in target:
        return index.get(target, [])
    found = []
    for path in _pages(manifest):
        key = path.lower()[:-3]
        if key == target or key.endswith("/" + target):
            found.append(path)
    return found


def resolve(target, from_path, index, manifest):
    """Return the url for `target` seen from page `from_path`, or None."""
    paths = _candidates(target, index, manifest)
    if not paths:
        return None
    folder = PurePosixPath(from_path).parent

    def rank(path):
        same = PurePosixPath(path).parent == folder
        return (not same, len(PurePosixPath(path).parts), path)

    return _pages(manifest)[min(paths, key=rank)]["url"]
