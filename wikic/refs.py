"""Blob references: upload external documents to RustFS (S3) and track them."""
import hashlib
import json
import os
from pathlib import Path

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".avif", ".bmp"}


def infer_kind(name):
    ext = Path(name).suffix.lower()
    if ext == ".pdf":
        return "pdf"
    if ext in IMAGE_EXTS:
        return "images"
    if ext == ".md":
        return "md"
    raise ValueError(f"cannot infer kind for {name!r}; pass --kind pdf|images|md")


def make_client():
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=os.environ.get("S3_ENDPOINT", "http://localhost:9000"),
        aws_access_key_id=os.environ.get("BLOB_ACCESS_KEY"),
        aws_secret_access_key=os.environ.get("BLOB_SECRET_KEY"),
        region_name="us-east-1",
    )


def bucket_name():
    return os.environ.get("S3_BUCKET", "wiki")


def _is_missing(err):
    code = str(getattr(err, "response", {}).get("Error", {}).get("Code", ""))
    return code in ("NoSuchKey", "404", "NoSuchBucket", "NotFound")


def ensure_bucket(client, bucket):
    try:
        client.head_bucket(Bucket=bucket)
    except Exception as err:  # botocore ClientError
        if not _is_missing(err):
            raise
        client.create_bucket(Bucket=bucket)


def read_meta(client, bucket, doc):
    try:
        body = client.get_object(Bucket=bucket, Key=f"{doc}/meta.json")["Body"].read()
    except Exception as err:
        if not _is_missing(err):
            raise
        return {"title": doc, "objects": {}}
    return json.loads(body.decode("utf-8"))


def add(client, bucket, file, doc, kind=None):
    """Upload `file` to `<doc>/<kind>/<basename>` and update `<doc>/meta.json`."""
    path = Path(file)
    kind = kind or infer_kind(path.name)
    data = path.read_bytes()
    ensure_bucket(client, bucket)
    rel = f"{kind}/{path.name}"
    client.put_object(Bucket=bucket, Key=f"{doc}/{rel}", Body=data)
    meta = read_meta(client, bucket, doc)
    meta["objects"][rel] = {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
    client.put_object(
        Bucket=bucket,
        Key=f"{doc}/meta.json",
        Body=(json.dumps(meta, sort_keys=True, indent=2) + "\n").encode("utf-8"),
        ContentType="application/json",
    )
    return rel


def list_objects(client, bucket, doc):
    return sorted(read_meta(client, bucket, doc)["objects"])
