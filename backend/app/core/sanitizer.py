"""
Input sanitization for Common Ground.
Defense-in-depth: strip dangerous content before it reaches the DB.
"""
import re

import bleach


# Markdown-safe tags that could appear in rich text
ALLOWED_TAGS = [
    "p", "br", "strong", "em", "b", "i", "a",
    "ul", "ol", "li", "code", "pre", "blockquote",
    "h1", "h2", "h3", "h4", "hr",
]
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title"],
}
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]

# Regex for safe URLs (http/https only)
_SAFE_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def sanitize_html(text: str) -> str:
    """Strip dangerous HTML tags while preserving safe formatting."""
    if not text:
        return text
    return bleach.clean(
        text,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )


def sanitize_plain_text(text: str) -> str:
    """Strip ALL HTML tags. For titles and other plain-text fields."""
    if not text:
        return text
    return bleach.clean(text, tags=[], attributes={}, strip=True)


def is_safe_url(url: str | None) -> bool:
    """
    Validate that a URL is safe (http or https only).
    Rejects javascript:, data:, vbscript:, and other dangerous schemes.
    """
    if not url:
        return True
    return bool(_SAFE_URL_RE.match(url.strip()))
