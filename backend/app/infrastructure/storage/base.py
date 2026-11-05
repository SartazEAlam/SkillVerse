"""Provider-neutral artifact storage interface and metadata schemas."""

from __future__ import annotations

import abc
from collections.abc import Generator
from dataclasses import dataclass
from datetime import datetime
from typing import BinaryIO


class StorageError(Exception):
    """Base exception for artifact storage operations."""

    def __init__(self, message: str, code: str = "STORAGE_ERROR", status_code: int = 500) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class StorageFileNotFoundError(StorageError):
    """Raised when a requested storage object is not found."""

    def __init__(self, message: str = "Artifact object not found.") -> None:
        super().__init__(message, code="ARTIFACT_NOT_FOUND", status_code=404)


class StorageFileTooLargeError(StorageError):
    """Raised when an uploaded file exceeds the configured maximum size."""

    def __init__(self, message: str = "File exceeds the maximum allowable size.") -> None:
        super().__init__(message, code="FILE_TOO_LARGE", status_code=413)


class StorageInvalidTypeError(StorageError):
    """Raised when an uploaded file type or extension is not allowed."""

    def __init__(self, message: str = "File type or extension is not permitted.") -> None:
        super().__init__(message, code="INVALID_FILE_TYPE", status_code=415)


class StorageSecurityError(StorageError):
    """Raised when a potential path traversal or security violation is detected."""

    def __init__(self, message: str = "Storage access security violation.") -> None:
        super().__init__(message, code="STORAGE_SECURITY_VIOLATION", status_code=400)


@dataclass(frozen=True)
class StoredFileMetadata:
    """Safe metadata describing a persisted storage object without exposing internal filesystem paths."""

    storage_key: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    checksum_sha256: str
    created_at: datetime


class StorageInterface(abc.ABC):
    """Abstract interface defining the boundary for secure object and artifact storage."""

    @abc.abstractmethod
    def store(
        self,
        file_data: bytes | BinaryIO,
        filename: str,
        content_type: str | None = None,
        prefix: str = "artifacts",
    ) -> StoredFileMetadata:
        """Persist a file and return its safe metadata and generated storage key."""
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve(self, storage_key: str) -> bytes:
        """Retrieve full file contents as bytes."""
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_stream(
        self, storage_key: str, chunk_size: int = 65536
    ) -> Generator[bytes, None, None]:
        """Stream file contents in bounded chunks to prevent high memory usage."""
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, storage_key: str) -> bool:
        """Delete a stored object by its storage key."""
        raise NotImplementedError

    @abc.abstractmethod
    def exists(self, storage_key: str) -> bool:
        """Check whether an object exists in storage."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_metadata(self, storage_key: str) -> StoredFileMetadata | None:
        """Retrieve safe metadata for a stored object."""
        raise NotImplementedError

