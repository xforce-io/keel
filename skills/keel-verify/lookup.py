#!/usr/bin/env python3
"""Locate a project-local verify-* handbook under the app repo's .grok/skills.

Never searches .cursor or any other agent-home tree. The driving handbook and
feature map live in the current application repository, not in the keel plugin.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

SKILL_MD = "SKILL.md"
FEATURES = "features"
FEATURES_README = "README.md"
GROK_SKILLS = (".grok", "skills")
VERIFY_PREFIX = "verify-"


@dataclass(frozen=True)
class VerifyHandbook:
    name: str
    skill_file: Path
    features_dir: Path
    feature_files: tuple[Path, ...]


def _feature_files(features_dir: Path) -> tuple[Path, ...]:
    files = [
        path
        for path in sorted(features_dir.iterdir())
        if path.is_file() and path.suffix.lower() in {".md", ".markdown"} and path.name.lower() != "readme.md"
    ]
    return tuple(files)


def incomplete_handbooks(app_root: Path) -> dict[str, list[str]]:
    """Map verify-* dirs that are missing required parts to the missing file names."""
    skills = app_root.expanduser().resolve().joinpath(*GROK_SKILLS)
    if not skills.is_dir():
        return {}
    problems: dict[str, list[str]] = {}
    for child in sorted(skills.iterdir()):
        if not child.is_dir() or not child.name.startswith(VERIFY_PREFIX):
            continue
        missing = [
            str(relative)
            for relative in (Path(SKILL_MD), Path(FEATURES), Path(FEATURES) / FEATURES_README)
            if not (child / relative).exists()
        ]
        if missing:
            problems[child.name] = missing
    return problems


def find_verify_handbooks(app_root: Path) -> tuple[VerifyHandbook, ...]:
    """Return handbooks at <app_root>/.grok/skills/verify-*/ with SKILL.md, features/ and features/README.md."""
    root = app_root.expanduser().resolve()
    skills = root.joinpath(*GROK_SKILLS)
    if not skills.is_dir():
        return ()
    found: list[VerifyHandbook] = []
    for child in sorted(skills.iterdir()):
        if not child.is_dir() or not child.name.startswith(VERIFY_PREFIX):
            continue
        skill_file = child / SKILL_MD
        features_dir = child / FEATURES
        if not skill_file.is_file() or not (features_dir / FEATURES_README).is_file():
            continue
        found.append(
            VerifyHandbook(
                name=child.name,
                skill_file=skill_file,
                features_dir=features_dir,
                feature_files=_feature_files(features_dir),
            )
        )
    return tuple(found)


def find_verify_handbook(app_root: Path) -> VerifyHandbook | None:
    found = find_verify_handbooks(app_root)
    if len(found) == 1:
        return found[0]
    return None


def _handbook_json(item: VerifyHandbook) -> dict[str, object]:
    return {
        "name": item.name,
        "skill_file": str(item.skill_file),
        "features_dir": str(item.features_dir),
        "feature_files": [path.name for path in item.feature_files],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="keel-verify-lookup",
        description="在应用仓库 .grok/skills/verify-* 下查找驾驶手册与功能地图；不读 .cursor。",
    )
    parser.add_argument("app_root", help="应用仓库根目录")
    args = parser.parse_args(argv)
    root = Path(args.app_root)
    if not root.is_dir():
        print(json.dumps({"status": "missing", "reason": "app_root 不是目录"}, ensure_ascii=False))
        return 1
    found = find_verify_handbooks(root)
    if not found:
        payload: dict[str, object] = {"status": "missing"}
        incomplete = incomplete_handbooks(root)
        if incomplete:
            payload["incomplete"] = incomplete
        print(json.dumps(payload, ensure_ascii=False))
        return 1
    print(
        json.dumps(
            {"status": "found", "handbooks": [_handbook_json(item) for item in found]},
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
