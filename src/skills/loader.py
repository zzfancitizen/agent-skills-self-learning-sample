"""
Skill Loader - Parse and load SKILL.md files

SKILL.md format:
---
name: skill_name
description: Brief description
tags: [tag1, tag2]
---

# Skill detailed content...

Supports lazy loading: at init time only the YAML frontmatter (header) is
parsed. The full body content is loaded on demand when first accessed via the
`content` property, following the Cursor/Claude skill pattern.

Each agent may have multiple skills organised under ``agent_dir/skills/<name>/``.
Use ``SkillLoader.load_agent_skills()`` to discover all of them at once.
"""

import logging
import re
from pathlib import Path
from typing import Optional, TYPE_CHECKING

import yaml
from langchain_core.tools import BaseTool, tool

if TYPE_CHECKING:
    from .registry import SkillRegistry

logger = logging.getLogger(__name__)


class Skill:
    """Represents a loaded Skill with lazy content loading support.

    When loaded lazily (the default), only header metadata (name, description,
    tags) is available immediately. The full body content is read from disk and
    cached on the first access of the ``content`` property.
    """

    def __init__(
        self,
        name: str,
        description: str,
        path: Path,
        tags: list[str] | None = None,
        scripts_dir: Optional[Path] = None,
        resources_dir: Optional[Path] = None,
        content: Optional[str] = None,
    ):
        self.name = name
        self.description = description
        self.path = path
        self.tags = tags if tags is not None else []
        self.scripts_dir = scripts_dir
        self.resources_dir = resources_dir
        # Lazy loading internals
        self._content: Optional[str] = content
        self._content_loaded: bool = content is not None

    # -- lazy content property ------------------------------------------------

    @property
    def content(self) -> str:
        """Return skill body content, loading it lazily from disk if needed."""
        if not self._content_loaded:
            self._load_content()
        return self._content or ""

    def _load_content(self) -> None:
        """Read the SKILL.md file and extract the body (everything after the
        frontmatter).  Called automatically on the first access of ``content``.
        """
        skill_file = self.path / "SKILL.md"
        if skill_file.exists():
            raw = skill_file.read_text(encoding="utf-8")
            _, body = SkillLoader._parse_frontmatter(raw)
            self._content = body.strip()
            logger.debug(
                "Lazy-loaded content for skill '%s' from %s (%d chars)",
                self.name, skill_file, len(self._content),
            )
        else:
            self._content = ""
            logger.warning("Skill file not found for lazy loading: %s", skill_file)
        self._content_loaded = True

    # -- prompt helpers -------------------------------------------------------

    def get_prompt_section(self) -> str:
        """Generate content for injection into system prompt.

        Accessing ``self.content`` here triggers a lazy load if the body has
        not been read yet.
        """
        return f"""## Skill: {self.name}
{self.description}

{self.content}
"""

    def __repr__(self) -> str:
        status = "loaded" if self._content_loaded else "lazy"
        return f"Skill(name={self.name!r}, tags={self.tags}, content_status={status})"


