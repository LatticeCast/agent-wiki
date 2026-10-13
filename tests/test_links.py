import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "wiki"
sys.path.insert(0, str(ROOT / "wikic"))
from links import compile_text, slugify  # noqa: E402


def res(target, from_path):
    return {"beta": "/Alpha/beta/"}.get(target)


class LinksTest(unittest.TestCase):
    def c(self, text):
        return compile_text(text, "Alpha/index.md", res)

    def test_forms(self):
        out, broken = self.c("[[beta]] [[beta|Beta page]] [[beta#Some Heading]]")
        self.assertEqual(
            out, "[beta](/Alpha/beta/) [Beta page](/Alpha/beta/) [beta](/Alpha/beta/#some-heading)"
        )
        self.assertEqual(broken, [])

    def test_plain_unchanged(self):
        self.assertEqual(self.c("no links [x](y)\n"), ("no links [x](y)\n", []))

    def test_unresolved(self):
        self.assertEqual(
            self.c("[[nope]] [[nope|Alias]]"),
            ('<span class="wikilink-broken">nope</span> <span class="wikilink-broken">Alias</span>',
             ["nope", "nope"]),
        )

    def test_code_untouched(self):
        text = "```\n[[beta]]\n```\n~~~\n[[nope]]\n~~~\n`[[beta]]` and ``[[x]]``\n"
        self.assertEqual(self.c(text), (text, []))

    def test_slug(self):
        self.assertEqual(slugify("Some Heading!"), "some-heading")

    def test_cli(self):
        with tempfile.TemporaryDirectory() as o:
            subprocess.run(
                [sys.executable, str(ROOT / "wikic" / "wikic.py"), "compile",
                 "--root", str(FIXTURE), "--out", o],
                check=True, capture_output=True,
            )
            text = (Path(o) / "Alpha" / "index.md").read_text()
            self.assertIn("[beta](/Alpha/beta/)", text)
            self.assertIn("[Beta page](/Alpha/beta/)", text)
            self.assertIn("[beta](/Alpha/beta/#some-heading)", text)
            self.assertTrue((Path(o) / "manifest.json").exists())

    def test_cli_code_and_report(self):
        with tempfile.TemporaryDirectory() as o:
            r = subprocess.run(
                [sys.executable, str(ROOT / "wikic" / "wikic.py"), "compile",
                 "--root", str(FIXTURE), "--out", o],
                check=True, capture_output=True, text=True,
            )
            self.assertEqual(r.returncode, 0)
            src = (FIXTURE / "Docs" / "code.md").read_text()
            out = (Path(o) / "Docs" / "code.md").read_text()
            self.assertIn("```\n[[beta]] in a fence\n```", out)
            self.assertIn("~~~\n[[beta|alias]]\n~~~", out)
            self.assertIn("`[[beta]]`", out)
            self.assertIn('<span class="wikilink-broken">nope</span>', out)
            self.assertIn('<span class="wikilink-broken">Gone alias</span>', out)
            self.assertIn("[[nope]]", src)
            report = json.loads((Path(o) / "report.json").read_text())
            self.assertEqual(
                report,
                {"broken": [{"page": "Docs/code.md", "target": "gone"},
                            {"page": "Docs/code.md", "target": "nope"}]},
            )
            self.assertIn("2 broken", r.stdout)


if __name__ == "__main__":
    unittest.main()
