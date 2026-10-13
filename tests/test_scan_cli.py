import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "wiki"
CLI = ROOT / "wikic" / "wikic.py"

EXPECTED = {
    "index.md": ("index", "/"),
    "Alpha/index.md": ("alpha", "/Alpha/"),
    "Alpha/beta.md": ("beta", "/Alpha/beta.html"),
    "Docs/beta.md": ("beta", "/Docs/beta.html"),
    "Docs/code.md": ("code", "/Docs/code.html"),
    "Docs/ref.md": ("ref", "/Docs/ref.html"),
}


def tree_hashes(root: Path) -> dict:
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def run_scan(out: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CLI), "scan", "--root", str(FIXTURE), "--out", str(out)],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


class ScanCliTest(unittest.TestCase):
    def test_manifest_matches_expected(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "nested" / "out"  # CLI must create it
            res = run_scan(out)
            self.assertEqual(res.returncode, 0, res.stderr)
            pages = json.loads((out / "manifest.json").read_text("utf-8"))["pages"]
            self.assertEqual(set(pages), set(EXPECTED))
            for path, (name, url) in EXPECTED.items():
                self.assertEqual(pages[path]["name"], name)
                self.assertEqual(pages[path]["url"], url)
                digest = hashlib.sha256((FIXTURE / path).read_bytes()).hexdigest()
                self.assertEqual(pages[path]["hash"], "sha256:" + digest)

    def test_deterministic_and_sources_untouched(self):
        before = tree_hashes(FIXTURE)
        with tempfile.TemporaryDirectory() as tmp:
            outputs = []
            for i in range(2):
                out = Path(tmp) / f"o{i}"
                self.assertEqual(run_scan(out).returncode, 0)
                outputs.append((out / "manifest.json").read_bytes())
            self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(tree_hashes(FIXTURE), before)


if __name__ == "__main__":
    unittest.main()
