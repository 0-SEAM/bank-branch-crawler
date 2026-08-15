import re
import unicodedata
from collections.abc import Iterable
from typing import Optional

from .models import Branch

DAEJEON_MARKERS = ("대전", "大田")
FOREIGN_MARKERS = ("글로벌", "외국인", "foreign", "international")


def make_id(bank_id: str, name: str, address: str) -> str:
    value = unicodedata.normalize("NFKC", f"{bank_id}-{name}-{address}").lower()
    value = re.sub(r"[^a-z0-9가-힣]+", "-", value).strip("-")
    return value


def normalize_branch(
    *,
    bank_id: str,
    bank_name: str,
    name: str,
    address: str,
    source_url: str,
    latitude: Optional[float],
    longitude: Optional[float],
    evidence: Optional[str],
    verified_at: str,
    collected_at: str,
    city: str = "대전",
) -> Optional[Branch]:
    clean_name = " ".join(name.split())
    clean_address = " ".join(address.split())
    if not clean_name or not clean_address or not any(marker in clean_address for marker in DAEJEON_MARKERS):
        return None

    foreign_text = f"{clean_name} {evidence or ''}".lower()
    foreign_support = any(marker in foreign_text for marker in FOREIGN_MARKERS)
    return Branch(
        id=make_id(bank_id, clean_name, clean_address),
        bank_id=bank_id,
        bank_name=bank_name,
        name=clean_name,
        address=clean_address,
        city=city,
        latitude=latitude,
        longitude=longitude,
        foreign_support=foreign_support,
        foreign_support_evidence=evidence if foreign_support else None,
        source_url=source_url,
        verified_at=verified_at,
        collected_at=collected_at,
    )


def deduplicate(branches: Iterable[Branch]) -> list[Branch]:
    return list({branch.id: branch for branch in branches}.values())
