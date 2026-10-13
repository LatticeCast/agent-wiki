"""Check that every internal link in a built site resolves to a file."""
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.hrefs.append(href)


def resolves(site, href):
    """True if an internal href maps to a file or folder index in `site`."""
    path = unquote(urlsplit(href).path)
    target = site / path.lstrip("/")
    return target.is_file() or (target / "index.html").is_file()


def check(site):
    """Return a list of (page, href) pairs for broken internal links."""
    site = Path(site)
    broken = []
    for page in sorted(site.rglob("*.html")):
        parser = Links()
        parser.feed(page.read_text(encoding="utf-8"))
        for href in parser.hrefs:
            if not href.startswith("/") or href.startswith("//"):
                continue
            if not resolves(site, href):
                broken.append((str(page.relative_to(site)), href))
    return broken


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    site = Path(argv[0] if argv else "_site")
    if not (site / "index.html").is_file():
        print(f"{site}/index.html missing", file=sys.stderr)
        return 1
    broken = check(site)
    for page, href in broken:
        print(f"broken link: {page}: {href}", file=sys.stderr)
    print(f"{len(broken)} broken internal links")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
