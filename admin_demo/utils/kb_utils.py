from pathlib import Path
import datetime
import re


def list_domains(kb_root: Path) -> list[str]:
    return [
        d.name for d in sorted(kb_root.iterdir())
        if d.is_dir() and not d.name.startswith(".")
    ]


def list_files(domain_path: Path) -> list[Path]:
    if not domain_path.exists():
        return []
    return sorted(domain_path.glob("*.md"))


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def save_file(path: Path, content: str) -> None:
    content = _bump_last_updated(content)
    path.write_text(content, encoding="utf-8")


def create_file(domain_path: Path, name: str, domain: str) -> Path:
    domain_path.mkdir(parents=True, exist_ok=True)
    path = domain_path / f"{name}.md"
    today = datetime.date.today().isoformat()
    template = f"""---
title: {name}
domain: {domain}
tags: []
source:
last_updated: {today}
importance: medium
---

{name}에 대한 설명을 작성하세요.

## 관련 항목
"""
    path.write_text(template, encoding="utf-8")
    return path


def delete_file(path: Path, kb_root: Path) -> None:
    log_path = kb_root / "wiki_admin" / "log.md"
    today = datetime.date.today().isoformat()
    entry = f"\n## {today} — 삭제: {path.name}\n삭제 사유: (수동 입력 필요)\n"
    if log_path.exists():
        with log_path.open("a", encoding="utf-8") as f:
            f.write(entry)
    path.unlink()


def update_index(kb_root: Path, domain: str, file_stem: str) -> None:
    index_path = kb_root / "index.md"
    if not index_path.exists():
        return
    content = index_path.read_text(encoding="utf-8")
    entry = f"| [[{domain}/{file_stem}]] | (설명 추가 필요) | medium |"
    if file_stem not in content:
        # 해당 도메인 섹션 끝에 추가
        section_marker = f"## {domain}/"
        if section_marker in content:
            idx = content.rfind("\n", 0, content.find(section_marker) + 500)
            content = content[:idx] + f"\n{entry}" + content[idx:]
        else:
            content += f"\n{entry}\n"
        index_path.write_text(content, encoding="utf-8")


def _bump_last_updated(content: str) -> str:
    today = datetime.date.today().isoformat()
    return re.sub(r"(last_updated:\s*)[\d-]+", rf"\g<1>{today}", content)
