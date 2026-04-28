"""
MinIO / S3-compatible storage service.

Usage:
    from app.services.minio_service import minio_service

    # Upload bytes
    key = minio_service.upload_pdf(data: bytes, prefix="contratos") -> str (object key)

    # Generate a presigned URL (for iframe viewing)
    url = minio_service.presigned_get(key, expires_seconds=300)

    # Delete object
    minio_service.delete(key)

    # Check existence
    minio_service.exists(key) -> bool
"""
import io
import uuid
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

try:
    from minio import Minio
    from minio.error import S3Error
    _MINIO_AVAILABLE = True
except ImportError:
    _MINIO_AVAILABLE = False
    logger.warning("minio package not installed — MinioService disabled.")


class MinioService:
    def __init__(self):
        self._client = None
        self._bucket = None

    def init_app(self, app):
        if not _MINIO_AVAILABLE:
            app.logger.error("minio package missing; file upload disabled.")
            return

        endpoint = app.config.get('MINIO_ENDPOINT', 'localhost:9000')
        access_key = app.config.get('MINIO_ACCESS_KEY', '')
        secret_key = app.config.get('MINIO_SECRET_KEY', '')
        secure = app.config.get('MINIO_SECURE', False)
        self._bucket = app.config.get('MINIO_BUCKET_NAME', 'uploads')

        try:
            self._client = Minio(
                endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure,
            )
            # Ensure bucket exists
            if not self._client.bucket_exists(self._bucket):
                self._client.make_bucket(self._bucket)
                app.logger.info(f"MinIO: bucket '{self._bucket}' creado.")
            app.logger.info(
                f"MinIO: conectado a {endpoint}, bucket='{self._bucket}'."
            )
        except Exception as exc:
            app.logger.error(f"MinIO: no se pudo inicializar — {exc}")
            self._client = None

    # ------------------------------------------------------------------

    @property
    def available(self) -> bool:
        return self._client is not None

    def upload_pdf(self, data: bytes, prefix: str = "contratos") -> str:
        """Upload raw PDF bytes. Returns the object key."""
        if not self.available:
            raise RuntimeError("MinIO no disponible.")
        key = f"{prefix}/{uuid.uuid4()}.pdf"
        self._client.put_object(
            self._bucket,
            key,
            io.BytesIO(data),
            length=len(data),
            content_type="application/pdf",
        )
        return key

    def presigned_get(self, key: str, expires_seconds: int = 300) -> str:
        """Return a presigned GET URL valid for `expires_seconds`."""
        if not self.available:
            raise RuntimeError("MinIO no disponible.")
        url = self._client.presigned_get_object(
            self._bucket,
            key,
            expires=timedelta(seconds=expires_seconds),
        )
        return url

    def delete(self, key: str) -> None:
        """Delete an object. Raises S3Error on failure."""
        if not self.available:
            raise RuntimeError("MinIO no disponible.")
        self._client.remove_object(self._bucket, key)

    def exists(self, key: str) -> bool:
        """Return True if the object exists in the bucket."""
        if not self.available:
            return False
        try:
            self._client.stat_object(self._bucket, key)
            return True
        except Exception:
            return False


minio_service = MinioService()
