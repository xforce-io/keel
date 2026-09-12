#!/usr/bin/env python3
"""Inspect effective AGENTS.md sources and lightweight repository evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


GLOBAL_CANDIDATES = (
    ".agents/AGENTS.md",
    ".config/agents/AGENTS.md",
    ".codex/AGENTS.md",
    ".pi/agent/AGENTS.md",
    ".grok/AGENTS.md",
    ".grok/Agents.md",
    ".omp/agent/AGENTS.md",
)


def run_git(cwd: Path, *args: str) -> tuple[int, str]:
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode, result.stdout.rstrip()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_record(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": str(path),
        "canonical_path": str(resolved),
        "sha256": digest(resolved),
        "bytes": resolved.stat().st_size,
    }


def sanitize_remote(remote: str) -> tuple[str | None, str | None]:
    """Return a credential-free remote only when its shape is understood."""
    value = remote.strip()
    if not value or any(ord(character) < 32 or ord(character) == 127 for character in value):
        return None, None

    url_match = re.match(r"^([A-Za-z][A-Za-z0-9+.-]*)://", value)
    if url_match:
        scheme = url_match.group(1).lower()
        if scheme not in {"git", "http", "https", "ssh"}:
            return None, None
        try:
            parsed = urlsplit(value)
            host = parsed.hostname
            port = parsed.port
        except ValueError:
            return None, None
        if not host:
            return None, None
        display_host = f"[{host}]" if ":" in host else host
        endpoint = f"{scheme}://{display_host}:{port}" if port is not None else f"{scheme}://{display_host}"
        return endpoint, host

    colon_index = value.find(":")
    at_index = value.find("@")
    if at_index >= 0 and (colon_index < 0 or at_index > colon_index):
        return None, None

    scp_match = re.fullmatch(
        r"(?:[^@\s/:]+@)?(?P<host>[A-Za-z0-9._-]+):(?P<path>[^\s?#]+)",
        value,
    )
    if scp_match:
        host = scp_match.group("host")
        return host, host

    # Local paths, remote helpers, and malformed values are intentionally omitted:
    # returning the raw value could expose credentials embedded in an unknown syntax.
    return None, None


def hosting_record(cwd: Path) -> dict[str, Any]:
    code, origin = run_git(cwd, "remote", "get-url", "origin")
    if code != 0 or not origin:
        return {"kind": "unknown", "host": None, "sanitized_origin": None}

    sanitized_origin, host = sanitize_remote(origin)
    normalized_host = (host or "").lower()
    if normalized_host == "github.com":
        kind = "github"
    elif "gitlab" in normalized_host:
        kind = "gitlab"
    else:
        kind = "unknown"

    return {
        "kind": kind,
        "host": host,
        "sanitized_origin": sanitized_origin,
    }


def find_global_sources() -> tuple[list[dict[str, Any]], list[str], str | None]:
    home = Path.home()
    records = [
        file_record(home / relative)
        for relative in GLOBAL_CANDIDATES
        if (home / relative).is_file()
    ]
    canonical_paths = sorted({record["canonical_path"] for record in records})
    conflicts: list[str] = []
    target: str | None = None

    if len(canonical_paths) == 1:
        target = canonical_paths[0]
    elif len(canonical_paths) > 1:
        conflicts.append(
            "Global AGENTS.md files resolve to multiple canonical sources: "
            + ", ".join(canonical_paths)
        )

    return records, conflicts, target


def find_project_chain(repo_root: Path, cwd: Path) -> list[dict[str, Any]]:
    chain: list[dict[str, Any]] = []
    current = repo_root
    while True:
        candidate = current / "AGENTS.md"
        if candidate.is_file():
            chain.append(file_record(candidate))
        if current == cwd or current not in cwd.parents:
            break
        relative_parts = cwd.relative_to(current).parts
        if not relative_parts:
            break
        current = current / relative_parts[0]
    return chain


def repository_record(cwd: Path) -> dict[str, Any] | None:
    code, root_output = run_git(cwd, "rev-parse", "--show-toplevel")
    if code != 0 or not root_output:
        return None

    root = Path(root_output).resolve()
    _, branch = run_git(cwd, "branch", "--show-current")
    _, status = run_git(cwd, "status", "--short")
    _, diff_stat = run_git(cwd, "diff", "--stat")
    _, staged_diff_stat = run_git(cwd, "diff", "--cached", "--stat")
    _, changed = run_git(cwd, "diff", "--name-status", "HEAD")

    return {
        "root": str(root),
        "branch": branch or None,
        "status_short": status,
        "diff_stat": diff_stat,
        "staged_diff_stat": staged_diff_stat,
        "changed_files": changed,
        "hosting": hosting_record(cwd),
        "project_instruction_chain": find_project_chain(root, cwd),
        "default_project_target": str(root / "AGENTS.md"),
        "glossary_exists": (root / "docs" / "glossary.md").is_file(),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect AGENTS.md sources for the keel-reflect skill."
    )
    parser.add_argument(
        "--cwd",
        default=os.getcwd(),
        help="Working directory to inspect (defaults to the current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cwd = Path(args.cwd).expanduser().resolve()
    if not cwd.is_dir():
        raise SystemExit(f"Not a directory: {cwd}")

    global_sources, conflicts, global_target = find_global_sources()
    repository = repository_record(cwd)
    scope = "project" if repository else "global"

    output = {
        "schema_version": 2,
        "cwd": str(cwd),
        "scope": scope,
        "global_sources": global_sources,
        "canonical_global_target": global_target,
        "configuration_conflicts": conflicts,
        "repository": repository,
    }
    json.dump(output, fp=os.sys.stdout, ensure_ascii=False, indent=2)
    os.sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
