"""Pydantic schemas and sanitization for structured, versioned lesson content."""

from __future__ import annotations

import enum
import re
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


class BlockType(enum.StrEnum):
    """Supported lesson content block types."""

    HEADING = "heading"
    TEXT = "text"
    LIST = "list"
    CODE_EXAMPLE = "code_example"
    CALLOUT = "callout"
    IMAGE = "image"
    VIDEO = "video"


# ── Content Sanitization Helpers ───────────────────────

# Disallow unsafe HTML tags: <script>, <iframe>, <object>, <embed>, <form>, <link>, <style>, on* handlers
_UNSAFE_HTML_PATTERN = re.compile(
    r"<\s*(script|iframe|object|embed|form|link|style|meta|base)\b[^>]*>.*?</\s*\1\s*>|"
    r"<\s*(script|iframe|object|embed|form|link|style|meta|base)\b[^>]*/>|"
    r"\bon\w+\s*=",
    re.IGNORECASE | re.DOTALL,
)

_JAVASCRIPT_URI_PATTERN = re.compile(r"^\s*javascript:", re.IGNORECASE)


def sanitize_text(value: str) -> str:
    """Sanitize text to prevent script injection and dangerous HTML constructs."""
    if not value:
        return ""
    cleaned = _UNSAFE_HTML_PATTERN.sub("", value)
    return cleaned.strip()


def validate_url(url: str, allowed_schemes: tuple[str, ...] = ("http", "https")) -> str:
    """Validate resource URLs to prevent javascript: or file: attacks."""
    if not url:
        raise ValueError("URL cannot be empty.")
    if _JAVASCRIPT_URI_PATTERN.match(url):
        raise ValueError("javascript: URLs are strictly prohibited.")
    parsed = urlparse(url.strip())
    if parsed.scheme and parsed.scheme.lower() not in allowed_schemes:
        raise ValueError(
            f"URL scheme '{parsed.scheme}' is not allowed. Must be one of {allowed_schemes}."
        )
    return url.strip()


# ── Specific Block Data Schemas ────────────────────────


class HeadingBlockData(BaseModel):
    """Heading block: semantic sub-headings within a lesson."""

    level: int = Field(
        default=2, ge=2, le=4, description="Heading level (h2-h4 for accessible hierarchy)"
    )
    text: str = Field(min_length=1, max_length=300, description="Heading text")

    @field_validator("text", mode="before")
    @classmethod
    def sanitize_heading_text(cls, v: str) -> str:
        cleaned = sanitize_text(v)
        if not cleaned:
            raise ValueError("Heading text cannot be empty after sanitization.")
        return cleaned


class TextBlockData(BaseModel):
    """Text block: narrative explanation formatted in markdown."""

    text: str = Field(min_length=1, max_length=50000, description="Markdown narrative body")
    format: Literal["markdown", "plain"] = Field(default="markdown")

    @field_validator("text", mode="before")
    @classmethod
    def sanitize_body_text(cls, v: str) -> str:
        cleaned = sanitize_text(v)
        if not cleaned:
            raise ValueError("Text content cannot be empty after sanitization.")
        return cleaned


class ListBlockData(BaseModel):
    """List block: ordered or unordered list of bullet points."""

    ordered: bool = Field(
        default=False, description="True for numbered list, False for bulleted list"
    )
    items: list[str] = Field(min_length=1, max_length=100, description="List items")

    @field_validator("items", mode="before")
    @classmethod
    def sanitize_items(cls, v: list[str]) -> list[str]:
        cleaned_items = [sanitize_text(item) for item in v if sanitize_text(item)]
        if not cleaned_items:
            raise ValueError("List must contain at least one non-empty item.")
        return cleaned_items


class CodeExampleBlockData(BaseModel):
    """Code example block: syntax-highlighted code sample with optional caption."""

    language: str = Field(
        default="text",
        max_length=50,
        description="Programming language identifier (e.g. html, css, javascript, python, sql)",
    )
    code: str = Field(min_length=1, max_length=50000, description="Raw code content")
    caption: str | None = Field(
        default=None, max_length=300, description="Optional explanation or filename"
    )
    show_line_numbers: bool = Field(default=True)

    @field_validator("language", mode="before")
    @classmethod
    def normalize_language(cls, v: str) -> str:
        return v.strip().lower() if v else "text"


