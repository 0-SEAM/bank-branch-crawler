from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass(frozen=True)
class Branch:
    id: str
    bank_id: str
    bank_name: str
    name: str
    address: str
    city: str
    latitude: Optional[float]
    longitude: Optional[float]
    foreign_support: bool
    foreign_support_evidence: Optional[str]
    source_url: str
    verified_at: str
    collected_at: str

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


def utc_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")
