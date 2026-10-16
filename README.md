# agent-wiki

A static wiki. The wiki pages are Markdown in Git (`wiki/`). External documents live in a git-ignored `blob/` folder. A two-stage build turns the pages into a static site that Jekyll serves from a Docker container. Nothing generated is ever written to the host.

## Content model

| Kind | Where | Notes |
|------|-------|-------|
| **Wiki pages** (written and updated by AI agents and humans) | `wiki/**/*.md` | The codebase: editable and versioned by Git. |
| **External documents** (PDFs, images, cited sources) | `blob/<doc>/<kind>/<file>`, `kind` = `pdf` \| `images` \| `md` | Git-ignored, never committed. The site serves the folder at `/blob/*`. |

A document is a folder in `wiki/` (`wiki/<doc>/index.md`, more `.md` next to it). Its external files are in `blob/<doc>/…`, with the same `<doc>` name.

## Two-stage build

```
 wiki/*.md (Git)
    │  Stage 1: lint/lint.py then build/bulid.py in the py container
    ▼
 _stage1/  (Docker volume: compiled pages + Jekyll project files)
    │  Stage 2: Jekyll in the jekyll container
    ▼
 _site/    (Docker volume) + ./blob mounted at _site/blob/
```

`_stage1/` and `_site/` are Docker volumes shared by the `py` and `jekyll` containers. They never appear in the repo folder. Only `./blob` is a host folder, and the `jekyll` service mounts it at `_site/blob/`, so `<domain>/blob/*` serves it.

### Stage 1 (`lint/lint.py` then `build/bulid.py`, Python 3 with `uv`)

1. **Lint before compiling.** Every page must have Jekyll front matter with an ISO-8601 `updated_at`; unresolved wiki links and malformed blob references fail the build.
2. **Hash every page with its path.** Walk `wiki/` and write `manifest.json` (`path`, `name`, `hash` = `sha256:…`, `url` for each page).
2. **Compile Obsidian-style links** to Markdown links:
   - `[[name]]` becomes `[name](/path/)`
   - `[[name|alias]]` becomes `[alias](/path/)`
   - `[[name#Heading]]` becomes `[name](/path/#heading)`
   - Pages with the same name: the one in the same folder wins, then the shortest path.
   - Links inside code are left alone. An unresolved link becomes `<span class="wikilink-broken">name</span>` and is listed in `report.json`.
3. **Blob references** (below) are compiled in the same pass.
4. A page's url is its file path: `Alpha/beta.md` is `/Alpha/beta.html`, and `Alpha/index.md` is `/Alpha/`. Stage 1 adds `title:` when absent.
5. The Jekyll project files (`_config.yml`, `Gemfile`, `_layouts`, `assets`) are copied into `_stage1/`, which makes it a self-contained Jekyll source.

Excluded from the wiki pages: dot-folders, folders starting with `_`, `README.md`, `AGENTS.md`, `CLAUDE.md` and `llm*.md`.

### Stage 2

Jekyll builds `_stage1/` into `_site/` with the `jekyll/jekyll` image. Gems are cached in the `bundle_cache` volume, so only the first build installs them.

## Blob references and viewer

| Write in a page | Compiled to |
|-----------------|-------------|
| `![[<doc>/images/<file>]]` | `![<file>](/blob/<doc>/images/<file>)` |
| `[[ref:<doc>/<kind>/<file>]]` | `[<file>](/assets/viewer.html#<doc>/<kind>/<file>)` |
| `[[ref:<doc>/pdf/<file>#p=N]]` | `[<file>](/assets/viewer.html#<doc>/pdf/<file>&p=N)` |

`/assets/viewer.html` is a small JS page (with `assets/viewer.js`). It reads the path from the URL hash and loads the file from `/blob/…`: images with `<img>`, PDF with PDF.js, `md` as text rendered in the browser, anything else as a download link. PDF.js and marked are vendored in `assets/vendor/`.

`build/bulid.py ref add <file> --doc <doc>` copies a file into `blob/<doc>/<kind>/` and updates `blob/<doc>/meta.json` (sha256 and size per file). `ref list --doc <doc>` lists them.

## Jekyll setup

- `_layouts/default.html` is the only layout, with `assets/wiki.css` (light and dark, system fonts). The site loads nothing from a third party: no CDN scripts, styles or fonts.
- No Jekyll plugin folder and no Ruby files. `_config.yml` lists only gems (`jekyll-seo-tag`, `jekyll-sitemap`, `jekyll-redirect-from`, `jekyll-titles-from-headings`, `jekyll-external-links`, `jekyll-feed`). `keep_files: [blob]` stops Jekyll from cleaning the mounted blob.
- A page's title is its file name without `.md`. Pages have no `title:` front matter and no `# heading`; the layout prints the title as the page heading.

## Docker

`docker-compose.yml` has two services. `docker compose up` starts only `jekyll`.

- `jekyll`: `jekyll/jekyll:latest`. It mounts the `stage1` and `site` volumes, `./blob` at `_site/blob`, and the `bundle_cache` volume. It builds `_stage1` into `_site` and serves it on port `4000`.
- `py` (profile `tools`, so `up` does not start it): built from `build/Dockerfile` on the `ghcr.io/astral-sh/uv` image. It mounts the repo source folders read-only and runs Stage 1. Run it with `make stage1`.

## Run

```
make lint         # validate wiki metadata, links, and blob-reference syntax
make build        # lint, then build wiki/ into the _site volume
make stage1       # lint, then compile wiki/ into the _stage1 volume
docker compose up # build _stage1 and serve it at http://localhost:4000 (jekyll container only)
make serve        # make stage1, then docker compose up
make test         # unit tests (python3 -m unittest discover -s tests)
make test-site    # build tests/fixtures/wiki and check every internal link
make clean        # remove the containers and the stage1/site volumes
```

## Project management

Tickets are tracked in the `agent-wiki` table (from the `pm` template): `https://table.novasplit.ai/homun%40novasplit-ai/agent-wiki`. They are worked by the agentic-hive (`.agent-skills/agent/agentic-hive`). Connection settings are in `.tmp/agentic-hive/.env`.