class CalloutBlockData(BaseModel):
    """Callout block: highlighted key concept, pro-tip, warning, or definition."""

    variant: Literal["info", "tip", "warning", "key_concept"] = Field(
        default="info", description="Visual styling and semantic intent"
    )
    title: str | None = Field(default=None, max_length=200, description="Optional callout title")
    text: str = Field(min_length=1, max_length=5000, description="Callout content body")

    @field_validator("title", "text", mode="before")
    @classmethod
    def sanitize_callout(cls, v: str | None) -> str | None:
        if v is None:
            return None
        cleaned = sanitize_text(v)
        return cleaned or None


class ImageBlockData(BaseModel):
    """Image block: accessible graphic or architectural diagram."""

    url: str = Field(description="URL to the image asset")
    alt_text: str = Field(
        min_length=3,
        max_length=500,
        description="Required alternative text for accessibility (screen readers)",
    )
    caption: str | None = Field(
        default=None, max_length=300, description="Optional visible caption"
    )

    @field_validator("url")
    @classmethod
    def check_image_url(cls, v: str) -> str:
        return validate_url(v)

    @field_validator("alt_text", mode="before")
    @classmethod
    def sanitize_alt(cls, v: str) -> str:
        cleaned = sanitize_text(v)
        if len(cleaned) < 3:
            raise ValueError("alt_text must be at least 3 characters long for accessibility.")
        return cleaned


class VideoBlockData(BaseModel):
    """Video block: approved external video stream or hosted walkthrough."""

    url: str = Field(description="URL to the video stream (e.g. YouTube, Vimeo, CDN)")
    title: str = Field(min_length=1, max_length=300, description="Title of the video")
    duration_seconds: int | None = Field(default=None, ge=1, le=86400)
    transcript_url: str | None = Field(
        default=None, description="Optional link to full transcript for accessibility"
    )

    @field_validator("url")
    @classmethod
    def check_video_url(cls, v: str) -> str:
        url = validate_url(v)
        parsed = urlparse(url)
        # Enforce approved hosts for video embeds
        allowed_hosts = {
            "youtube.com",
            "www.youtube.com",
            "youtu.be",
            "vimeo.com",
            "player.vimeo.com",
            "assets.skillverse.dev",
            "localhost",
            "127.0.0.1",
        }
        host = (parsed.hostname or "").lower()
        if host not in allowed_hosts and not host.endswith(".skillverse.dev"):
            raise ValueError(
                f"Video host '{host}' is not on the approved provider list. Allowed: YouTube, Vimeo, or SkillVerse CDN."
            )
        return url


# ── Generic Block Container ────────────────────────────


class LessonBlock(BaseModel):
    """A single validated content block in a lesson document."""

    id: str = Field(description="Unique block identifier")
    type: BlockType = Field(description="The block type")
    data: dict[str, Any] = Field(description="The validated block-specific payload")

    @field_validator("data", mode="after")
    @classmethod
    def validate_block_data(cls, v: dict[str, Any], info: Any) -> dict[str, Any]:
        """Validate data payload against the specific block type model."""
        block_type = info.data.get("type")
        if not block_type:
            return v

        type_map = {
            BlockType.HEADING: HeadingBlockData,
            BlockType.TEXT: TextBlockData,
            BlockType.LIST: ListBlockData,
            BlockType.CODE_EXAMPLE: CodeExampleBlockData,
            BlockType.CALLOUT: CalloutBlockData,
            BlockType.IMAGE: ImageBlockData,
            BlockType.VIDEO: VideoBlockData,
        }

        schema_cls = type_map.get(block_type)
        if schema_cls is None:
            raise ValueError(f"Unsupported block type: {block_type}")

        # Validate by instantiating the schema model, then serialize back to dict
        validated_obj = schema_cls.model_validate(v)
        return validated_obj.model_dump()


class SupportingResource(BaseModel):
    """External reference, documentation link, or cheat-sheet."""

    title: str = Field(min_length=1, max_length=200)
    url: str = Field(description="External resource URL")
    description: str | None = Field(default=None, max_length=500)

    @field_validator("url")
    @classmethod
    def check_resource_url(cls, v: str) -> str:
        return validate_url(v)


class LessonContentDocument(BaseModel):
    """Top-level structured lesson content document."""

    schema_version: str = Field(default="1.0", pattern=r"^\d+\.\d+$")
    learning_objectives: list[str] = Field(
        default_factory=list,
        description="Specific learning outcomes learners will achieve in this lesson",
    )
    blocks: list[LessonBlock] = Field(
        default_factory=list,
        description="Ordered sequence of lesson blocks",
    )
    resources: list[SupportingResource] = Field(
        default_factory=list,
        description="Optional supplementary readings and references",
    )
    accessibility_notes: str | None = Field(
        default=None,
        max_length=1000,
        description="Guidance for learners using assistive technologies",
    )
