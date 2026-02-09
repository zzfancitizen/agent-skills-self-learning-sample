"""
Skill Loader - Parse and load SKILL.md files

SKILL.md format:
---
name: skill_name
description: Brief description
tags: [tag1, tag2]
---

# Skill detailed content...
"""

import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

import yaml


@dataclass
class Skill:
    """Represents a loaded Skill"""
    name: str
    description: str
    content: str
    path: Path
    tags: list[str] = field(default_factory=list)
    scripts_dir: Optional[Path] = None
    resources_dir: Optional[Path] = None

    def get_prompt_section(self) -> str:
        """Generate content for injection into system prompt"""
        return f"""## Skill: {self.name}
{self.description}

{self.content}
"""


class SkillLoader:
    """Load a single Skill or an entire Skill directory"""

    FRONTMATTER_PATTERN = re.compile(
        r'^---\s*\n(.*?)\n---\s*\n(.*)$',
        re.DOTALL
    )

    @classmethod
    def load_skill(cls, skill_dir: Path) -> Optional[Skill]:
        """
        Load a skill from a skill directory

        Args:
            skill_dir: Skill directory path, must contain SKILL.md

        Returns:
            Skill object, or None if loading fails
        """
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            return None

        raw_content = skill_file.read_text(encoding="utf-8")
        metadata, content = cls._parse_frontmatter(raw_content)

        # Get skill name from metadata or directory name
        name = metadata.get("name", skill_dir.name)
        description = metadata.get("description", "")
        tags = metadata.get("tags", [])

        # Check for optional subdirectories
        scripts_dir = skill_dir / "scripts"
        resources_dir = skill_dir / "resources"

        return Skill(
            name=name,
            description=description,
            content=content.strip(),
            path=skill_dir,
            tags=tags if isinstance(tags, list) else [tags],
            scripts_dir=scripts_dir if scripts_dir.exists() else None,
            resources_dir=resources_dir if resources_dir.exists() else None,
        )

    @classmethod
    def load_skills_from_directory(cls, skills_root: Path) -> list[Skill]:
        """
        Load all skills from a directory

        Args:
            skills_root: Skills root directory

        Returns:
            List of Skill objects
        """
        skills = []
        skills_root = Path(skills_root)

        if not skills_root.exists():
            return skills

        for item in skills_root.iterdir():
            if item.is_dir():
                skill = cls.load_skill(item)
                if skill:
                    skills.append(skill)

        return skills

    @classmethod
    def _parse_frontmatter(cls, content: str) -> tuple[dict, str]:
        """
        Parse YAML frontmatter

        Returns:
            (metadata_dict, remaining_content)
        """
        match = cls.FRONTMATTER_PATTERN.match(content)
        if match:
            try:
                metadata = yaml.safe_load(match.group(1)) or {}
                body = match.group(2)
                return metadata, body
            except yaml.YAMLError:
                pass

        # No frontmatter or parsing failed
        return {}, content
