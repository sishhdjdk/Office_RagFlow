import uuid
from minio import Minio
from flask import current_app


def get_minio_client():
    """获取 MinIO 客户端"""
    return Minio(
        current_app.config["MINIO_ENDPOINT"],
        access_key=current_app.config["MINIO_ACCESS_KEY"],
        secret_key=current_app.config["MINIO_SECRET_KEY"],
        secure=False,
    )


def upload_file(file_data, original_name: str, content_type: str) -> dict:
    """上传文件到 MinIO，返回 object_key 和 file_size"""
    client = get_minio_client()
    bucket = current_app.config["MINIO_BUCKET"]

    ext = original_name.rsplit(".", 1)[-1] if "." in original_name else "bin"
    object_key = f"{uuid.uuid4().hex}/{uuid.uuid4().hex}.{ext}"

    file_data.seek(0, 2)
    file_size = file_data.tell()
    file_data.seek(0)

    client.put_object(
        bucket_name=bucket,
        object_name=object_key,
        data=file_data,
        length=file_size,
        content_type=content_type,
    )

    return {"object_key": object_key, "file_size": file_size}


def get_file_url(object_key: str, bucket: str = None) -> str:
    """生成文件临时下载 URL（7天有效）"""
    client = get_minio_client()
    bucket = bucket or current_app.config["MINIO_BUCKET"]
    return client.presigned_get_object(bucket, object_key, expires=7 * 24 * 3600)

def download_file(object_key: str, local_path: str, bucket: str = None):
    client = get_minio_client()
    bucket = bucket or current_app.config["MINIO_BUCKET"]
    client.fget_object(bucket, object_key, local_path)

def remove_object(object_key: str, bucket: str = None):
    """删除 MinIO 中的对象"""
    client = get_minio_client()
    bucket = bucket or current_app.config["MINIO_BUCKET"]
    client.remove_object(bucket, object_key)
