#!/usr/bin/env python3
"""아웃라인 정량 검증 스크립트 (범용).

사용법: python workflow/outline_validate.py <project_dir>
예시:   python workflow/outline_validate.py ssulhwa
출력:   JSON 형식의 검증 결과
"""

import io
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

# Windows 환경 UTF-8 출력 보장
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent


def load_project_config(project_dir: Path) -> dict:
    """project.yaml 로드."""
    config_path = project_dir / "project.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"project.yaml을 찾을 수 없음: {config_path}")

    text = config_path.read_text(encoding="utf-8")

    if yaml:
        return yaml.safe_load(text)
    else:
        raise ImportError("PyYAML이 필요합니다: pip install pyyaml")


def get_preproduction_config(config: dict) -> dict:
    """preproduction 설정을 기본값과 병합하여 반환."""
    defaults = {
        "outline": {
            "outline_file": "lore/episode-outline.md",
            "ep_fields": ["핵심 사건", "감정 전개", "떡밥", "엔딩 훅"],
            "supplementary_sections": [],
        },
        "review": {
            "min_foreshadow_recovery_rate": 0.7,
            "max_revision_loops": 2,
        },
    }
    preprod = config.get("preproduction", {})
    outline_cfg = dict(defaults["outline"])
    outline_cfg.update(preprod.get("outline", {}))
    review_cfg = dict(defaults["review"])
    review_cfg.update(preprod.get("review", {}))
    return {"outline": outline_cfg, "review": review_cfg}


def parse_episodes(text: str) -> list[dict]:
    """episode-outline.md에서 에피소드 블록을 파싱.

    각 에피소드는 ### EP-XX: 제목 헤더로 시작.
    반환: [{"id": "EP-01", "num": 1, "title": "...", "body": "...", "fields": {...}}]
    """
    ep_pattern = re.compile(r"^### (EP-(\d+)):\s*(.+)$", re.MULTILINE)
    matches = list(ep_pattern.finditer(text))

    episodes = []
    for i, match in enumerate(matches):
        ep_id = match.group(1)
        ep_num = int(match.group(2))
        ep_title = match.group(3).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()

        fields = {}
        for field_match in re.finditer(
            r"^- \*\*(.+?)\*\*:\s*(.+?)(?=\n- \*\*|\n###|\n---|\n##|\Z)",
            body,
            re.MULTILINE | re.DOTALL,
        ):
            field_name = field_match.group(1).strip()
            field_value = field_match.group(2).strip()
            fields[field_name] = field_value

        episodes.append(
            {
                "id": ep_id,
                "num": ep_num,
                "title": ep_title,
                "body": body,
                "fields": fields,
            }
        )

    return episodes


def check_v1_episode_count(
    episodes: list[dict], expected_total: int
) -> dict:
    """V1: 에피소드 수가 project.yaml의 episodes.total과 일치하는지 검증."""
    actual = len(episodes)
    passed = actual == expected_total
    return {
        "id": "V1",
        "name": "에피소드 수",
        "result": "PASS" if passed else "FAIL",
        "value": actual,
        "criteria": f"project.yaml episodes.total={expected_total}",
        "detail": f"아웃라인 {actual}편"
        + ("" if passed else f" (기대값 {expected_total}편)"),
    }


def check_v2_field_completeness(
    episodes: list[dict], required_fields: list[str]
) -> dict:
    """V2: 모든 EP에 필수 필드(4필드)가 존재하는지 검증."""
    missing = []
    for ep in episodes:
        ep_missing = [f for f in required_fields if f not in ep["fields"]]
        if ep_missing:
            missing.append({"ep": ep["id"], "missing": ep_missing})

    passed = len(missing) == 0
    detail = "모든 EP에 필수 필드 완비"
    if not passed:
        samples = missing[:5]
        detail = "; ".join(
            f"{m['ep']}: {', '.join(m['missing'])} 누락" for m in samples
        )
        if len(missing) > 5:
            detail += f" 외 {len(missing) - 5}건"

    return {
        "id": "V2",
        "name": "필드 완비",
        "result": "PASS" if passed else "FAIL",
        "value": len(missing),
        "criteria": f"모든 EP에 {required_fields} 존재",
        "detail": detail,
    }


