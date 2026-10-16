import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "wiki"
sys.path.insert(0, str(ROOT / "build"))
from index import build_index, resolve  # noqa: E402
from scan import scan  # noqa: E402


class IndexTest(unittest.TestCase):
    def setUp(self):
        self.manifest = scan(FIXTURE)
        self.index = build_index(self.manifest)

    def r(self, target, from_path):
        return resolve(target, from_path, self.index, self.manifest)

    def test_build_index(self):
        self.assertEqual(self.index["beta"], ["Alpha/beta.md", "Docs/beta.md"])
        self.assertEqual(self.index["alpha"], ["Alpha/index.md"])

    def test_same_folder_wins(self):
        self.assertEqual(self.r("beta", "Alpha/index.md"), "/Alpha/beta.html")
        self.assertEqual(self.r("beta", "Docs/code.md"), "/Docs/beta.html")

    def test_tie_is_lexicographic(self):
        self.assertEqual(self.r("beta", "index.md"), "/Alpha/beta.html")

    def test_path_like_and_case(self):
        self.assertEqual(self.r("Docs/beta", "index.md"), "/Docs/beta.html")
        self.assertEqual(self.r("docs/BETA.md", "Alpha/index.md"), "/Docs/beta.html")

    def test_unknown_is_none(self):
        self.assertIsNone(self.r("nope", "index.md"))
        self.assertIsNone(self.r("Docs/nope", "index.md"))
        self.assertIsNone(self.r("", "index.md"))


if __name__ == "__main__":
    unittest.main()
