"""Attachment storage — local-disk first (free, no server), S3 when configured.

S3 activates only when S3_ENDPOINT is set (MinIO/R2/AWS). Dev and pilot run
on local disk under STORAGE_DIR (default ./var/storage, git-ignored).
"""
import os
import pathlib
import uuid

_DIR = None


def storage_dir() -> pathlib.Path:
    global _DIR
    if _DIR is None:
        root = os.getenv("STORAGE_DIR", os.path.join(os.getcwd(), "var", "storage"))
        _DIR = pathlib.Path(root)
        _DIR.mkdir(parents=True, exist_ok=True)
    return _DIR


def s3_enabled() -> bool:
    return bool(os.getenv("S3_ENDPOINT"))


def save_attachment(org_id: str, filename: str, data: bytes) -> dict:
    """Persist bytes, return a locator dict (stable shape for both backends)."""
    safe = f"{uuid.uuid4().hex}_{pathlib.Path(filename).name}"
    if s3_enabled():
        import boto3

        bucket = os.getenv("S3_BUCKET", "quote-desk")
        client = boto3.client(
            "s3",
            endpoint_url=os.getenv("S3_ENDPOINT"),
            aws_access_key_id=os.getenv("MINIO_USER", "minio"),
            aws_secret_access_key=os.getenv("MINIO_PASSWORD", "minio12345"),
        )
        try:
            client.head_bucket(Bucket=bucket)
        except Exception:
            client.create_bucket(Bucket=bucket)
        client.put_object(Bucket=bucket, Key=f"{org_id}/{safe}", Body=data)
        return {"backend": "s3", "bucket": bucket, "key": f"{org_id}/{safe}"}
    dest = storage_dir() / org_id
    dest.mkdir(parents=True, exist_ok=True)
    (dest / safe).write_bytes(data)
    return {"backend": "local", "path": str(dest / safe), "key": f"{org_id}/{safe}"}


def open_attachment(locator: dict) -> bytes:
    if locator.get("backend") == "s3":
        import boto3

        client = boto3.client(
            "s3",
            endpoint_url=os.getenv("S3_ENDPOINT"),
            aws_access_key_id=os.getenv("MINIO_USER", "minio"),
            aws_secret_access_key=os.getenv("MINIO_PASSWORD", "minio12345"),
        )
        obj = client.get_object(Bucket=locator["bucket"], Key=locator["key"])
        return obj["Body"].read()
    return pathlib.Path(locator["path"]).read_bytes()
