"""Stage 1 link compile: rewrite Obsidian wikilinks to Markdown links."""
import re

WIKILINK = re.compile(r"\[\[([^\[\]\|#\n]+)(?:#([^\[\]\|\n]*))?(?:\|([^\[\]\n]*))?\]\]")


def slugify(heading: str) -> str:
    slug = heading.strip().lower().replace(" ", "-")
    return re.sub(r"[^\w-]", "", slug)


# Fenced blocks (``` or ~~~) and inline code spans are copied through untouched.
CODE = re.compile(
    r"^ {0,3}(```+|~~~+)[^\n]*\n.*?(?:^ {0,3}\1[`~]*[ \t]*$|\Z)|(`+)(?!`)[^\n]+?(?<!`)\2(?!`)",
    re.S | re.M,
)


def compile_text(text, from_path, resolve):
    """Rewrite wikilinks in `text` outside code; return (text, broken target names).

    `resolve(target, from_path)` returns a page url or None.
    """
    broken = []

    def repl(m):
        target, heading, alias = m.group(1).strip(), m.group(2), m.group(3)
        url = resolve(target, from_path)
        if url is None:
            broken.append(target)
            label = alias.strip() if alias else target
            return f'<span class="wikilink-broken">{label}</span>'
        if heading:
            url += "#" + slugify(heading)
        return f"[{alias.strip() if alias else target}]({url})"

    out, pos = [], 0
    for code in CODE.finditer(text):
        out.append(WIKILINK.sub(repl, text[pos:code.start()]))
        out.append(code.group(0))
        pos = code.end()
    out.append(WIKILINK.sub(repl, text[pos:]))
    return "".join(out), broken
