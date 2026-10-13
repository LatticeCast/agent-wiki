"""Stage 1 link compile: rewrite Obsidian wikilinks to Markdown links."""
import re

WIKILINK = re.compile(r"\[\[([^\[\]\|#\n]+)(?:#([^\[\]\|\n]*))?(?:\|([^\[\]\n]*))?\]\]")


def slugify(heading: str) -> str:
    slug = heading.strip().lower().replace(" ", "-")
    return re.sub(r"[^\w-]", "", slug)


def compile_text(text, from_path, resolve):
    """Rewrite wikilinks in `text`; return (text, broken target names).

    `resolve(target, from_path)` returns a page url or None.
    """
    broken = []

    def repl(m):
        target, heading, alias = m.group(1).strip(), m.group(2), m.group(3)
        url = resolve(target, from_path)
        if url is None:
            broken.append(target)
            return m.group(0)
        if heading:
            url += "#" + slugify(heading)
        return f"[{alias.strip() if alias else target}]({url})"

    return WIKILINK.sub(repl, text), broken
