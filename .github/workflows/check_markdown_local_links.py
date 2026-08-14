from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path.cwd()
MARKDOWN_SUFFIXES = {".md", ".markdown", ".mdown", ".mkd"}
INLINE_LINK_RE = re.compile(r"(!?\[[^\]]*]\(([^)]+)\))")
REFERENCE_DEF_RE = re.compile(r"^\s{0,3}\[[^\]]+]:\s*(\S+)", re.MULTILINE)
IGNORED_SCHEMES = {"http", "https", "mailto", "tel", "data"}


def iter_markdown_files(root: Path) -> list[Path]:
    return [
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in MARKDOWN_SUFFIXES
    ]


def iter_link_targets(text: str) -> list[str]:
    targets = [match.group(2).strip() for match in INLINE_LINK_RE.finditer(text)]
    targets.extend(match.group(1).strip() for match in REFERENCE_DEF_RE.finditer(text))
    return targets


def normalize_target(raw_target: str) -> str:
    target = raw_target.strip()
    if not target:
        return ""
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    if (target.startswith('"') and target.endswith('"')) or (
        target.startswith("'") and target.endswith("'")
    ):
        target = target[1:-1].strip()
    return target


def is_local_target(target: str) -> bool:
    if not target or target.startswith("#"):
        return False
    parsed = urlparse(target)
    if parsed.scheme.lower() in IGNORED_SCHEMES:
        return False
    return True


def resolve_target(source_file: Path, target: str) -> Path:
    parsed = urlparse(target)
    path_part = unquote(parsed.path)
    if path_part.startswith("/"):
        return ROOT / path_part.lstrip("/")
    return (source_file.parent / path_part).resolve()


def main() -> int:
    errors: list[str] = []

    for md_file in iter_markdown_files(ROOT):
        text = md_file.read_text(encoding="utf-8")
        for raw_target in iter_link_targets(text):
            target = normalize_target(raw_target)
            if not is_local_target(target):
                continue

            resolved = resolve_target(md_file, target)
            if resolved.exists():
                continue

            rel_source = md_file.relative_to(ROOT)
            errors.append(f"{rel_source}: missing target: {target}")

    if errors:
        print("Broken local markdown links:")
        for error in errors:
            print(error)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
