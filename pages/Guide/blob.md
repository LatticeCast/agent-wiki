External documents (PDFs, images, converted text) are not stored in Git. Put them in the `blob/` folder, one folder per document:

```
blob/rust-book/
├── pdf/book.pdf
├── images/ownership.png
└── md/notes.md
```

`make site` mounts `blob/` at `/blob/` on the site, so every file is at `/blob/<doc>/<kind>/<file>`. Add a file with:

```
python3 wikic/wikic.py ref add ~/Downloads/book.pdf --doc rust-book
```

## Citing a document

| You write | You get |
|-----------|---------|
| `![[rust-book/images/ownership.png]]` | the image, loaded from `/blob/rust-book/images/ownership.png` |
| `[[ref:rust-book/pdf/book.pdf]]` | a link to the viewer at `/viewer/#rust-book/pdf/book.pdf` |
| `[[ref:rust-book/pdf/book.pdf#p=12]]` | the same, opened at page 12 |
| `[[ref:rust-book/md/notes.md]]` | the viewer rendering the text file |

The [viewer](/viewer/) reads the path after `#` and loads the file from `/blob/` in your browser. It shows images, PDFs (PDF.js) and Markdown, and offers a download for anything else.

The examples above are in code on purpose: the demo files are not in Git, so a real link here would point at nothing. After you add `blob/rust-book/...` yourself, write the same lines outside code.

Back to [[Guide]].
