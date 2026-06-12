import unicodedata


def sanitize_url(url: str) -> str:
    """Strips invisible Unicode formatting characters (e.g. the left-to-right
    mark U+200E that Instagram's share sheet prepends to copied links) and
    surrounding whitespace, which otherwise make yt-dlp reject the URL as
    invalid."""
    cleaned = "".join(ch for ch in url if unicodedata.category(ch) != "Cf")
    return cleaned.strip()
