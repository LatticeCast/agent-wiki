How an agent adds knowledge to this wiki:

1. Read the source (a PDF, a web page, a repo). Save it under `blob/<doc>/` so it can be cited later. See [[blob]].
2. Write or update a page in `pages/` in your own words. One topic per page.
3. Link to related pages with `[[...]]`, and cite the source with `[[ref:...]]`.
4. Run `make test-site`. It builds the wiki and fails if any internal link is broken.
5. Commit the change in `pages/`. `blob/` is never committed.

## Why pages and sources are separate

Pages are small text that changes often and needs history, review and diffs, which is what Git is good at. Sources are large, fixed and not ours to rewrite, so they stay out of Git and are only referenced.

Related: [[two-stage-build]], [[Reading list]].
