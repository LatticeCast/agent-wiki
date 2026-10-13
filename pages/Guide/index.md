## Where things live

| What | Where |
|------|-------|
| Wiki pages | `pages/**/*.md` (this folder, in Git) |
| External documents | `blob/<doc>/<kind>/<file>` (git-ignored, served at `/blob/*`) |

## Write a page

1. Create `pages/<folder>/<name>.md`. The file path is the page url: `pages/Notes/two-stage-build.md` is `/Notes/two-stage-build.html`, and `pages/Guide/index.md` is `/Guide/` (its title is "index").
2. The page title is the file name without `.md` (`Reading list.md` is titled "Reading list"). Do not write a `# heading` or `title:` front matter. Start with text, and use `##` for sections.
3. Link to other pages by file name: `[[two-stage-build]]`. See [[wikilinks]].
4. Cite an external document with `[[ref:...]]`. See [[blob]].
5. Run `make site`, then `make serve`.

## Conventions

- One topic per page. Short pages that link to each other beat long pages.
- Put what you learned in your own words in `pages/`. Keep the original source in `blob/` and cite it.
- Keep a `## Sources` list at the end of a page, one citation per line.

Back to [[index]].
