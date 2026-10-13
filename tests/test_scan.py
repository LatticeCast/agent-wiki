import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "wiki"
sys.path.insert(0, str(ROOT / "wikic"))
from scan import scan  # noqa: E402

EXPECTED = {
    "index.md": ("index", "/"),
    "Alpha/index.md": ("alpha", "/Alpha/"),
    "Alpha/beta.md": ("beta", "/Alpha/beta/"),
    "Docs/beta.md": ("beta", "/Docs/beta/"),
    "Docs/code.md": ("code", "/Docs/code/"),
    "Docs/ref.md": ("ref", "/Docs/ref/"),
}


class ScanTest(unittest.TestCase):
    def test_pages_names_urls(self):
        pages = scan(FIXTURE)["pages"]
        self.assertEqual(set(pages), set(EXPECTED))
        for path, (name, url) in EXPECTED.items():
            self.assertEqual(pages[path]["name"], name)
            self.assertEqual(pages[path]["url"], url)

    def test_hash(self):
        pages = scan(FIXTURE)["pages"]
        want = "sha256:" + hashlib.sha256((FIXTURE / "Alpha/beta.md").read_bytes()).hexdigest()
        self.assertEqual(pages["Alpha/beta.md"]["hash"], want)
        self.assertEqual(scan(FIXTURE), scan(FIXTURE))

    def test_cli_deterministic(self):
        with tempfile.TemporaryDirectory() as o1, tempfile.TemporaryDirectory() as o2:
            for o in (o1, o2):
                subprocess.run(
                    [sys.executable, str(ROOT / "wikic/wikic.py"), "scan",
                     "--root", str(FIXTURE), "--out", o],
                    check=True, capture_output=True,
                )
            a = (Path(o1) / "manifest.json").read_bytes()
            self.assertEqual(a, (Path(o2) / "manifest.json").read_bytes())
            self.assertTrue(a.endswith(b"\n"))
            self.assertEqual(set(json.loads(a)["pages"]), set(EXPECTED))


if __name__ == "__main__":
    unittest.main()
