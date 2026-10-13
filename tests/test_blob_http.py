"""Blob HTTP smoke test against the compose `blob` service (set BLOB_E2E=1)."""
import os
import sys
import tempfile
import unittest
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "wikic"))
import refs  # noqa: E402

PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c6360f8cfc0f01f0005000201a5f645400000000049454e44ae426082"
)


@unittest.skipUnless(os.environ.get("BLOB_E2E") == "1", "set BLOB_E2E=1 to run")
class BlobHttpTest(unittest.TestCase):
    def test_anonymous_get_with_cors(self):
        client = refs.make_client()
        bucket = refs.bucket_name()
        refs.init(client, bucket)
        refs.init(client, bucket)  # idempotent
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "pixel.png"
            f.write_bytes(PNG)
            rel = refs.add(client, bucket, f, "demo")
        base = os.environ.get(
            "BLOB_BASE",
            os.environ.get("S3_ENDPOINT", "http://localhost:9000").rstrip("/") + "/" + bucket,
        ).rstrip("/")
        req = urllib.request.Request(
            f"{base}/demo/{rel}", headers={"Origin": "http://localhost:4000"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.read(), PNG)
            self.assertIn(
                resp.headers.get("Access-Control-Allow-Origin"), ("*", "http://localhost:4000")
            )


if __name__ == "__main__":
    unittest.main()
