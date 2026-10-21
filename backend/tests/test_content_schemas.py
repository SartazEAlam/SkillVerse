"""Unit tests for lesson content block schemas, rich-text sanitization, and URL security."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.modules.courses.content_schemas import (
    CalloutBlockData,
    CodeExampleBlockData,
    HeadingBlockData,
    ImageBlockData,
    LessonBlock,
    LessonContentDocument,
    ListBlockData,
    TextBlockData,
    VideoBlockData,
    sanitize_text,
    validate_url,
)


def test_sanitize_text_strips_scripts_and_malicious_tags() -> None:
    """Ensure dangerous HTML script tags and javascript execution vectors are neutralized."""
    dirty = "Welcome to SkillVerse! <script>alert('pwned')</script> Let's learn."
    clean = sanitize_text(dirty)
    assert "<script>" not in clean
    assert "alert" not in clean
    assert "Welcome to SkillVerse!" in clean

    # Allow safe formatting tags like <strong> and <em>
    safe_markup = "This is <strong>important</strong> and <em>notable</em>."
    clean_safe = sanitize_text(safe_markup)
    assert "<strong>important</strong>" in clean_safe
    assert "<em>notable</em>" in clean_safe


def test_validate_url_rejects_javascript_and_disallowed_schemes() -> None:
    """Validate that javascript: and unexpected URI schemes are rejected."""
    with pytest.raises(ValueError, match="javascript: URLs are strictly prohibited"):
        validate_url("javascript:alert(1)")

    with pytest.raises(ValueError, match="URL scheme 'ftp' is not allowed"):
        validate_url("ftp://example.com/file.txt")

    assert validate_url("https://example.com/image.png") == "https://example.com/image.png"


def test_heading_block_validation() -> None:
    """Test heading block level boundaries (h2-h4) and sanitization."""
    valid_h2 = HeadingBlockData(level=2, text="Introduction to Algorithms")
    assert valid_h2.level == 2
    assert valid_h2.text == "Introduction to Algorithms"

    # h1 is reserved for page titles, so level 1 must fail validation
    with pytest.raises(ValidationError):
        HeadingBlockData(level=1, text="Main Page Title")

    # level 5 is too deep for our accessible heading hierarchy
    with pytest.raises(ValidationError):
        HeadingBlockData(level=5, text="Sub sub sub sub heading")

    # Strips malicious scripts from heading text
    sanitized = HeadingBlockData(level=2, text="Topic <script>alert(1)</script>")
    assert "<script>" not in sanitized.text


def test_text_block_validation() -> None:
    """Test markdown narrative block sanitization and formats."""
    text_blk = TextBlockData(format="markdown", text="## Getting Started\nThis is **markdown**.")
    assert text_blk.format == "markdown"
    assert "**markdown**" in text_blk.text

    with pytest.raises(ValidationError):
        TextBlockData(format="markdown", text="")


def test_list_block_validation() -> None:
    """Test ordered and unordered list validation and sanitization."""
    bullet_list = ListBlockData(ordered=False, items=["Item 1", "Item 2", "Item 3"])
    assert not bullet_list.ordered
    assert len(bullet_list.items) == 3

    # Empty list must fail
    with pytest.raises(ValidationError):
        ListBlockData(ordered=True, items=[])


def test_code_example_block_validation() -> None:
    """Test code example block language normalization and code payload."""
    code_blk = CodeExampleBlockData(
        language="JavaScript",
        code="const x = 42;\nconsole.log(x);",
        caption="Basic Variable Declaration",
    )
    assert code_blk.language == "javascript"
    assert "const x = 42;" in code_blk.code


def test_callout_block_validation() -> None:
    """Test callout variants and body text."""
    callout = CalloutBlockData(
        variant="key_concept",
        title="Mental Model",
        text="State flows down, events bubble up.",
    )
    assert callout.variant == "key_concept"
    assert callout.text == "State flows down, events bubble up."

    # Invalid variant fails validation
    with pytest.raises(ValidationError):
        CalloutBlockData(variant="invalid_variant", text="Invalid")


def test_image_block_accessibility_and_security() -> None:
    """Test image block requires valid URL and accessible alt_text."""
    img = ImageBlockData(
        url="https://assets.skillverse.dev/diagrams/arch.png",
        alt_text="System architecture block diagram showing microservices",
    )
    assert img.url.startswith("https://")
    assert len(img.alt_text) >= 3

    # Reject javascript: url
    with pytest.raises(ValidationError):
        ImageBlockData(url="javascript:attack()", alt_text="Valid alt text")

    # Reject missing or insufficient alt_text
    with pytest.raises(ValidationError):
        ImageBlockData(url="https://assets.skillverse.dev/img.png", alt_text="a")


def test_video_block_host_allowlist() -> None:
    """Test video embed URLs are restricted to approved streaming hosts."""
    yt = VideoBlockData(
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        title="Rick Astley - Never Gonna Give You Up",
    )
    assert "youtube.com" in yt.url

    vimeo = VideoBlockData(
        url="https://player.vimeo.com/video/12345678",
        title="Platform Walkthrough",
    )
    assert "vimeo.com" in vimeo.url

    # Untrusted domain must fail validation
    with pytest.raises(ValidationError):
        VideoBlockData(
            url="https://malicious-site.ru/exploit.mp4",
            title="Untrusted Video Stream",
        )


def test_lesson_block_container_and_unknown_type() -> None:
    """Test generic LessonBlock validation container and rejection of unsupported block types."""
    valid_blk = LessonBlock(
        id="blk-1",
        type="heading",
        data={"level": 2, "text": "Lesson Overview"},
    )
    assert valid_blk.type == "heading"
    assert valid_blk.data["text"] == "Lesson Overview"

    # Unsupported block type fails
    with pytest.raises(ValidationError):
        LessonBlock(
            id="blk-2",
            type="unsupported_type",
            data={"foo": "bar"},
        )


def test_lesson_content_document_validation() -> None:
    """Test full LessonContentDocument assembly with multiple valid blocks."""
    doc = LessonContentDocument(
        schema_version="1.0",
        learning_objectives=["Understand CSS Grid layouts."],
        blocks=[
            LessonBlock(
                id="blk-h",
                type="heading",
                data={"level": 2, "text": "CSS Grid Architecture"},
            ),
            LessonBlock(
                id="blk-t",
                type="text",
                data={"format": "markdown", "text": "Grid allows 2D responsive alignment."},
            ),
            LessonBlock(
                id="blk-c",
                type="code_example",
                data={"language": "css", "code": ".container { display: grid; }"},
            ),
        ],
    )
    assert doc.schema_version == "1.0"
    assert len(doc.blocks) == 3
    assert len(doc.learning_objectives) == 1

    # Malformed schema version fails regex
    with pytest.raises(ValidationError):
        LessonContentDocument(schema_version="invalid-version", blocks=[])
