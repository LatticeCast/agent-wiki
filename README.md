# agent-wiki

A static wiki. The wiki is Markdown in this repo. External documents live in a blob (RustFS). It is built in two stages and then served as static HTML by Jekyll.

Conventions follow the reference projects in `.tmp/`: `homunmage.github.io` (the site) and `jekyll_layouts` (the `_layouts` submodule).

## Content model

The wiki is offline-first: referenced material is kept in the blob instead of linking to the outside web.

| Kind | Where | Notes |
|------|-------|-------|
| **Wiki content** (written and updated by AI agents and humans) | Markdown in this repo | It is the codebase: editable and versioned by Git. |
| **External documents** (PDFs, images, cited sources) | **Blob**: the `rustfs/rustfs` service in `docker-compose.yml` | Never in Git. |

A document is a folder, like `.tmp/homunmage.github.io/Slides/<doc_name>/`:

```
<doc_name>/
├── index.md        # the wiki page (Git)
├── *.md            # more pages of the same document (Git)
├── images/         # blob
└── pdf/            # blob
```

The Markdown stays in Git. `images/`, `pdf/` and the other external files of each document are stored in the blob under the same `<doc_name>/` path.

The frontend shows blob items with JS: a page can open a blob item (PDF, image, text) and load it straight from the blob at view time.

## Two-stage build

```
 *.md at the repo root (Git)
    │
    ▼  Stage 1: wikic.py (Python 3): hash + link compile
 _stage1/  (plain Markdown, standard links, plus the Jekyll project files)
    │
    ▼  Stage 2: Jekyll (docker image)
 _site/    (static HTML)
```

The Jekyll project lives at the repo root, like `.tmp/homunmage.github.io`: `_config.yml`, `Gemfile`, `_layouts` (submodule), `_plugins`. Wiki pages are the `.md` files in folders at the root. Stage 1 never edits them. It reads them and writes the compiled copy to `_stage1/`, and Jekyll builds from `_stage1/`.

### Stage 1 (`wikic/wikic.py`, Python 3 with `uv`)

1. **Hash every page with its path.** Walk all pages and write `_stage1/manifest.json` (`path`, `name`, `hash`, `url` for each page).
2. **Compile Obsidian-style links.** Resolve `[[filename]]` with that index and rewrite it to a Markdown link:
   - `[[name]]` becomes `[name](/path/)`
   - `[[name|alias]]` becomes `[alias](/path/)`
   - `[[name#Heading]]` becomes `[name](/path/#heading)`
   - Same-name pages: the one in the same folder wins, then the shortest path.
   - Links inside code are left alone. A link that does not resolve becomes `<span class="wikilink-broken">name</span>` and is listed in the build report.
3. **Blob references** (see below) are compiled in the same pass.

Excluded from the wiki pages: dot-folders, folders starting with `_`, `README.md`, `AGENTS.md`, `CLAUDE.md`, `llm*.md`, and the Jekyll/Docker project files.

### Stage 2

Jekyll builds `_stage1/` into `_site/` with the `jekyll/jekyll` Docker image.

## Blob references and viewer

External documents live in the blob (RustFS), one folder per document: `<doc_name>/pdf/…`, `<doc_name>/images/…`, `<doc_name>/md/…`.

In a wiki page:

| Write | Compiled to |
|-------|-------------|
| `![[<doc>/images/<file>]]` | `![<file>](<BLOB_BASE>/<doc>/images/<file>)` |
| `[[ref:<doc>/<kind>/<file>]]` | `[<file>](/viewer/#<doc>/<kind>/<file>)` |
| `[[ref:<doc>/pdf/<file>#p=N]]` | `[<file>](/viewer/#<doc>/pdf/<file>&p=N)` |

`<BLOB_BASE>` is the blob's public URL, set in `_config.yml`.

