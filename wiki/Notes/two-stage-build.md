---
updated_at: 2026-10-13
---

Jekyll cannot resolve `[[name]]` links, because that needs to know every page first. So the build is split.

## Stage 1

A Python tool in the `py` container reads `wiki/` after lint passes.

1. Hash every page together with its path, and write `manifest.json`.
2. Rewrite `[[wikilinks]]` to Markdown links using that index. See [[wikilinks]].
3. Write the compiled pages, plus the site files (layout, styles, viewer), into the `_stage1` volume.

## Stage 2

Jekyll in the `jekyll` container builds `_stage1` into the `_site` volume. Jekyll sees only plain Markdown. The `blob/` folder is mounted at `_site/blob/`, so `/blob/*` is served next to the pages.

Neither volume is on the host, so the repo folder holds only sources. Who runs these steps? See [[agent-workflow]].

Back to [[index]].
