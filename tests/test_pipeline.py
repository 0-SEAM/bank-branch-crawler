from pathlib import Path

from daedeok_branch_crawler.normalization import normalize_branch
from daedeok_branch_crawler.sources import SourceConfig, parse_html_table

FIXTURE = Path(__file__).parent / "fixtures" / "bank.html"


def test_html_table_keeps_daejeon_and_marks_official_foreign_support():
    source = SourceConfig("hana", "하나은행", "html_table", "https://example.test/bank")
    branches = parse_html_table(source, FIXTURE.read_text(encoding="utf-8"), "2026-08-16T12:00:00+09:00")

    assert len(branches) == 1
    assert branches[0].address.startswith("대전")
    assert branches[0].foreign_support is True
    assert branches[0].foreign_support_evidence == "글로벌 서비스"
    assert branches[0].latitude == 36.35149


def test_missing_coordinates_are_allowed():
    branch = normalize_branch(
        bank_id="kb", bank_name="KB국민은행", name="대전역점", address="대전광역시 동구 중앙로 1",
        source_url="https://example.test", latitude=None, longitude=None, evidence=None,
        verified_at="2026-08-16", collected_at="2026-08-16T12:00:00+09:00",
    )

    assert branch is not None
    assert branch.latitude is None
    assert branch.longitude is None
    assert branch.foreign_support is False
