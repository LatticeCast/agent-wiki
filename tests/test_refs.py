import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "wikic"))
import refs  # noqa: E402


class RefsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.blob = self.root / "blob"
        (self.root / "book.pdf").write_bytes(b"%PDF-1.4 demo")
        (self.root / "fig.png").write_bytes(b"\x89PNG demo")
        (self.root / "notes.md").write_text("# n\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_infer_kind(self):
        self.assertEqual(refs.infer_kind("a.PDF"), "pdf")
        self.assertEqual(refs.infer_kind("a.webp"), "images")
        self.assertEqual(refs.infer_kind("a.md"), "md")
        with self.assertRaises(ValueError):
            refs.infer_kind("a.zip")

    def test_add_copies_file_and_writes_meta(self):
        rel = refs.add(self.blob, self.root / "book.pdf", "rust-book")
        self.assertEqual(rel, "pdf/book.pdf")
        self.assertEqual((self.blob / "rust-book/pdf/book.pdf").read_bytes(), b"%PDF-1.4 demo")
        meta = json.loads((self.blob / "rust-book/meta.json").read_text())
        self.assertEqual(meta["objects"]["pdf/book.pdf"]["size"], 13)
        self.assertEqual(len(meta["objects"]["pdf/book.pdf"]["sha256"]), 64)

    def test_add_is_idempotent_and_lists_sorted(self):
        for f in ("book.pdf", "fig.png", "notes.md", "book.pdf"):
            refs.add(self.blob, self.root / f, "d")
        self.assertEqual(
            refs.list_objects(self.blob, "d"), ["images/fig.png", "md/notes.md", "pdf/book.pdf"]
        )

    def test_cli_add_and_list(self):
        run = lambda *a: subprocess.run(
            [sys.executable, str(REPO / "wikic/wikic.py"), "ref", *a],
            capture_output=True, text=True, check=True,
        ).stdout.split()
        self.assertEqual(
            run("add", str(self.root / "fig.png"), "--doc", "d", "--blob-dir", str(self.blob)),
            ["d/images/fig.png"],
        )
        self.assertEqual(run("list", "--doc", "d", "--blob-dir", str(self.blob)), ["images/fig.png"])


if __name__ == "__main__":
    unittest.main()
