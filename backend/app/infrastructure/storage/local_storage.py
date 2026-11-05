"""Local filesystem implementation of the artifact storage interface.

Enforces server-side key generation, path traversal defense, file size limits,
content signature (magic bytes) validation, and strict file isolation.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import logging
import mimetypes
import os
from collections.abc import Generator
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from app.infrastructure.storage.base import (
    StorageError,
    StorageFileNotFoundError,
    StorageFileTooLargeError,
    StorageInterface,
    StorageInvalidTypeError,
    StorageSecurityError,
    StoredFileMetadata,
)

logger = logging.getLogger("skillverse.storage")

# Common magic byte signatures for content validation
MAGIC_SIGNATURES: dict[str, list[bytes]] = {
    ".png": [b"\x89PNG\r\n\x1a\n"],
    ".jpg": [b"\xff\xd8\xff"],
    ".jpeg": [b"\xff\xd8\xff"],
    ".pdf": [b"%PDF-"],
    ".zip": [b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"],
    ".tar.gz": [b"\x1f\x8b"],
    ".tgz": [b"\x1f\x8b"],
}

# Dangerous executable and script extensions that are always strictly blocked
BLOCKED_EXTENSIONS: set[str] = {
    ".exe",
    ".bat",
    ".cmd",
    ".sh",
    ".bash",
    ".ps1",
    ".py",
    ".pyw",
    ".js",
    ".mjs",
    ".cjs",
    ".ts",
    ".html",
    ".htm",
    ".xhtml",
    ".php",
    ".phtml",
    ".asp",
    ".aspx",
    ".jsp",
    ".dll",
    ".so",
    ".dylib",
    ".vbs",
    ".wsf",
    ".scr",
    ".jar",
    ".com",
    ".msi",
}


class LocalStorageService(StorageInterface):
    """Local disk artifact storage service for development and testing."""

    def __init__(
        self,
        base_dir: str | Path,
        max_file_size_bytes: int = 20 * 1024 * 1024,
        allowed_extensions: list[str] | set[str] | None = None,
    ) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.max_file_size_bytes = max_file_size_bytes
        self.allowed_extensions = {
            ext.lower()
            for ext in (
                allowed_extensions
                or [
                    ".zip",
                    ".tar.gz",
                    ".tgz",
                    ".pdf",
                    ".png",
                    ".jpg",
                    ".jpeg",
                    ".webp",
                    ".txt",
                    ".md",
                    ".json",
                    ".csv",
                ]
            )
        }
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
            if hasattr(os, "chmod") and os.name != "nt":
                os.chmod(self.base_dir, 0o700)
        except Exception as exc:
            logger.warning("Could not set permissions on storage root %s: %s", self.base_dir, exc)

    def _extract_extension(self, filename: str) -> str:
        """Extract extension safely, recognizing compound extensions like .tar.gz."""
        lower = filename.lower()
        if lower.endswith(".tar.gz"):
            return ".tar.gz"
        return Path(lower).suffix

    def _is_within_base_dir(self, target_path: Path) -> bool:
        """Verify that target_path is strictly contained within self.base_dir.

        Rejects sibling directories sharing string prefixes and the root directory itself.
        """
        try:
            resolved_target = target_path.resolve()
            resolved_base = self.base_dir.resolve()
            if resolved_target == resolved_base:
                return False
            if not resolved_target.is_relative_to(resolved_base):
                return False
            common = os.path.commonpath([str(resolved_target), str(resolved_base)])
            return os.path.normcase(common) == os.path.normcase(str(resolved_base))
        except (ValueError, AttributeError):
            return False

    def _resolve_secure_path(self, storage_key: str) -> Path:
        """Resolve a storage key and strictly verify it resides within the base directory.

        Prevents directory traversal, null-byte injection, and absolute path escapes.
        """
        if not storage_key or not isinstance(storage_key, str):
            raise StorageSecurityError("Storage key must be a non-empty string.")

        if "\0" in storage_key:
            raise StorageSecurityError("Null bytes are prohibited in storage keys.")

        normalized = storage_key.replace("\\", "/").strip()
        parts = normalized.split("/")
        if any(part in ("..", ".", "") for part in parts):
            raise StorageSecurityError(
                f"Path traversal sequence detected in storage key: {storage_key}"
            )

        resolved = (self.base_dir / normalized).resolve()
        if not self._is_within_base_dir(resolved):
            raise StorageSecurityError("Resolved storage path escapes the storage root.")

        return resolved

    def _validate_file_type(self, extension: str, header_bytes: bytes) -> None:
        """Validate extension allowlist, blocklist, and magic byte signatures."""
        ext = extension.lower()

        if ext in BLOCKED_EXTENSIONS:
            raise StorageInvalidTypeError(f"File extension '{ext}' is explicitly blocked for security reasons.")

        if ext not in self.allowed_extensions:
            raise StorageInvalidTypeError(
                f"File extension '{ext}' is not permitted. Allowed: {sorted(self.allowed_extensions)}"
            )

        # Check content signature (magic bytes) if applicable
        expected_signatures = MAGIC_SIGNATURES.get(ext)
        if expected_signatures and (
            not header_bytes or not any(header_bytes.startswith(sig) for sig in expected_signatures)
        ):
            raise StorageInvalidTypeError(
                f"File content does not match expected binary signature for extension '{ext}'."
            )

        # Genuine WebP signature validation: RIFF at offset 0, WEBP at offset 8 (minimum 12 bytes)
        if ext == ".webp" and (
            not header_bytes
            or len(header_bytes) < 12
            or not header_bytes.startswith(b"RIFF")
            or header_bytes[8:12] != b"WEBP"
        ):
            raise StorageInvalidTypeError(
                f"File content does not match expected binary signature for extension '{ext}'."
            )

        # Strict validation for text formats: reject executable binary signatures first, then null bytes
        if ext in (".txt", ".md", ".json", ".csv") and header_bytes:
            if header_bytes.startswith(
                (b"MZ", b"\x7fELF", b"\xca\xfe\xba\xbe", b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf")
            ):
                raise StorageInvalidTypeError(
                    f"File claims to be text ({ext}) but contains executable binary signature."
                )
            if b"\x00" in header_bytes:
                raise StorageInvalidTypeError(
                    f"Text file '{ext}' contains binary null bytes and cannot be uploaded."
                )

    def store(
        self,
        file_data: bytes | BinaryIO,
        filename: str,
        content_type: str | None = None,
        prefix: str = "artifacts",
    ) -> StoredFileMetadata:
        """Persist file data in streaming chunks with validation and server key generation."""
        # Sanitize original display filename
        clean_name = os.path.basename(filename.replace("\\", "/")).strip()
        if not clean_name:
            clean_name = "unnamed_artifact"

        ext = self._extract_extension(clean_name)
        stream = BytesIO(file_data) if isinstance(file_data, bytes) else file_data

        # Read initial chunk to inspect header and validate signature
        header = stream.read(512)
        self._validate_file_type(ext, header)
        stream.seek(0)

        # Generate server-side random storage key (never includes user filename in path)
        now = datetime.now(UTC)
        safe_prefix = prefix.strip("/").replace("\\", "/")
        key_parts = [safe_prefix, f"{now.year:04d}", f"{now.month:02d}", f"{uuid4().hex}{ext}"]
        storage_key = "/".join(key_parts)

        target_path = self._resolve_secure_path(storage_key)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Stream chunks to disk while calculating SHA-256 and enforcing size limit
        hasher = hashlib.sha256()
        total_bytes = 0
        chunk_size = 65536

        try:
            with open(target_path, "wb") as dst:
                while True:
                    chunk = stream.read(chunk_size)
                    if not chunk:
                        break
                    total_bytes += len(chunk)
                    if total_bytes > self.max_file_size_bytes:
                        raise StorageFileTooLargeError(
                            f"File size ({total_bytes} bytes) exceeds maximum limit "
                            f"({self.max_file_size_bytes} bytes)."
                        )
                    hasher.update(chunk)
                    dst.write(chunk)

            # Set restrictive file permissions where supported
            if hasattr(os, "chmod") and os.name != "nt":
                os.chmod(target_path, 0o600)

        except Exception:
            # Clean up partially written file on failure
            if target_path.exists():
                with contextlib.suppress(OSError):
                    target_path.unlink()
            raise

        detected_mime, _ = mimetypes.guess_type(clean_name)
        mime_type = content_type or detected_mime or "application/octet-stream"
        checksum = hasher.hexdigest()

        metadata = StoredFileMetadata(
            storage_key=storage_key,
            original_filename=clean_name,
            mime_type=mime_type,
            file_size_bytes=total_bytes,
            checksum_sha256=checksum,
            created_at=now,
        )

        # Persist sidecar metadata for retrieval and audit
        meta_path = target_path.with_suffix(target_path.suffix + ".meta.json")
        try:
            with open(meta_path, "w", encoding="utf-8") as meta_file:
                json.dump(
                    {
                        "storage_key": metadata.storage_key,
                        "original_filename": metadata.original_filename,
                        "mime_type": metadata.mime_type,
                        "file_size_bytes": metadata.file_size_bytes,
                        "checksum_sha256": metadata.checksum_sha256,
                        "created_at": metadata.created_at.isoformat(),
                    },
                    meta_file,
                )
        except Exception as exc:
            logger.warning("Could not persist sidecar metadata for %s: %s", storage_key, exc)

        return metadata

    def retrieve(self, storage_key: str) -> bytes:
        """Retrieve full file content as bytes."""
        path = self._resolve_secure_path(storage_key)
        if not path.is_file():
            raise StorageFileNotFoundError(f"Artifact object '{storage_key}' not found.")
        try:
            return path.read_bytes()
        except OSError as exc:
            raise StorageError(f"Failed to read artifact: {exc}") from exc

    def retrieve_stream(
        self, storage_key: str, chunk_size: int = 65536
    ) -> Generator[bytes, None, None]:
        """Stream file contents in bounded chunks."""
        path = self._resolve_secure_path(storage_key)
        if not path.is_file():
            raise StorageFileNotFoundError(f"Artifact object '{storage_key}' not found.")
        try:
            with open(path, "rb") as src:
                while True:
                    chunk = src.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        except OSError as exc:
            raise StorageError(f"Failed to stream artifact: {exc}") from exc

    def delete(self, storage_key: str) -> bool:
        """Delete a stored object and its sidecar metadata."""
        path = self._resolve_secure_path(storage_key)
        deleted = False
        if path.is_file():
            try:
                path.unlink()
                deleted = True
            except OSError as exc:
                raise StorageError(f"Failed to delete artifact file: {exc}") from exc

        meta_path = path.with_suffix(path.suffix + ".meta.json")
        if meta_path.is_file():
            with contextlib.suppress(OSError):
                meta_path.unlink()

        return deleted

    def exists(self, storage_key: str) -> bool:
        """Check if storage key exists as a regular file."""
        try:
            path = self._resolve_secure_path(storage_key)
            return path.is_file()
        except StorageSecurityError:
            return False

    def get_metadata(self, storage_key: str) -> StoredFileMetadata | None:
        """Retrieve safe metadata for a stored object."""
        path = self._resolve_secure_path(storage_key)
        if not path.is_file():
            return None

        meta_path = path.with_suffix(path.suffix + ".meta.json")
        if meta_path.is_file():
            try:
                with open(meta_path, encoding="utf-8") as f:
                    data = json.load(f)
                return StoredFileMetadata(
                    storage_key=data["storage_key"],
                    original_filename=data.get("original_filename", Path(storage_key).name),
                    mime_type=data.get("mime_type", "application/octet-stream"),
                    file_size_bytes=data.get("file_size_bytes", path.stat().st_size),
                    checksum_sha256=data.get("checksum_sha256", ""),
                    created_at=datetime.fromisoformat(data["created_at"]),
                )
            except Exception as exc:
                logger.warning("Could not read sidecar metadata: %s", exc)

        stat = path.stat()
        mime, _ = mimetypes.guess_type(path.name)
        return StoredFileMetadata(
            storage_key=storage_key,
            original_filename=path.name,
            mime_type=mime or "application/octet-stream",
            file_size_bytes=stat.st_size,
            checksum_sha256="",
            created_at=datetime.fromtimestamp(stat.st_ctime, tz=UTC),
        )

