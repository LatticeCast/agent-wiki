"""Stage 1 link compile: rewrite Obsidian wikilinks to Markdown links."""
import re

WIKILINK = re.compile(r"\[\[([^\[\]\|#\n]+)(?:#([^\[\]\|\n]*))?(?:\|([^\[\]\n]*))?\]\]")


# `![[doc/images/file]]` embeds and `[[ref:doc/kind/file#p=N]]` viewer links.
BLOBREF = re.compile(r"(!)?\[\[(ref:)?([^\[\]\|#\n]+)(?:#([^\[\]\|\n]*))?(?:\|([^\[\]\n]*))?\]\]")
KINDS = ("pdf", "images", "md")
DEFAULT_BLOB_BASE = "/blob"


def slugify(heading: str) -> str:
    slug = heading.strip().lower().replace(" ", "-")
    return re.sub(r"[^\w-]", "", slug)


# Fenced blocks (``` or ~~~) and inline code spans are copied through untouched.
CODE = re.compile(
    r"^ {0,3}(```+|~~~+)[^\n]*\n.*?(?:^ {0,3}\1[`~]*[ \t]*$|\Z)|(`+)(?!`)[^\n]+?(?<!`)\2(?!`)",
    re.S | re.M,
)


def compile_text(text, from_path, resolve, blob_base=DEFAULT_BLOB_BASE, on_broken=None):
    """Rewrite wikilinks in `text` outside code; return (text, broken target names).

    `resolve(target, from_path)` returns a page url or None.
    """
    broken = []
    blob_base = blob_base.rstrip("/")

    def blobref(m):
        bang, ref, target, frag, alias = m.groups()
        if not bang and not ref:
            return m.group(0)
        target = target.strip()
        parts = target.split("/")
        ok = len(parts) >= 3 and all(parts) and parts[1] in KINDS
        if bang and ok:
            ok = parts[1] == "images"
        if not ok:
            broken.append(target)
            if on_broken:
                on_broken("reference", target)
            return f'<span class="wikilink-broken">{target}</span>'
        label = parts[-1]
        if bang:
            return f"![{label}]({blob_base}/{target})"
        url = f"/assets/viewer.html#{target}"
        if frag and frag.startswith("p=") and frag[2:].isdigit():
            url += f"&{frag}"
        return f"[{alias.strip() if alias else label}]({url})"

    def repl(m):
        target, heading, alias = m.group(1).strip(), m.group(2), m.group(3)
        url = resolve(target, from_path)
        if url is None:
            broken.append(target)
            if on_broken:
                on_broken("link", target)
            label = alias.strip() if alias else target
            return f'<span class="wikilink-broken">{label}</span>'
        if heading:
            url += "#" + slugify(heading)
        return f"[{alias.strip() if alias else target}]({url})"

    def sub(chunk):
        return WIKILINK.sub(repl, BLOBREF.sub(blobref, chunk))

    out, pos = [], 0
    for code in CODE.finditer(text):
        out.append(sub(text[pos:code.start()]))
        out.append(code.group(0))
        pos = code.end()
    out.append(sub(text[pos:]))
    return "".join(out), broken
