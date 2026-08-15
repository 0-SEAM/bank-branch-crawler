import json
from pathlib import Path

from .models import Branch
from .normalization import deduplicate
from .sources import SourceConfig, collect_source


def load_sources(path: Path) -> list[SourceConfig]:
    records = json.loads(path.read_text(encoding="utf-8"))
    return [SourceConfig(**record) for record in records if record.get("enabled", True)]


def collect(sources: list[SourceConfig]) -> tuple[list[Branch], list[str]]:
    branches: list[Branch] = []
    errors: list[str] = []
    for source in sources:
        try:
                source_branches = collect_source(source)
                if not source_branches:
                    errors.append(f"{source.bank_id}: adapter returned no valid Daejeon branches")
                branches.extend(source_branches)
        except Exception as error:  # isolate one bank/source from the rest of the run
            errors.append(f"{source.bank_id}: {error}")
    return deduplicate(branches), errors


def write_asset(branches: list[Branch], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "city": "대전",
        "generated_at": branches[0].collected_at if branches else None,
        "branches": [branch.to_json() for branch in branches],
    }
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)
