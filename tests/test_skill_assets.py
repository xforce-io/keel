"""Validate loadable assets and references, not the meaning of natural-language rules."""
from __future__ import annotations

import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class SkillAssetTests(unittest.TestCase):
    def test_skill_entry_metadata_matches_directory(self) -> None:
        entries = sorted((ROOT / "skills").glob("*/SKILL.md"))
        self.assertTrue(entries, "No skill entries found")
        for path in entries:
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8")
                self.assertTrue(text.startswith("---\n"), "Missing frontmatter")
                parts = text.split("---", 2)
                self.assertEqual(len(parts), 3, "Unclosed frontmatter")
                metadata = parts[1]
                name = re.search(r"^name:\s*(\S+)\s*$", metadata, re.M)
                self.assertIsNotNone(name, "Missing skill name")
                self.assertEqual(name.group(1), path.parent.name)
                description = re.search(
                    r"^description:\s*(.*(?:\n[ \t]+[^\n]+)*)", metadata, re.M
                )
                self.assertIsNotNone(description, "Missing description")
                self.assertTrue(description.group(1).strip().strip(">|+- "), "Empty description")
                self.assertTrue(parts[2].strip(), "Empty skill body")

    def test_local_markdown_links_resolve(self) -> None:
        paths = (
            [ROOT / "README.md"]
            + list((ROOT / "skills").rglob("*.md"))
            + list((ROOT / "evals").rglob("*.md"))
            + list((ROOT / ".agents/skills/verify-keel").rglob("*.md"))
        )
        for path in sorted(paths):
            text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.S)
            for link in re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", text):
                target = urlsplit(link)
                if target.scheme or target.netloc or not target.path:
                    continue
                with self.subTest(path=path.relative_to(ROOT), link=link):
                    resolved = (path.parent / unquote(target.path)).resolve()
                    self.assertTrue(resolved.is_relative_to(ROOT), "Link leaves checkout")
                    self.assertTrue(resolved.is_file(), "Missing local link target")

    def test_router_stage_table_links_existing_entries(self) -> None:
        text = (ROOT / "skills/keel/SKILL.md").read_text(encoding="utf-8")
        stages = re.findall(r"^\| \d+ \| `(keel(?:-[a-z]+)?)` \|", text, re.M)
        self.assertEqual(stages, [
            "keel-issue", "keel-how", "keel-design", "keel-dev",
            "keel-verify", "keel-review", "keel-release",
        ])
        for stage in stages:
            self.assertTrue((ROOT / "skills" / stage / "SKILL.md").is_file(), stage)

    def test_glossary_uses_three_column_table(self) -> None:
        text = (ROOT / "docs/glossary.md").read_text(encoding="utf-8")
        rows = [line for line in text.splitlines() if line.startswith("|")]
        self.assertGreaterEqual(len(rows), 3)
        terms = []
        for row in rows[2:]:
            columns = [cell.strip() for cell in row.strip("|").split("|")]
            self.assertEqual(len(columns), 3, row)
            self.assertTrue(all(columns), row)
            terms.append(columns[0])
        self.assertEqual(len(terms), len(set(terms)), "Duplicate glossary term")


if __name__ == "__main__":
    unittest.main()