def check_v3_foreshadow(episodes: list[dict]) -> dict:
    """V3: 각 EP에 떡밥 필드가 기술되어 있는지 검증."""
    empty = []
    for ep in episodes:
        foreshadow = ep["fields"].get("떡밥", "").strip()
        if not foreshadow:
            empty.append(ep["id"])

    passed = len(empty) == 0
    detail = "모든 EP에 떡밥 기술됨"
    if not passed:
        detail = f"떡밥 누락: {', '.join(empty[:10])}"
        if len(empty) > 10:
            detail += f" 외 {len(empty) - 10}건"

    return {
        "id": "V3",
        "name": "떡밥 존재",
        "result": "PASS" if passed else "FAIL",
        "value": len(empty),
        "criteria": "각 EP에 떡밥 필드 기술",
        "detail": detail,
    }


def check_v4_character_distribution(
    episodes: list[dict], config: dict
) -> dict:
    """V4: 주요 캐릭터가 아웃라인에 최소 1회 이상 등장하는지 검증."""
    character_names = config.get("context", {}).get("character_names", {})
    if not character_names:
        return {
            "id": "V4",
            "name": "캐릭터 분포",
            "result": "PASS",
            "value": 0,
            "criteria": "주요 캐릭터 최소 1회 등장",
            "detail": "character_names 미설정 — 스킵",
        }

    all_text = "\n".join(ep["body"] for ep in episodes)
    not_found = []
    for short_name, full_name in character_names.items():
        if short_name not in all_text and full_name not in all_text:
            not_found.append(short_name)

    passed = len(not_found) == 0
    result = "PASS" if passed else "WARN"
    detail = "모든 주요 캐릭터 등장 확인"
    if not passed:
        detail = f"미등장 캐릭터: {', '.join(not_found)}"

    return {
        "id": "V4",
        "name": "캐릭터 분포",
        "result": result,
        "value": len(not_found),
        "criteria": "주요 캐릭터 최소 1회 등장",
        "detail": detail,
    }


def check_v5_ending_hooks(episodes: list[dict]) -> dict:
    """V5: 모든 EP에 엔딩 훅이 존재하는지 검증."""
    missing = []
    for ep in episodes:
        hook = ep["fields"].get("엔딩 훅", "").strip()
        if not hook:
            missing.append(ep["id"])

    passed = len(missing) == 0
    detail = "모든 EP에 엔딩 훅 존재"
    if not passed:
        detail = f"엔딩 훅 누락: {', '.join(missing[:10])}"
        if len(missing) > 10:
            detail += f" 외 {len(missing) - 10}건"

    return {
        "id": "V5",
        "name": "엔딩 훅",
        "result": "PASS" if passed else "FAIL",
        "value": len(missing),
        "criteria": "모든 EP에 엔딩 훅 존재",
        "detail": detail,
    }


def validate(project_dir_name: str) -> dict:
    """전체 아웃라인 검증 실행."""
    project_dir = PROJECT_ROOT / project_dir_name
    config = load_project_config(project_dir)
    preprod = get_preproduction_config(config)

    expected_total = config.get("episodes", {}).get("total", 0)
    required_fields = preprod["outline"]["ep_fields"]

    outline_file = preprod["outline"]["outline_file"]
    outline_path = project_dir / outline_file
    if not outline_path.exists():
        return {
            "error": f"아웃라인 파일을 찾을 수 없음: {outline_path}",
            "overall": "ERROR",
        }

    text = outline_path.read_text(encoding="utf-8")
    episodes = parse_episodes(text)

    results = [
        check_v1_episode_count(episodes, expected_total),
        check_v2_field_completeness(episodes, required_fields),
        check_v3_foreshadow(episodes),
        check_v4_character_distribution(episodes, config),
        check_v5_ending_hooks(episodes),
    ]

    fail_items = [r["id"] for r in results if r["result"] == "FAIL"]
    warn_items = [r["id"] for r in results if r["result"] == "WARN"]
    overall = "FAIL" if fail_items else "PASS"

    return {
        "project": config.get("name", project_dir_name),
        "outline_file": str(outline_path),
        "episode_count": len(episodes),
        "results": results,
        "overall": overall,
        "fail_items": fail_items,
        "warn_items": warn_items,
        "summary": {r["id"]: r["result"] for r in results},
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            json.dumps(
                {
                    "error": "사용법: python workflow/outline_validate.py <project_dir>\n"
                    "예시: python workflow/outline_validate.py ssulhwa",
                    "overall": "ERROR",
                },
                ensure_ascii=False,
            )
        )
        sys.exit(1)

    result = validate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["overall"] in ("PASS",) else 1)