The `/viewer/` page is a small JS page. It reads the path from the URL hash and loads the object straight from the blob: images with `<img>`, PDF with PDF.js, `md` as text rendered in the browser, anything else as a download link. The site itself contains no blob data. The blob must allow public read and CORS for the site's origin.

`wikic.py ref add <file> --doc <doc>` uploads a file into the blob under `<doc>/<kind>/`.

### Blob

`ref add <file> --doc <doc> [--kind pdf|images|md]` uploads to key `<doc>/<kind>/<basename>` (kind is inferred from the extension when omitted), creates the bucket if missing, and updates `<doc>/meta.json` (`{"title", "objects": {"<kind>/<file>": {"sha256", "size"}}}`). Re-adding the same file is idempotent. `ref list --doc <doc>` prints the stored objects. Settings come from `S3_ENDPOINT` (default `http://localhost:9000`), `BLOB_ACCESS_KEY`, `BLOB_SECRET_KEY`, `S3_BUCKET` (default `wiki`).

```
docker compose up -d blob
docker compose run --rm py python wikic/wikic.py ref add tests/fixtures/sample.pdf --doc demo
docker compose run --rm py python wikic/wikic.py ref list --doc demo
```

Inside compose set `S3_ENDPOINT=http://blob:9000`.

## Jekyll setup (as in `.tmp/homunmage.github.io`)

- `_layouts` is the `PosetMage/jekyll_layouts` git submodule. Layouts used: `base`, `page/note/basic`, `page/note/directory`.
- `_config.yml`: `defaults` choose the layout per path. Plugins: `jekyll-seo-tag`, `jekyll-sitemap`, `jekyll-redirect-from`, `jekyll-titles-from-headings`, `jekyll-external-links`, `jekyll-feed`. `docker-compose.yml`, `Dockerfile` and `.dockerignore` are excluded from the build.
- `_plugins/raw_markdown.rb` serves each page's raw `.md` next to its HTML.
- `llms.txt` / `llm.txt` tell AI how to reach the raw Markdown and the sitemap.
- Images are `.webp` (`img2webp.sh` converts png/jpg).

## Page conventions (as in `.tmp/homunmage.github.io`)

- Front matter: `layout` and `title`; a folder index uses `layout: page/note/directory`.
- `llm.slides.md` is the writing guideline that AI agents follow when writing slides.
- `AGENTS.md` at the repo root holds the working rules for agents.

## Docker

`docker-compose.yml`:

- `blob`: `rustfs/rustfs:latest`. S3 API on `9000`, console on `9001`, keys from `BLOB_ACCESS_KEY` / `BLOB_SECRET_KEY`.
- `py`: built from `wikic/Dockerfile` on the `ghcr.io/astral-sh/uv` image; dependencies are in `pyproject.toml` and installed with `uv sync`. It runs Stage 1 (`wikic/wikic.py`) on the project directory.
- `jekyll`: `jekyll/jekyll:latest`, Stage 2: builds `_stage1/` into `_site/`.

## Run

Set `BLOB_ACCESS_KEY` and `BLOB_SECRET_KEY` in `.env` (read by `docker-compose.yml`).

```
git submodule update --init      # _layouts
make site                        # stage 1 (py container) + stage 2 (jekyll container) -> _site/
make test-site                   # build tests/fixtures/wiki and check every internal link
make test-blob                   # start blob, upload, anonymous GET with CORS
python3 -m unittest discover -s tests
make clean
```

The `blob` service runs as root (`user: "0:0"`), because the RustFS default user cannot write a fresh volume. The `jekyll` service keeps its gems in the `bundle_cache` volume, so only the first `make site` installs them. `py` and `jekyll` write `_stage1/` and `_site/` as your user.

## Project management

Tickets are tracked in the `agent-wiki` table (from the `pm` template): `https://table.novasplit.ai/homun%40novasplit-ai/agent-wiki`. They are worked by the agentic-hive (`.agent-skills/agent/agentic-hive`). Connection settings are in `.tmp/agentic-hive/.env`.
