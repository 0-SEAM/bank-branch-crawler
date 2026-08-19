# Daejeon Bank Branch Crawler

대전 생활권 은행 지점 정보를 공식 웹 페이지에서 수집해 0:SEAM의 정적 JSON 에셋으로 만드는 독립 프로젝트입니다.

## Pipeline

```text
bank source -> source adapter -> common branch schema -> validation -> frontend/src/data/bank-branches.json
```

은행별 수집기는 `src/daedeok_branch_crawler/sources.py`의 어댑터로 격리됩니다. 한 소스가 실패해도 다른 소스의 결과와 이전 산출물은 삭제하지 않습니다.

## Run

```bash
cd crawler
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -e '.[test]'
python -m daedeok_branch_crawler.cli --config config/sources.json --output ../frontend/src/data/
pytest
```

실제 운영에서는 각 은행의 공식 지점 검색 페이지 URL과 HTML 구조를 `config/sources.json`에 등록하고, 사이트 이용약관과 robots.txt를 확인한 뒤 낮은 요청 빈도로 실행합니다. 로그에는 실패한 소스만 남기고 기존 JSON은 성공한 전체 검증이 끝날 때까지 교체하지 않습니다.

## Data rules

- 대전 주소만 통과시킵니다.
- 이름과 주소가 없는 항목은 제외합니다.
- 좌표가 없으면 지점은 보존하지만 지도/거리 추천 대상에서 제외할 수 있도록 `latitude`와 `longitude`를 `null`로 둡니다.
- `foreign_support`는 공식 페이지에 `글로벌`, `외국인`, `외국인 전용` 등의 표기가 있을 때만 `true`입니다. 판단 문구를 `foreign_support_evidence`에 보존합니다.
- 모든 지점에 원문 URL과 `verified_at`을 저장합니다.

## Source configuration

`config/sources.json`은 어댑터 이름, 은행 식별자, 공식 URL을 관리합니다. 현재 `hana_json`은 하나은행 공식 영업점 iframe의 JSON 엔드포인트를, `kb_json`은 KB국민은행 공식 지점검색 화면의 레거시 JSON 엔드포인트를 사용합니다. `html_table`과 `json_ld`는 일반적인 표/JSON-LD 페이지용으로 유지합니다. 좌표는 페이지에 있으면 우선 사용하고, 없는 경우 별도 geocoder를 호출하지 않고 `null`로 둡니다.
