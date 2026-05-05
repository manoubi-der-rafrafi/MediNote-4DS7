import re
import unicodedata


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = normalized.lower()
    normalized = re.sub(r"[^\w\s:.-]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def cleanup_text(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value).strip(" .;,\n\t")
    return cleaned


def sentence_case(value: str) -> str:
    cleaned = cleanup_text(value)
    if not cleaned:
        return ""
    return cleaned[0].upper() + cleaned[1:]
