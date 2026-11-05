"""Focused unit tests for the artifact storage abstraction and local storage security."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from app.config import Settings
from app.infrastructure.storage import (
    LocalStorageService,
    StorageError,
    StorageFileNotFoundError,
    StorageFileTooLargeError,
    StorageInvalidTypeError,
    StorageSecurityError,
    get_storage_service,
    reset_storage_service,
)


@pytest.fixture
def temp_storage(tmp_path: Path) -> LocalStorageService:
    """Fixture providing an isolated local storage service backed by a temporary directory."""
    return LocalStorageService(
        base_dir=tmp_path / "artifacts",
        max_file_size_bytes=1024 * 1024,  # 1 MB limit for tests
        allowed_extensions=[".png", ".jpg", ".jpeg", ".pdf", ".zip", ".tar.gz", ".txt", ".md", ".json", ".webp"],
    )


class TestLocalStorageService:
    """Test suite for LocalStorageService functionality and security boundaries."""

    def test_store_and_retrieve_valid_text_file(self, temp_storage: LocalStorageService) -> None:
        """Stores a valid text file and verifies retrieval, metadata, and checksum."""
        content = b"SkillVerse Phase 9 Project Artifact Submission"
        metadata = temp_storage.store(
            file_data=content,
            filename="my_reflection.md",
            content_type="text/markdown",
        )

        assert metadata.original_filename == "my_reflection.md"
        assert metadata.file_size_bytes == len(content)
        assert metadata.mime_type == "text/markdown"
        assert len(metadata.checksum_sha256) == 64
        # Storage key must be server-generated and NOT contain original filename
        assert "my_reflection.md" not in metadata.storage_key
        assert metadata.storage_key.startswith("artifacts/")

        # Verify object existence
        assert temp_storage.exists(metadata.storage_key) is True

        # Verify retrieval matches original content exactly
        retrieved = temp_storage.retrieve(metadata.storage_key)
        assert retrieved == content

        # Verify stream retrieval
        chunks = list(temp_storage.retrieve_stream(metadata.storage_key, chunk_size=10))
        assert b"".join(chunks) == content

    def test_store_and_retrieve_binary_with_magic_bytes(self, temp_storage: LocalStorageService) -> None:
        """Verifies binary file with valid magic bytes (PDF header)."""
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
        metadata = temp_storage.store(
            file_data=pdf_content,
            filename="Architecture_Design.pdf",
            content_type="application/pdf",
        )

        assert metadata.original_filename == "Architecture_Design.pdf"
        assert metadata.file_size_bytes == len(pdf_content)
        assert temp_storage.exists(metadata.storage_key) is True

        data = temp_storage.retrieve(metadata.storage_key)
        assert data.startswith(b"%PDF-")

    def test_delete_existing_file(self, temp_storage: LocalStorageService) -> None:
        """Verifies deleting an existing storage object removes file and sidecar metadata."""
        content = b"temporary test artifact"
        metadata = temp_storage.store(content, "temp.txt")

        assert temp_storage.exists(metadata.storage_key) is True
        deleted = temp_storage.delete(metadata.storage_key)
        assert deleted is True

        # Subsequent existence check should be False
        assert temp_storage.exists(metadata.storage_key) is False

        # Retrieval should raise StorageFileNotFoundError
        with pytest.raises(StorageFileNotFoundError):
            temp_storage.retrieve(metadata.storage_key)

    def test_delete_non_existent_file(self, temp_storage: LocalStorageService) -> None:
        """Deleting a non-existent file returns False without raising an unhandled error."""
        assert temp_storage.delete("artifacts/2026/10/non_existent_file.txt") is False

    def test_reject_oversized_file(self, temp_storage: LocalStorageService) -> None:
        """Rejects files that exceed the configured size limit and cleans up partial writes."""
        # Configured limit is 1 MB; create 1.2 MB of dummy data
        oversized = b"X" * (1024 * 1024 + 200)

        with pytest.raises(StorageFileTooLargeError) as exc_info:
            temp_storage.store(oversized, "big_file.txt")

        assert "exceeds maximum limit" in str(exc_info.value)

    def test_reject_blocked_executable_extensions(self, temp_storage: LocalStorageService) -> None:
        """Rejects dangerous executable extensions immediately regardless of allowlist."""
        blocked_samples = [
            ("malware.exe", b"MZ\x90\x00"),
            ("script.sh", b"#!/bin/bash\nrm -rf /"),
            ("payload.bat", b"@echo off\necho pwned"),
            ("exploit.py", b"import os\nos.system('calc')"),
            ("trojan.dll", b"MZ..."),
            ("stealer.js", b"console.log(process.env)"),
            ("phish.html", b"<script>alert(1)</script>"),
        ]

        for filename, data in blocked_samples:
            with pytest.raises(StorageInvalidTypeError) as exc_info:
                temp_storage.store(data, filename)
            assert "blocked" in str(exc_info.value).lower() or "not permitted" in str(exc_info.value).lower()

    def test_reject_magic_byte_mismatch(self, temp_storage: LocalStorageService) -> None:
        """Rejects files whose header signature does not match the extension."""
        # Disguised file: text content with .png extension
        fake_png = b"This is not a real PNG image file at all."
        with pytest.raises(StorageInvalidTypeError) as exc_info:
            temp_storage.store(fake_png, "avatar.png")

        assert "binary signature" in str(exc_info.value)

        # Disguised file: text content with .pdf extension
        fake_pdf = b"Hello, I am pretending to be a PDF document."
        with pytest.raises(StorageInvalidTypeError) as exc_info:
            temp_storage.store(fake_pdf, "document.pdf")

        assert "binary signature" in str(exc_info.value)

    def test_store_and_retrieve_valid_webp_image(self, temp_storage: LocalStorageService) -> None:
        """Stores a valid WebP image with RIFF and WEBP signature markers."""
        # 12-byte minimum header: RIFF + 4-byte size + WEBP + payload
        webp_content = b"RIFF\x24\x00\x00\x00WEBPVP8 " + b"\x00" * 32
        metadata = temp_storage.store(
            file_data=webp_content,
            filename="screenshot.webp",
            content_type="image/webp",
        )

        assert metadata.original_filename == "screenshot.webp"
        assert metadata.file_size_bytes == len(webp_content)
        assert metadata.mime_type == "image/webp"
        assert temp_storage.exists(metadata.storage_key) is True

        retrieved = temp_storage.retrieve(metadata.storage_key)
        assert retrieved.startswith(b"RIFF")
        assert retrieved[8:12] == b"WEBP"

    def test_reject_webp_invalid_riff_header(self, temp_storage: LocalStorageService) -> None:
        """Rejects files with .webp extension if byte offset 0 is not RIFF."""
        bad_riff = b"DIFF\x24\x00\x00\x00WEBPVP8 " + b"\x00" * 32
        with pytest.raises(StorageInvalidTypeError) as exc_info:
            temp_storage.store(bad_riff, "invalid_header.webp")

        assert "binary signature" in str(exc_info.value)

    def test_reject_webp_missing_webp_marker(self, temp_storage: LocalStorageService) -> None:
        """Rejects files with .webp extension if byte offset 8 is not WEBP (e.g. AVI/WAV RIFF)."""
        bad_marker = b"RIFF\x24\x00\x00\x00AVIFVP8 " + b"\x00" * 32
        with pytest.raises(StorageInvalidTypeError) as exc_info:
            temp_storage.store(bad_marker, "not_a_webp.webp")

        assert "binary signature" in str(exc_info.value)

    def test_reject_webp_arbitrary_text_renamed(self, temp_storage: LocalStorageService) -> None:
        """Rejects arbitrary text disguised with a .webp extension."""
        text_payload = b"Hello, I am just an ordinary text file disguised with a webp extension."
        with pytest.raises(StorageInvalidTypeError) as exc_info:
            temp_storage.store(text_payload, "disguised.webp")

        assert "binary signature" in str(exc_info.value)

    def test_reject_webp_truncated_header(self, temp_storage: LocalStorageService) -> None:
        """Rejects files shorter than 12 bytes claiming to be WebP."""
        short_header = b"RIFF123"  # Only 7 bytes
        with pytest.raises(StorageInvalidTypeError) as exc_info:
            temp_storage.store(short_header, "short.webp")

        assert "binary signature" in str(exc_info.value)

    def test_reject_empty_signature_checked_file(self, temp_storage: LocalStorageService) -> None:
        """Rejects 0-byte uploads for binary formats requiring signature verification."""
        for ext in (".webp", ".png", ".jpg", ".pdf", ".zip"):
            with pytest.raises(StorageInvalidTypeError) as exc_info:
                temp_storage.store(b"", f"empty{ext}")
            assert "binary signature" in str(exc_info.value)

    def test_containment_rejects_sibling_directory_sharing_prefix(self, temp_storage: LocalStorageService) -> None:
        """Strictly rejects sibling directories that share the storage root string prefix."""
        # Genuine inside path
        valid_child = temp_storage.base_dir / "2026" / "11" / "file.txt"
        assert temp_storage._is_within_base_dir(valid_child) is True

        # Sibling directory sharing the string prefix
        sibling_dir = temp_storage.base_dir.parent / (temp_storage.base_dir.name + "_sibling")
        sibling_file = sibling_dir / "stolen_data.txt"
        assert temp_storage._is_within_base_dir(sibling_file) is False

        # Storage root directory itself
        assert temp_storage._is_within_base_dir(temp_storage.base_dir) is False

        # Parent directory
        assert temp_storage._is_within_base_dir(temp_storage.base_dir.parent) is False

    def test_path_traversal_attempts_rejected(self, temp_storage: LocalStorageService) -> None:
        """Strictly blocks path traversal sequences in storage keys."""
        traversal_keys = [
            "../etc/passwd",
            "../../windows/system32/cmd.exe",
            "artifacts/../../secret.txt",
            "..\\..\\boot.ini",
            "/absolute/root/file.txt",
            "artifacts/subdir/../../../escaped.txt",
            "artifacts/\0/nullbyte.txt",
        ]

        for bad_key in traversal_keys:
            with pytest.raises(StorageSecurityError):
                temp_storage.retrieve(bad_key)

            with pytest.raises(StorageSecurityError):
                temp_storage.delete(bad_key)

            assert temp_storage.exists(bad_key) is False

    def test_no_filesystem_paths_in_public_metadata(self, temp_storage: LocalStorageService) -> None:
        """Ensures internal base directories and OS paths are not leaked in StoredFileMetadata."""
        metadata = temp_storage.store(b"clean content", "project_doc.txt")

        # The storage key must be relative and portable
        assert not metadata.storage_key.startswith("/")
        assert not metadata.storage_key.startswith("C:\\")
        assert not metadata.storage_key.startswith("D:\\")
        assert str(temp_storage.base_dir) not in metadata.storage_key

    def test_get_metadata_for_existing_and_missing(self, temp_storage: LocalStorageService) -> None:
        """Verifies get_metadata retrieves persisted metadata or returns None when missing."""
        content = b"metadata verification content"
        meta = temp_storage.store(content, "manifest.json", content_type="application/json")

        fetched = temp_storage.get_metadata(meta.storage_key)
        assert fetched is not None
        assert fetched.storage_key == meta.storage_key
        assert fetched.original_filename == "manifest.json"
        assert fetched.mime_type == "application/json"
        assert fetched.file_size_bytes == len(content)
        assert fetched.checksum_sha256 == meta.checksum_sha256

        # Missing key returns None
        missing = temp_storage.get_metadata("artifacts/2026/10/non_existent.json")
        assert missing is None

    def test_streaming_input_source(self, temp_storage: LocalStorageService) -> None:
        """Verifies that store accepts a BinaryIO stream like BytesIO or SpooledTemporaryFile."""
        stream = io.BytesIO(b"streaming input bytes data")
        metadata = temp_storage.store(stream, "streamed.txt")

        assert metadata.file_size_bytes == 26
        assert temp_storage.retrieve(metadata.storage_key) == b"streaming input bytes data"


class TestStorageFactory:
    """Tests for storage service factory resolution and settings."""

    def test_factory_returns_local_storage(self) -> None:
        reset_storage_service()
        settings = Settings(
            storage_provider="local",
            storage_local_root="uploads/test_artifacts",
            storage_max_file_size_mb=15,
        )
        service = get_storage_service(settings)
        assert isinstance(service, LocalStorageService)
        assert service.max_file_size_bytes == 15 * 1024 * 1024

    def test_factory_raises_for_unsupported_s3(self) -> None:
        settings = Settings(storage_provider="s3")
        with pytest.raises(NotImplementedError) as exc_info:
            get_storage_service(settings)
        assert "not yet configured" in str(exc_info.value)

    def test_factory_raises_for_disabled_storage(self) -> None:
        settings = Settings(storage_provider="disabled")
        with pytest.raises(StorageError) as exc_info:
            get_storage_service(settings)
        assert "explicitly disabled" in str(exc_info.value)

