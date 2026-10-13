import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_site import check  # noqa: E402


class CheckSiteTest(unittest.TestCase):
    def build(self, tmp, link):
        site = Path(tmp)
        (site / "a").mkdir()
        (site / "index.html").write_text(f'<a href="{link}">x</a>')
        (site / "a" / "index.html").write_text("ok")
        return site

    def test_resolving_and_external_links_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = self.build(tmp, "/a/")
            (site / "a" / "index.html").write_text(
                '<a href="https://x.org/z">e</a><a href="/a/#h">s</a>'
            )
            self.assertEqual(check(site), [])

    def test_broken_link_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = self.build(tmp, "/missing/")
            self.assertEqual(check(site), [("index.html", "/missing/")])


if __name__ == "__main__":
    unittest.main()
