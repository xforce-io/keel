#!/usr/bin/env python3
"""Locate a project-local verify-* handbook under the app repo's .agents/skills.

The handbook root is host-neutral: `.agents/skills/verify-*` is shared by every
agent host that reads the application repository. Never searches .cursor or any
other agent-home tree. The retired `.grok/skills/verify-*` location is only
detected so the caller can be told to migrate it; it is never treated as a
handbook. The driving handbook and feature map live in the current application
repository, not in the keel plugin.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

SKILL_MD = "SKILL.md"
FEATURES = "features"
FEATURES_README = "README.md"
HANDBOOK_ROOT = (".agents", "skills")
LEGACY_ROOT = (".grok", "skills")
VERIFY_PREFIX = "verify-"
LEGACY_MOVE_HINT = (
    "'.grok/skills/verify-*' is no longer a handbook location; move each directory to '.agents/skills/' "
    "(e.g. mkdir -p .agents/skills && git mv .grok/skills/verify-<app> .agents/skills/verify-<app>)."
)
LEGACY_REMOVE_HINT = (
    "'.grok/skills/verify-*' is retired and a '.agents/skills/' handbook already exists; "
    "delete the old directory (e.g. git rm -r .grok/skills/verify-<app>)."
)


@dataclass(frozen=True)
class VerifyHandbook:
    name: str
    skillFile: Path
    featuresDir: Path
    featureFiles: tuple[Path, ...]


def _featureFiles(featuresDir: Path) -> tuple[Path, ...]:
    files = [
        path
        for path in sorted(featuresDir.iterdir())
        if path.is_file() and path.suffix.lower() in {".md", ".markdown"} and path.name.lower() != "readme.md"
    ]
    return tuple(files)


def _verifyDirs(appRoot: Path, root: tuple[str, ...]) -> list[Path]:
    skills = appRoot.expanduser().resolve().joinpath(*root)
    if not skills.is_dir():
        return []
    return [child for child in sorted(skills.iterdir()) if child.is_dir() and child.name.startswith(VERIFY_PREFIX)]


def incompleteHandbooks(appRoot: Path) -> dict[str, list[str]]:
    """Map verify-* dirs under .agents/skills that lack required parts to the missing file names."""
    problems: dict[str, list[str]] = {}
    for child in _verifyDirs(appRoot, HANDBOOK_ROOT):
        missing = [
            str(relative)
            for relative, check in (
                (Path(SKILL_MD), Path.is_file),
                (Path(FEATURES), Path.is_dir),
                (Path(FEATURES) / FEATURES_README, Path.is_file),
            )
            if not check(child / relative)
        ]
        if missing:
            problems[child.name] = missing
    return problems


def legacyHandbooks(appRoot: Path) -> list[str]:
    """Names of verify-* dirs still sitting at the retired .grok/skills location."""
    return [child.name for child in _verifyDirs(appRoot, LEGACY_ROOT)]


def findVerifyHandbooks(appRoot: Path) -> tuple[VerifyHandbook, ...]:
    """Return handbooks at <appRoot>/.agents/skills/verify-*/ with SKILL.md, features/ and features/README.md."""
    found: list[VerifyHandbook] = []
    for child in _verifyDirs(appRoot, HANDBOOK_ROOT):
        skillFile = child / SKILL_MD
        featuresDir = child / FEATURES
        if not skillFile.is_file() or not (featuresDir / FEATURES_README).is_file():
            continue
        found.append(
            VerifyHandbook(
                name=child.name,
                skillFile=skillFile,
                featuresDir=featuresDir,
                featureFiles=_featureFiles(featuresDir),
            )
        )
    return tuple(found)


def findVerifyHandbook(appRoot: Path) -> VerifyHandbook | None:
    found = findVerifyHandbooks(appRoot)
    if len(found) == 1:
        return found[0]
    return None


def _handbookJson(item: VerifyHandbook) -> dict[str, object]:
    return {
        "name": item.name,
        "skill_file": str(item.skillFile),
        "features_dir": str(item.featuresDir),
        "feature_files": [path.name for path in item.featureFiles],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="keel-verify-lookup",
        description="在应用仓库 .agents/skills/verify-* 下查找驾驶手册与功能地图；不读 .cursor，不认旧的 .grok/skills。",
    )
    parser.add_argument("app_root", help="应用仓库根目录")
    args = parser.parse_args(argv)
    root = Path(args.app_root)
    if not root.is_dir():
        print(json.dumps({"status": "missing", "reason": "app_root 不是目录"}, ensure_ascii=False))
        return 1
    legacy = legacyHandbooks(root)
    found = findVerifyHandbooks(root)
    if not found:
        payload: dict[str, object] = {"status": "missing"}
        incomplete = incompleteHandbooks(root)
        if incomplete:
            payload["incomplete"] = incomplete
        if legacy:
            payload["legacy"] = legacy
            payload["hint"] = LEGACY_MOVE_HINT
        print(json.dumps(payload, ensure_ascii=False))
        return 1
    result: dict[str, object] = {"status": "found", "handbooks": [_handbookJson(item) for item in found]}
    if legacy:
        result["legacy"] = legacy
        result["hint"] = LEGACY_REMOVE_HINT
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