class SkillLoader:
    """Load a single Skill or an entire Skill directory"""

    FRONTMATTER_PATTERN = re.compile(
        r'^---\s*\n(.*?)\n---\s*\n(.*)$',
        re.DOTALL
    )

    @classmethod
    def load_skill(cls, skill_dir: Path, lazy: bool = True) -> Optional[Skill]:
        """
        Load a skill from a skill directory.

        Args:
            skill_dir: Skill directory path, must contain SKILL.md
            lazy: If True (default), only load header metadata at init time.
                  The body content is loaded on demand when first accessed
                  via the ``content`` property.

        Returns:
            Skill object, or None if loading fails
        """
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            return None

        # --- metadata / content extraction -----------------------------------
        body_content: Optional[str] = None  # None → lazy (not yet loaded)

        if lazy:
            # Only read the YAML frontmatter header; skip the body entirely
            metadata = cls._read_frontmatter(skill_file)
        else:
            # Eager: read everything in one pass
            raw = skill_file.read_text(encoding="utf-8")
            metadata, body = cls._parse_frontmatter(raw)
            body_content = body.strip()

        # --- build Skill object ----------------------------------------------
        name = metadata.get("name", skill_dir.name)
        description = metadata.get("description", "")
        tags = metadata.get("tags", [])

        scripts_dir = skill_dir / "scripts"
        resources_dir = skill_dir / "resources"

        return Skill(
            name=name,
            description=description,
            path=skill_dir,
            tags=tags if isinstance(tags, list) else [tags],
            scripts_dir=scripts_dir if scripts_dir.exists() else None,
            resources_dir=resources_dir if resources_dir.exists() else None,
            content=body_content,
        )

    @classmethod
    def load_skills_from_directory(
        cls, skills_root: Path, lazy: bool = True
    ) -> list[Skill]:
        """
        Load all skills from a directory.

        Args:
            skills_root: Skills root directory
            lazy: If True (default), only load header metadata for each skill

        Returns:
            List of Skill objects
        """
        skills: list[Skill] = []
        skills_root = Path(skills_root)

        if not skills_root.exists():
            return skills

        for item in skills_root.iterdir():
            if item.is_dir():
                skill = cls.load_skill(item, lazy=lazy)
                if skill:
                    skills.append(skill)

        return skills

    @classmethod
    def load_agent_skills(cls, agent_dir: Path, lazy: bool = True) -> list[Skill]:
        """
        Discover and load all skills from an agent's ``skills/`` directory.

        Each sub-directory of ``agent_dir/skills/`` that contains a SKILL.md
        file is treated as a separate skill.

        Args:
            agent_dir: The agent's root directory (e.g. ``src/agents/router``)
            lazy: If True (default), only load header metadata for each skill

        Returns:
            List of Skill objects
        """
        skills_dir = agent_dir / "skills"
        return cls.load_skills_from_directory(skills_dir, lazy=lazy)

    # -- frontmatter parsing --------------------------------------------------

    @classmethod
    def _read_frontmatter(cls, skill_file: Path) -> dict:
        """
        Read **only** the YAML frontmatter from a SKILL.md file.

        Reads line-by-line and stops as soon as the closing ``---`` marker is
        found, so the (potentially large) body content is never loaded into
        memory.

        Returns:
            Parsed frontmatter as a dictionary
        """
        lines: list[str] = []
        in_frontmatter = False

        with open(skill_file, "r", encoding="utf-8") as fh:
            for line in fh:
                stripped = line.strip()
                if stripped == "---":
                    if not in_frontmatter:
                        in_frontmatter = True
                        continue
                    else:
                        # Closing marker → stop reading
                        break
                if in_frontmatter:
                    lines.append(line)

        if lines:
            try:
                return yaml.safe_load("".join(lines)) or {}
            except yaml.YAMLError:
                pass

        return {}

    @classmethod
    def _parse_frontmatter(cls, content: str) -> tuple[dict, str]:
        """
        Parse YAML frontmatter **and** body content from a full file string.

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


# ---------------------------------------------------------------------------
# load_skill tool factory
# ---------------------------------------------------------------------------


def create_load_skill_tool(
    registry: "SkillRegistry",
    skill_names: list[str],
) -> BaseTool:
    """Create a ``load_skill`` LangChain tool scoped to *skill_names*.

    The returned tool allows the LLM to lazily load the full body content of a
    skill on demand.  At init time only the skill summaries (name + description)
    appear in the system prompt; the LLM calls this tool when it decides it
    needs the detailed instructions for a specific skill.

    Args:
        registry: The shared :class:`SkillRegistry`
        skill_names: Skill names this agent is allowed to load

    Returns:
        A LangChain ``BaseTool`` instance
    """

    @tool
    def load_skill(skill_name: str) -> str:
        """Load the full instructions for a skill.

        Call this tool **before** performing a task that matches one of the
        available skills listed in the system prompt.  It returns the complete
        skill content so you can follow its guidance.
        """
        if skill_name not in skill_names:
            return (
                f"Skill '{skill_name}' is not available for this agent. "
                f"Available skills: {skill_names}"
            )
        skill_obj = registry.get(skill_name)
        if skill_obj is None:
            return f"Skill '{skill_name}' not found in registry."
        # Accessing .content triggers lazy loading from disk
        return skill_obj.content

    return load_skill  # type: ignore[return-value]
