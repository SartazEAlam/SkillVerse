"""Storage service factory for dependency injection."""

from __future__ import annotations

import logging
from typing import Any

from app.config import settings as app_settings
from app.infrastructure.storage.base import StorageError, StorageInterface
from app.infrastructure.storage.local_storage import LocalStorageService

logger = logging.getLogger("skillverse.storage")

_storage_instance: StorageInterface | None = None


def get_storage_service(custom_settings: Any = None) -> StorageInterface:
    """Return the configured singleton storage service instance.

    Uses `settings.storage_provider` to resolve the active implementation:
    - 'local': LocalStorageService with disk bounds and server-generated keys.
    - 's3': Raises NotImplementedError (future production provider).
    - 'disabled': Raises StorageError indicating storage is not available.
    """
    global _storage_instance

    if _storage_instance is not None and custom_settings is None:
        return _storage_instance

    cfg = custom_settings or app_settings
    provider = getattr(cfg, "storage_provider", "local").lower()

    if provider == "local":
        instance = LocalStorageService(
            base_dir=cfg.storage_local_root,
            max_file_size_bytes=cfg.storage_max_file_size_mb * 1024 * 1024,
            allowed_extensions=cfg.storage_allowed_extensions,
        )
    elif provider == "s3":
        raise NotImplementedError(
            "S3/MinIO storage provider is not yet configured. "
            "Use 'local' storage provider for development and testing environments."
        )
    elif provider == "disabled":
        raise StorageError("Artifact storage is explicitly disabled in application configuration.")
    else:
        raise ValueError(f"Unknown storage provider: '{provider}'")

    if custom_settings is None:
        _storage_instance = instance
    return instance


def reset_storage_service() -> None:
    """Reset the singleton storage instance (used in test fixtures)."""
    global _storage_instance
    _storage_instance = None

