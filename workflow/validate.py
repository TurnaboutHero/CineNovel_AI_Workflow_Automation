#!/usr/bin/env python3
"""Stage 6: 에피소드 최종 검증 스크립트 (범용).

사용법: python workflow/validate.py <project_dir> <episode_file>
예시:   python workflow/validate.py ssulhwa ssulhwa/episodes/.staging/EP-05_draft_v1.md
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


def get_format_config(config: dict) -> dict:
    """format 설정을 기본값과 병합하여 반환."""
    defaults = {
        "char_count": [9000, 11000],
        "scenes": [3, 5],
        "img_markers": [3, 5],
        "scene_separators": [3, 6],
        "header_pattern": r"^# EP-\d+:",
        "next_preview_keyword": "다음 화 예고",
        "img_types": ["landscape", "character", "action", "emotion", "item"],
    }
    fmt = dict(defaults)
    fmt.update(config.get("format", {}))
    return fmt


def get_validation_config(config: dict) -> dict:
    """validation 설정을 기본값과 병합하여 반환."""
    defaults = {
        "max_consecutive_past_endings": 4,
        "min_sentence_length": 10,
    }
    val = dict(defaults)
    val.update(config.get("validation", {}))
    return val


def extract_body(text: str, next_preview_keyword: str = "다음 화 예고") -> str:
    """본문만 추출 (헤더/IMG/구분자/예고 제외)."""
    lines = text.split("\n")
    body_lines = []
    in_body = False

    for line in lines:
        stripped = line.strip()
        # 헤더 건너뛰기
        if stripped.startswith("# ") and not in_body:
            in_body = True
            continue
        # 한줄요약 건너뛰기 (> 로 시작)
        if stripped.startswith(">") and not in_body:
            continue
        if not in_body:
            # 첫 --- 이후부터 본문
            if stripped == "---":
                in_body = True
            continue
        # 다음 화 예고 이후 제외
        preview_patterns = [
            f"**{next_preview_keyword}**",
            f"**{next_preview_keyword.replace(' ', '')}**",
        ]
        if any(stripped.startswith(p) for p in preview_patterns):
            break
        # [IMG] 마커 제외
        if re.match(r"^\[IMG:[^\]]+\]$", stripped):
            continue
        # 구분자 제외
        if stripped == "---":
            continue
        body_lines.append(line)

    return "\n".join(body_lines)


def check_f1_char_count(text: str, fmt: dict, next_preview_keyword: str) -> dict:
    """F1: 글자 수 검증."""
    body = extract_body(text, next_preview_keyword)
    char_count = len(body.replace("\n", "").replace(" ", ""))
    min_chars, max_chars = fmt["char_count"]
    passed = min_chars <= char_count <= max_chars
    return {
        "id": "F1",
        "name": "글자 수",
        "result": "PASS" if passed else "FAIL",
        "value": char_count,
        "criteria": f"{min_chars:,}~{max_chars:,}자",
        "detail": f"본문 {char_count}자"
        + ("" if passed else f" ({'부족' if char_count < min_chars else '초과'})"),
    }


def check_f2_img_markers(text: str, fmt: dict) -> dict:
    """F2: [IMG] 마커 수 검증."""
    markers = re.findall(r"\[IMG:[^\]]+\]", text)
    count = len(markers)
    min_img, max_img = fmt["img_markers"]
    passed = min_img <= count <= max_img
    return {
        "id": "F2",
        "name": "[IMG] 마커",
        "result": "PASS" if passed else "FAIL",
        "value": count,
        "criteria": f"{min_img}~{max_img}개",
        "detail": f"[IMG] 마커 {count}개"
        + ("" if passed else f" ({'부족' if count < min_img else '초과'})"),
    }


def check_f3_scene_separators(text: str, fmt: dict) -> dict:
    """F3: 씬 구분자 수 검증."""
    lines = text.split("\n")
    count = sum(1 for line in lines if line.strip() == "---")
    min_sep, max_sep = fmt["scene_separators"]
    passed = min_sep <= count <= max_sep
    return {
        "id": "F3",
        "name": "씬 구분자",
        "result": "PASS" if passed else "FAIL",
        "value": count,
        "criteria": f"{min_sep}~{max_sep}개",
        "detail": f"--- 구분자 {count}개"
        + ("" if passed else f" ({'부족' if count < min_sep else '초과'})"),
    }


def check_f4_markdown_structure(text: str, fmt: dict) -> dict:
    """F4: 마크다운 구조 검증."""
    header_pattern = fmt["header_pattern"]
    matches = re.findall(header_pattern, text, re.MULTILINE)
    count = len(matches)
    passed = count == 1
    return {
        "id": "F4",
        "name": "마크다운 구조",
        "result": "PASS" if passed else "FAIL",
        "value": count,
        "criteria": f"헤더 패턴 1개 ({header_pattern})",
        "detail": f"헤더 {count}개 발견" + ("" if passed else " (정확히 1개 필요)"),
    }


def check_f5_next_preview(text: str, fmt: dict) -> dict:
    """F5: 다음 화 예고 존재 검증."""
    keyword = fmt["next_preview_keyword"]
    keyword_nospace = keyword.replace(" ", "")
    pattern = rf"\*\*{re.escape(keyword)}\*\*|\*\*{re.escape(keyword_nospace)}\*\*"
    has_preview = bool(re.search(pattern, text))
    return {
        "id": "F5",
        "name": "다음 화 예고",
        "result": "PASS" if has_preview else "FAIL",
        "value": 1 if has_preview else 0,
        "criteria": f"**{keyword}** 1개",
        "detail": "다음 화 예고 " + ("존재" if has_preview else "없음"),
    }


def _has_ssang_siot_batchim(char: str) -> bool:
    """한글 글자의 받침이 ㅆ(쌍시옷)인지 확인."""
    code = ord(char) - 0xAC00
    if code < 0 or code > 11171:
        return False
    return code % 28 == 20  # ㅆ 종성 인덱스


def _classify_ending(sentence: str) -> str:
    """문장 종결어미를 분류.

    Returns:
        'PAST': 과거 서술형 (~았다/었다/였다/했다/갔다/왔다 등 ㅆ받침+다)
        'OTHER_DA': 기타 ~다 종결 (현재형 ~ㄴ다, 피동 ~된다 등 - 변주로 인정)
        'NON_DA': ~다로 끝나지 않음 (명사형, 연결형, 대사 등)
    """
    clean = sentence.rstrip(".!? \t")
    if len(clean) >= 2 and clean[-1] == "다":
        prev = clean[-2]
        if _has_ssang_siot_batchim(prev):
            # 있다(상태/존재), 겠다(추측/미래)는 과거형이 아님
            if prev in ("있", "겠"):
                return "OTHER_DA"
            return "PAST"
        return "OTHER_DA"
    return "NON_DA"


def check_f6_sentence_endings(
    text: str, fmt: dict, val_config: dict, next_preview_keyword: str
) -> dict:
    """F6: 과거형 문미 연속 체크.

    과거 서술형(~았다/었다/였다/했다 등 ㅆ받침+다)이 N개 이상 연속되면 FAIL.
    현재형(~ㄴ다/한다), 피동형(~된다/진다) 등은 다른 패턴으로 분류하여
    과거형 연속을 끊는 것으로 처리한다.
    대사(따옴표), 짧은 파편(min_sentence_length 미만)은 제외한다.
    """
    body = extract_body(text, next_preview_keyword)
    max_consecutive = val_config["max_consecutive_past_endings"]
    min_sentence_len = val_config["min_sentence_length"]

    raw_lines = body.split("\n")
    sentences = []
    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        parts = re.split(r"(?<=[.!?])\s+", line)
        sentences.extend(p.strip() for p in parts if p.strip())

    categories = []
    sentence_texts = []
    for s in sentences:
        if len(s) < min_sentence_len:
            continue
        stripped = s.strip()
        # 대사 건너뛰기
        if stripped[0] in ('"', "\u201c", "\u300c"):
            continue
        if stripped.startswith("'") and stripped.endswith("'"):
            continue

        sentence_texts.append(stripped)
        categories.append(_classify_ending(stripped))

    # 연속 과거형(PAST) N개 이상 탐지
    violation_groups = []
    start = -1
    consecutive = 0
    for i, cat in enumerate(categories):
        if cat == "PAST":
            if consecutive == 0:
                start = i
            consecutive += 1
        else:
            if consecutive >= max_consecutive:
                violation_groups.append(
                    {
                        "start": start,
                        "length": consecutive,
                        "samples": [
                            sentence_texts[j][-30:]
                            for j in range(start, start + min(consecutive, 3))
                        ],
                    }
                )
            consecutive = 0
            start = -1
    if consecutive >= max_consecutive:
        violation_groups.append(
            {
                "start": start,
                "length": consecutive,
                "samples": [
                    sentence_texts[j][-30:]
                    for j in range(start, start + min(consecutive, 3))
                ],
            }
        )

    count = len(violation_groups)
    passed = count == 0
    detail_parts = [f"과거형 문미 연속 위반 {count}개소"]
    if not passed:
        for g in violation_groups[:3]:
            detail_parts.append(
                f"  [{g['length']}연속] ...{' / ...'.join(g['samples'])}"
            )

    return {
        "id": "F6",
        "name": "문미 연속",
        "result": "PASS" if passed else "FAIL",
        "value": count,
        "criteria": f"과거형(~았/었/였/했다) {max_consecutive}연속 0개소",
        "detail": "\n".join(detail_parts),
    }


def validate(project_dir_name: str, filepath: str) -> dict:
    """전체 검증 실행."""
    project_dir = PROJECT_ROOT / project_dir_name
    config = load_project_config(project_dir)
    fmt = get_format_config(config)
    val_config = get_validation_config(config)
    next_preview_keyword = fmt["next_preview_keyword"]

    path = Path(filepath)
    if not path.exists():
        return {"error": f"파일을 찾을 수 없음: {filepath}", "overall": "ERROR"}

    text = path.read_text(encoding="utf-8")

    results = [
        check_f1_char_count(text, fmt, next_preview_keyword),
        check_f2_img_markers(text, fmt),
        check_f3_scene_separators(text, fmt),
        check_f4_markdown_structure(text, fmt),
        check_f5_next_preview(text, fmt),
        check_f6_sentence_endings(text, fmt, val_config, next_preview_keyword),
    ]

    fail_items = [r["id"] for r in results if r["result"] == "FAIL"]
    overall = "FAIL" if fail_items else "PASS"

    return {
        "project": config.get("name", project_dir_name),
        "file": str(path),
        "results": results,
        "overall": overall,
        "fail_items": fail_items,
        "summary": {r["id"]: r["result"] for r in results},
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            json.dumps(
                {
                    "error": "사용법: python workflow/validate.py <project_dir> <episode_file>\n"
                    "예시: python workflow/validate.py ssulhwa ssulhwa/episodes/EP-01.md",
                    "overall": "ERROR",
                },
                ensure_ascii=False,
            )
        )
        sys.exit(1)

    result = validate(sys.argv[1], sys.argv[2])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["overall"] == "PASS" else 1)
