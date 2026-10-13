import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "wikic"))
import refs  # noqa: E402
import wikic  # noqa: E402


class FakeError(Exception):
    def __init__(self, code):
        self.response = {"Error": {"Code": code}}


class FakeS3:
    def __init__(self):
        self.buckets = set()
        self.objects = {}

    def head_bucket(self, Bucket):
        if Bucket not in self.buckets:
            raise FakeError("404")

    def create_bucket(self, Bucket):
        self.buckets.add(Bucket)

    def put_object(self, Bucket, Key, Body, **kw):
        self.objects[(Bucket, Key)] = Body

    def get_object(self, Bucket, Key):
        if (Bucket, Key) not in self.objects:
            raise FakeError("NoSuchKey")
        return {"Body": io.BytesIO(self.objects[(Bucket, Key)])}


class RefsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.s3 = FakeS3()

    def make(self, name, data=b"hello"):
        p = Path(self.tmp.name) / name
        p.write_bytes(data)
        return p

    def test_infer_kind(self):
        self.assertEqual(refs.infer_kind("a.PDF"), "pdf")
        self.assertEqual(refs.infer_kind("a.webp"), "images")
        self.assertEqual(refs.infer_kind("a.md"), "md")
        with self.assertRaises(ValueError):
            refs.infer_kind("a.zip")

    def test_add_uploads_and_writes_meta(self):
        f = self.make("sample.pdf")
        rel = refs.add(self.s3, "wiki", f, "demo")
        self.assertEqual(rel, "pdf/sample.pdf")
        self.assertIn("wiki", self.s3.buckets)
        self.assertEqual(self.s3.objects[("wiki", "demo/pdf/sample.pdf")], b"hello")
        meta = json.loads(self.s3.objects[("wiki", "demo/meta.json")])
        self.assertEqual(meta["title"], "demo")
        entry = meta["objects"]["pdf/sample.pdf"]
        self.assertEqual(entry["size"], 5)
        self.assertEqual(len(entry["sha256"]), 64)

    def test_add_idempotent_and_accumulates(self):
        f = self.make("sample.pdf")
        refs.add(self.s3, "wiki", f, "demo")
        first = self.s3.objects[("wiki", "demo/meta.json")]
        refs.add(self.s3, "wiki", f, "demo")
        self.assertEqual(self.s3.objects[("wiki", "demo/meta.json")], first)
        refs.add(self.s3, "wiki", self.make("p.png"), "demo")
        self.assertEqual(
            refs.list_objects(self.s3, "wiki", "demo"), ["images/p.png", "pdf/sample.pdf"]
        )

    def test_explicit_kind(self):
        rel = refs.add(self.s3, "wiki", self.make("notes.txt"), "d", kind="md")
        self.assertEqual(rel, "md/notes.txt")

    def test_cli_add_and_list(self):
        f = self.make("sample.pdf")
        args = wikic.argparse.Namespace(ref_cmd="add", file=str(f), doc="demo", kind=None)
        self.assertEqual(wikic.run_ref(args, self.s3), 0)
        out = io.StringIO()
        old, sys.stdout = sys.stdout, out
        try:
            wikic.run_ref(wikic.argparse.Namespace(ref_cmd="list", doc="demo"), self.s3)
        finally:
            sys.stdout = old
        self.assertEqual(out.getvalue().strip(), "pdf/sample.pdf")


if __name__ == "__main__":
    unittest.main()
