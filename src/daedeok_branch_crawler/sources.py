from dataclasses import dataclass
import re
from typing import Any, Dict, Optional

import requests
from bs4 import BeautifulSoup

from .models import utc_now
from .normalization import normalize_branch


@dataclass(frozen=True)
class SourceConfig:
    bank_id: str
    bank_name: str
    adapter: str
    url: str
    city: str = "대전"
    enabled: bool = True
    bounds: Optional[Dict[str, int]] = None
    search: Optional[str] = None


def fetch_html(source: SourceConfig, timeout_seconds: float = 20) -> tuple[str, str]:
    response = requests.get(
        source.url,
        headers={"User-Agent": "0-SEAM-branch-crawler/0.1 (+respectful scheduled collection)"},
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    response.encoding = response.apparent_encoding or response.encoding
    return response.text, utc_now()


def _number(value: Any) -> Optional[float]:
    try:
        return float(value) if value is not None and str(value).strip() else None
    except (TypeError, ValueError):
        return None


def parse_json_ld(source: SourceConfig, html: str, collected_at: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    branches = []
    for node in soup.select('script[type="application/ld+json"]'):
        try:
            import json
            payload = json.loads(node.string or "")
        except (ValueError, TypeError):
            continue
        items = payload if isinstance(payload, list) else payload.get("@graph", [payload]) if isinstance(payload, dict) else []
        for item in items:
            if not isinstance(item, dict) or not item.get("name"):
                continue
            address = item.get("address", {})
            address_text = address if isinstance(address, str) else " ".join(
                str(address.get(key, "")) for key in ("postalCode", "addressRegion", "addressLocality", "streetAddress")
            )
            geo = item.get("geo", {}) or {}
            branches.append(normalize_branch(
                bank_id=source.bank_id, bank_name=source.bank_name, name=str(item["name"]),
                address=address_text, source_url=source.url, latitude=_number(geo.get("latitude")),
                longitude=_number(geo.get("longitude")), evidence=str(item.get("description", "")) or None,
                verified_at=collected_at[:10], collected_at=collected_at, city=source.city,
            ))
    return [branch for branch in branches if branch is not None]


def collect_hana_json(source: SourceConfig) -> list:
    bounds = source.bounds or {
        "x1": 127250000,
        "x2": 127550000,
        "y1": 36250000,
        "y2": 36550000,
    }
    params = {
        "search_flag": "",
        "tab": "",
        "lang": "ko",
        "seq_no": "",
        "type": "",
        "search_type": "0",
        "search_word": "",
        **{key: str(value) for key, value in bounds.items()},
    }
    response = requests.post(
        source.url,
        data=params,
        headers={
            "User-Agent": "0-SEAM-branch-crawler/0.1 (+respectful scheduled collection)",
            "Referer": "https://openhanafn.ttmap.co.kr/content.jsp",
        },
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    collected_at = utc_now()
    branches = []
    for item in payload.get("resultList", []):
        evidence = "글로벌 데스크 표기" if item.get("global_desk_yn") == "Y" else None
        branch = normalize_branch(
            bank_id=source.bank_id,
            bank_name=source.bank_name,
            name=str(item.get("branch_name", "")),
            address=str(item.get("address_new") or item.get("address_detail") or ""),
            source_url="https://www.kebhana.com/cont/util/util04/util0401/index.jsp",
            latitude=_number(item.get("map_y")) / 1000000 if _number(item.get("map_y")) is not None else None,
            longitude=_number(item.get("map_x")) / 1000000 if _number(item.get("map_x")) is not None else None,
            evidence=evidence,
            verified_at=collected_at[:10],
            collected_at=collected_at,
            city=source.city,
        )
        if branch is not None:
            branches.append(branch)
    return branches


def parse_kb_response(text: str) -> list:
    items = []
    for raw_item in re.findall(r"\{([^{}]*)\}", text):
        item = dict(re.findall(r'([A-Za-z][A-Za-z0-9_]*):"([^"]*)"', raw_item))
        if item.get("name") and item.get("wgsx") and item.get("wgsy"):
            items.append(item)
    return items


def collect_kb_json(source: SourceConfig) -> list:
    params = {
        "searchtype": "branch_total",
        "type01": "0",
        "type04": "500",
        "type05": "1",
        "type07": "0",
        "type08": "0",
        "type10": "100",
        "type24": "0",
        "type25": "0",
        "type26": "0",
        "type28": "0",
        "type30": "0",
        "type31": "0",
        "type32": "0",
        "type33": "0",
        "type34": source.search or source.city,
        "type35": "",
        "USER_TYPE": "03",
    }
    response = requests.post(
        source.url + "&asfilecode=548565&RType=json",
        data=params,
        headers={
            "User-Agent": "0-SEAM-branch-crawler/0.1 (+respectful scheduled collection)",
            "Referer": "https://omoney.kbstar.com/quics?page=C016505",
        },
        timeout=20,
    )
    response.raise_for_status()
    response.encoding = "euc-kr"
    collected_at = utc_now()
    branches = []
    for item in parse_kb_response(response.text):
        branch = normalize_branch(
            bank_id=source.bank_id,
            bank_name=source.bank_name,
            name=item["name"],
            address=" ".join(part for part in (item.get("road"), item.get("road2")) if part),
            source_url="https://omoney.kbstar.com/quics?page=C016505",
            latitude=_number(item.get("wgsy")),
            longitude=_number(item.get("wgsx")),
            evidence=None,
            verified_at=collected_at[:10],
            collected_at=collected_at,
            city=source.city,
        )
        if branch is not None:
            branches.append(branch)
    return branches


def parse_html_table(source: SourceConfig, html: str, collected_at: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    branches = []
    for row in soup.select("table tr"):
        cells = [" ".join(cell.stripped_strings) for cell in row.select("th, td")]
        if len(cells) < 2 or cells[0] in {"지점명", "지점"}:
            continue
        branches.append(normalize_branch(
            bank_id=source.bank_id, bank_name=source.bank_name, name=cells[0], address=cells[1],
            source_url=source.url, latitude=_number(cells[2]) if len(cells) > 2 else None,
            longitude=_number(cells[3]) if len(cells) > 3 else None,
            evidence=cells[4] if len(cells) > 4 else None, verified_at=collected_at[:10],
            collected_at=collected_at, city=source.city,
        ))
    return [branch for branch in branches if branch is not None]


def collect_source(source: SourceConfig) -> list:
    if source.adapter == "hana_json":
        return collect_hana_json(source)
    if source.adapter == "kb_json":
        return collect_kb_json(source)
    html, collected_at = fetch_html(source)
    if source.adapter == "json_ld":
        return parse_json_ld(source, html, collected_at)
    if source.adapter == "html_table":
        return parse_html_table(source, html, collected_at)
    raise ValueError(f"Unsupported adapter: {source.adapter}")
