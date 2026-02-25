#!/usr/bin/env python3
"""Stage 1: 에피소드 컨텍스트 조립 헬퍼 (범용).

사용법: python workflow/context_assembly.py <project_dir> <episode>
예시:   python workflow/context_assembly.py ssulhwa EP-05
출력:   JSON 형식의 컨텍스트 패키지
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


def parse_ep_number(ep_arg: str) -> int:
    """EP-XX 형식에서 번호 추출."""
    match = re.match(r"EP-?(\d+)", ep_arg, re.IGNORECASE)
    if not match:
        raise ValueError(f"잘못된 에피소드 형식: {ep_arg} (예: EP-05)")
    return int(match.group(1))


def format_ep_tag(ep_num: int, id_format: str = "EP-{num:02d}") -> str:
    """에피소드 태그 생성."""
    return id_format.format(num=ep_num)


def extract_ep_outline(text: str, ep_num: int, id_format: str = "EP-{num:02d}") -> dict:
    """episode-outline.md에서 해당 EP 아웃라인 + 직전 EP 엔딩 훅 추출."""
    ep_tag = format_ep_tag(ep_num, id_format)
    prev_tag = format_ep_tag(ep_num - 1, id_format) if ep_num > 1 else None

    result = {"outline": "", "prev_ending_hook": "", "ep_title": ""}

    # 현재 EP 아웃라인 추출
    pattern = rf"### {re.escape(ep_tag)}:(.+?)(?=\n### (?:EP-|\S+-)\d+|\n---|\Z)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        result["outline"] = f"### {ep_tag}:{match.group(1).strip()}"
        title_match = re.search(
            rf"### {re.escape(ep_tag)}:\s*(.+?)(?:\s*\[|$)",
            match.group(0).split("\n")[0],
        )
        if title_match:
            result["ep_title"] = title_match.group(1).strip()

    # 직전 EP 엔딩 훅 추출
    if prev_tag:
        prev_pattern = rf"### {re.escape(prev_tag)}:(.+?)(?=\n### (?:EP-|\S+-)\d+|\n---|\Z)"
        prev_match = re.search(prev_pattern, text, re.DOTALL)
        if prev_match:
            hook_match = re.search(
                r"\*\*엔딩 훅\*\*:\s*(.+?)(?:\n\n|\n-|\Z)",
                prev_match.group(1),
                re.DOTALL,
            )
            if hook_match:
                result["prev_ending_hook"] = hook_match.group(1).strip()

    return result


def extract_characters(
    text: str,
    outline: str,
    character_names: dict,
    default_character: str = "",
    max_lines: int = 80,
) -> str:
    """characters.md에서 아웃라인에 언급된 캐릭터 섹션만 추출."""
    mentioned = []
    for name, section_header in character_names.items():
        if name in outline:
            mentioned.append(section_header)

    if not mentioned and default_character:
        mentioned = [default_character]

    extracted = []
    for header in mentioned:
        pattern = rf"## {re.escape(header)}(.+?)(?=\n## |\Z)"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            section = f"## {header}{match.group(1)}"
            lines = section.split("\n")
            if len(lines) > max_lines:
                section = "\n".join(lines[:max_lines]) + "\n[... 이하 생략]"
            extracted.append(section)

    return "\n\n".join(extracted)


def extract_world_sections(
    text: str,
    outline: str,
    world_keywords: dict,
    always_include: list = None,
    max_lines: int = 60,
) -> str:
    """world.md에서 키워드 기반 관련 섹션 추출."""
    needed_sections = set()

    # 항상 포함할 섹션
    if always_include:
        for section_name in always_include:
            for _category, config in world_keywords.items():
                for s in config.get("sections", []):
                    if section_name in s:
                        needed_sections.add(s)
            needed_sections.add(section_name)

    # 키워드 기반 매칭
    for _category, config in world_keywords.items():
        for keyword in config.get("keywords", []):
            if keyword in outline:
                needed_sections.update(config.get("sections", []))
                break

    # 섹션 추출
    extracted = []
    for section_name in needed_sections:
        pattern = rf"### {re.escape(section_name)}(.+?)(?=\n### |\n## |\Z)"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            section = f"### {section_name}{match.group(1)}"
            lines = section.split("\n")
            if len(lines) > max_lines:
                section = "\n".join(lines[:max_lines]) + "\n[... 이하 생략]"
            extracted.append(section)

    return "\n\n".join(extracted)


def get_previous_episode_ending(
    episodes_dir: Path, ep_num: int, id_format: str = "EP-{num:02d}"
) -> str:
    """이전 에피소드 파일의 마지막 500자 추출."""
    if ep_num <= 1:
        return ""

    prev_tag = format_ep_tag(ep_num - 1, id_format)

    if episodes_dir.exists():
        for pat in [f"{prev_tag}_*.md", f"{prev_tag}*.md"]:
            matches = list(episodes_dir.glob(pat))
            if matches:
                text = matches[0].read_text(encoding="utf-8")
                return text[-500:] if len(text) > 500 else text

        # pilot/ 디렉토리도 검색
        pilot_dir = episodes_dir / "pilot"
        if pilot_dir.exists():
            for pat in [f"{prev_tag}_*.md", f"{prev_tag}*.md"]:
                matches = list(pilot_dir.glob(pat))
                if matches:
                    text = matches[0].read_text(encoding="utf-8")
                    return text[-500:] if len(text) > 500 else text

    return ""


def assemble_context(project_dir_name: str, ep_arg: str) -> dict:
    """전체 컨텍스트 조립."""
    project_dir = PROJECT_ROOT / project_dir_name
    config = load_project_config(project_dir)

    ep_num = parse_ep_number(ep_arg)
    id_format = config.get("episodes", {}).get("id_format", "EP-{num:02d}")
    ep_tag = format_ep_tag(ep_num, id_format)

    # 로어 경로 결정
    lore_config = config.get("lore", {})
    episodes_dir = project_dir / "episodes"

    # 로어 파일 읽기
    outline_path = project_dir / lore_config.get("episode_outline", "lore/episode-outline.md")
    characters_path = project_dir / lore_config.get("characters", "lore/characters.md")
    world_path = project_dir / lore_config.get("world", "lore/world.md")
    style_path = project_dir / lore_config.get("style_guide", "lore/style-guide.md")

    outline_text = outline_path.read_text(encoding="utf-8")
    characters_text = characters_path.read_text(encoding="utf-8")
    world_text = world_path.read_text(encoding="utf-8")
    style_text = style_path.read_text(encoding="utf-8")

    # 컨텍스트 설정 로드
    ctx_config = config.get("context", {})
    character_names = ctx_config.get("character_names", {})
    default_character = ctx_config.get("default_character", "")
    max_character_lines = ctx_config.get("max_character_lines", 80)
    max_world_lines = ctx_config.get("max_world_lines", 60)
    world_keywords = ctx_config.get("world_keywords", {})
    always_include = ctx_config.get("always_include_sections", [])

    # 아웃라인 추출
    ep_data = extract_ep_outline(outline_text, ep_num, id_format)
    outline_for_matching = ep_data["outline"]

    context = {
        "project": config.get("name", project_dir_name),
        "language": config.get("language", "ko"),
        "episode": ep_tag,
        "ep_number": ep_num,
        "ep_title": ep_data["ep_title"],
        "outline": ep_data["outline"],
        "prev_ending_hook": ep_data["prev_ending_hook"],
        "characters": extract_characters(
            characters_text,
            outline_for_matching,
            character_names,
            default_character,
            max_character_lines,
        ),
        "world": extract_world_sections(
            world_text,
            outline_for_matching,
            world_keywords,
            always_include,
            max_world_lines,
        ),
        "style_guide": style_text,
        "previous_ending": get_previous_episode_ending(episodes_dir, ep_num, id_format),
        "format": config.get("format", {}),
    }

    # 토큰 추정 (한국어 1자 ≈ 1.5 토큰)
    total_chars = sum(len(str(v)) for k, v in context.items() if not k.startswith("_"))
    context["_meta"] = {
        "total_chars": total_chars,
        "estimated_tokens": int(total_chars * 1.5),
        "sections_included": {
            "outline": bool(context["outline"]),
            "prev_ending_hook": bool(context["prev_ending_hook"]),
            "characters": bool(context["characters"]),
            "world": bool(context["world"]),
            "previous_ending": bool(context["previous_ending"]),
        },
    }

    return context


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            json.dumps(
                {
                    "error": "사용법: python workflow/context_assembly.py <project_dir> <episode>\n"
                    "예시: python workflow/context_assembly.py ssulhwa EP-05"
                },
                ensure_ascii=False,
            )
        )
        sys.exit(1)

    try:
        result = assemble_context(sys.argv[1], sys.argv[2])
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(1)
