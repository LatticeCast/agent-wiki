# Changelog

## 0.2.0

- Breaking: rename `pages/` to `wiki/` and `wikic/` to `build/`.
- Add `lint/lint.py` and require lint before `make build` / `make stage1`.
- Replace `make site` with `make build`; add `make lint`.

## 0.1.0

- Introduce a Git-backed Markdown wiki, published as a static Jekyll site.
- Store editable wiki articles in the repository and keep external PDFs, images,
  and Markdown documents in a git-ignored `blob/` directory.
- Add a two-stage Docker build: Python scans and compiles source Markdown into a
  self-contained Jekyll source tree; Jekyll then renders the deployable site.
- Generate a deterministic page manifest containing logical names, SHA-256
  content hashes, and output URLs.
- Compile Obsidian-style wikilinks, aliases, and heading fragments into standard
  Markdown links; preserve links inside fenced and inline code.
- Resolve duplicate page names predictably: same-folder pages win, then shorter
  paths, then lexical order. Report unresolved links in `report.json` and render
  them visibly in the published page.
- Add blob-reference syntax for image embeds and a local viewer for PDFs, images,
  Markdown, and downloadable files. Vendor PDF.js and marked so the published
  site has no CDN dependency.
- Provide a small Python CLI for adding and listing blob objects, recording each
  object's SHA-256 digest and size in `meta.json`.
- Include a responsive light/dark Jekyll layout, Docker Compose development
  environment, and Make targets for compilation, serving, site validation, and
  cleanup.
- Add unit and integration-style checks for scanning, link compilation, blob
  handling, viewer URL parsing, output determinism, and generated-site links.
