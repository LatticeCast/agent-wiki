import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_scan_cli import CLI, FIXTURE, ROOT, tree_hashes  # noqa: E402

EXPECTED = ROOT / "tests" / "expected"


def run_compile(out: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CLI), "compile", "--root", str(FIXTURE), "--out", str(out)],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


def strip_code(text: str) -> str:
    text = re.sub(r"^(```|~~~).*?^\1", "", text, flags=re.S | re.M)
    return re.sub(r"`[^`\n]*`", "", text)


class CompileCliTest(unittest.TestCase):
    def test_output_matches_expected_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "nested" / "out"
            res = run_compile(out)
            self.assertEqual(res.returncode, 0, res.stderr)
            got, want = tree_hashes(out), tree_hashes(EXPECTED)
            got = {
                k: v
                for k, v in got.items()
                if k not in ("_config.yml", "Gemfile", "Gemfile.lock")
                and not k.startswith(("_layouts/", "assets/", "viewer/"))
            }
            self.assertEqual(set(got), set(want))
            for path in want:
                self.assertEqual(got[path], want[path], path)

    def test_sources_untouched_and_idempotent(self):
        before = tree_hashes(FIXTURE)
        with tempfile.TemporaryDirectory() as tmp:
            for i in range(2):
                self.assertEqual(run_compile(Path(tmp) / f"o{i}").returncode, 0)
            self.assertEqual(
                tree_hashes(Path(tmp) / "o0"), tree_hashes(Path(tmp) / "o1")
            )
        self.assertEqual(tree_hashes(FIXTURE), before)

    def test_report_lists_known_broken_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "o"
            res = run_compile(out)
            report = json.loads((out / "report.json").read_text("utf-8"))
            self.assertEqual(
                report["broken"],
                [
                    {"page": "Docs/code.md", "target": "gone"},
                    {"page": "Docs/code.md", "target": "nope"},
                ],
            )
            self.assertIn("[[nope]]", res.stderr)

    def test_no_raw_wikilink_outside_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "o"
            run_compile(out)
            for page in out.rglob("*.md"):
                self.assertNotIn("[[", strip_code(page.read_text("utf-8")), page)

    def test_output_contains_jekyll_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "o"
            self.assertEqual(run_compile(out).returncode, 0)
            for rel in (
                "_config.yml",
                "Gemfile",
                "_layouts/default.html",
            ):
                self.assertTrue((out / rel).is_file(), rel)
            self.assertFalse(list(out.rglob(".git")))


if __name__ == "__main__":
    unittest.main()
