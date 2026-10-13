import json
import shutil
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
JS = REPO / "assets" / "viewer.js"


@unittest.skipUnless(shutil.which("node"), "node not installed: skipping viewer tests")
class ViewerPureFunctions(unittest.TestCase):
    def run_js(self, expr):
        code = f"const v=require({json.dumps(str(JS))}); console.log(JSON.stringify({expr}))"
        out = subprocess.run(["node", "-e", code], capture_output=True, text=True, check=True)
        return json.loads(out.stdout)

    def test_parse_hash(self):
        r = self.run_js('v.parseHash("#rust-book/pdf/book.pdf&p=12")')
        self.assertEqual(r["doc"], "rust-book")
        self.assertEqual(r["kind"], "pdf")
        self.assertEqual(r["file"], "book.pdf")
        self.assertEqual(r["page"], 12)

    def test_parse_hash_rejects_bad_input(self):
        self.assertIsNone(self.run_js('v.parseHash("")'))
        self.assertIsNone(self.run_js('v.parseHash("#a/b")'))
        self.assertIsNone(self.run_js('v.parseHash("#a/../c")'))

    def test_kind_of(self):
        self.assertEqual(self.run_js('v.kindOf({kind:"images",file:"x.png"})'), "image")
        self.assertEqual(self.run_js('v.kindOf({kind:"pdf",file:"x.pdf"})'), "pdf")
        self.assertEqual(self.run_js('v.kindOf({kind:"md",file:"x.md"})'), "md")
        self.assertEqual(self.run_js('v.kindOf({kind:"zip",file:"x.zip"})'), "download")

    def test_build_url(self):
        self.assertEqual(
            self.run_js('v.buildUrl("http://h:9000/wiki/", "d/images/a b.png")'),
            "http://h:9000/wiki/d/images/a%20b.png",
        )


if __name__ == "__main__":
    unittest.main()
