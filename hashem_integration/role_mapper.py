from __future__ import annotations

from .config import get_hashem_default_role


class HashemRoleMapper:
    _MARKETING_KEYWORDS = ("marketing", "campagne", "campaign", "roi", "segment")
    _FOUNDER_KEYWORDS = ("direction", "founder", "executive", "revenue", "ca")

    def resolve(self, user_request: str) -> str:
        normalized = user_request.strip().lower()
        if any(keyword in normalized for keyword in self._MARKETING_KEYWORDS):
            return "marketing"
        if any(keyword in normalized for keyword in self._FOUNDER_KEYWORDS):
            return "founder"
        return get_hashem_default_role()
