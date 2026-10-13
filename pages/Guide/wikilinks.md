Stage 1 turns Obsidian-style links into normal Markdown links before Jekyll runs.

| You write | You get |
|-----------|---------|
| `[[two-stage-build]]` | [[two-stage-build]] |
| `[[two-stage-build\|how it is built]]` | [[two-stage-build|how it is built]] |
| `[[two-stage-build#Stage 1]]` | [[two-stage-build#Stage 1]] |
| `[[Notes/agent-workflow]]` | [[Notes/agent-workflow]] |

## Rules

- A link is resolved by file name, case-insensitive; `.md` is optional.
- If two pages share a name, the page in the same folder wins, then the shortest path. Write `[[folder/name]]` to be exact.
- Links inside code, like the ones in the table above, are not compiled.
- A link that matches no page is shown with a dashed red underline and listed in `report.json`: <span class="wikilink-broken">this one</span> is what it looks like.

See also [[blob]] and [[Guide]].
