"""
Skill Registry - Manage and query loaded Skills
"""

from pathlib import Path
from typing import Optional

from .loader import Skill, SkillLoader


class SkillRegistry:
    """
    Skill Registry

    Provides skill registration, querying, and prompt generation
    """

    def __init__(self, skills_dir: Optional[str | Path] = None, lazy: bool = True):
        """
        Initialize Registry

        Args:
            skills_dir: Optional skills directory path; if provided, skills are auto-loaded
            lazy: If True (default), only load skill header metadata (name,
                  description, tags) at registration time.  The full body
                  content is loaded on demand when first accessed.
        """
        self._skills: dict[str, Skill] = {}
        self._tags_index: dict[str, list[str]] = {}  # tag -> skill_names
        self._lazy = lazy

        if skills_dir:
            self.load_from_directory(skills_dir)

    def load_from_directory(self, skills_dir: str | Path, lazy: Optional[bool] = None) -> int:
        """
        Load all skills from a directory

        Args:
            skills_dir: Skills directory path
            lazy: Override the registry-level lazy setting for this call.
                  If None, uses the registry default.

        Returns:
            Number of skills loaded
        """
        use_lazy = self._lazy if lazy is None else lazy
        skills = SkillLoader.load_skills_from_directory(Path(skills_dir), lazy=use_lazy)
        for skill in skills:
            self.register(skill)
        return len(skills)

    def register(self, skill: Skill) -> None:
        """Register a skill"""
        self._skills[skill.name] = skill

        # Update tag index
        for tag in skill.tags:
            if tag not in self._tags_index:
                self._tags_index[tag] = []
            if skill.name not in self._tags_index[tag]:
                self._tags_index[tag].append(skill.name)

    def get(self, name: str) -> Optional[Skill]:
        """Get a skill by name"""
        return self._skills.get(name)

    def get_by_tag(self, tag: str) -> list[Skill]:
        """Get all skills matching a tag"""
        skill_names = self._tags_index.get(tag, [])
        return [self._skills[name] for name in skill_names if name in self._skills]

    def get_many(self, names: list[str]) -> list[Skill]:
        """Get multiple skills"""
        return [self._skills[name] for name in names if name in self._skills]

    def list_skills(self) -> list[str]:
        """List all registered skill names"""
        return list(self._skills.keys())

    def list_tags(self) -> list[str]:
        """List all tags"""
        return list(self._tags_index.keys())

    def get_skills_prompt(self, skill_names: list[str]) -> str:
        """
        Generate prompt fragment for specified skills

        Args:
            skill_names: List of skill names to include

        Returns:
            Formatted prompt string
        """
        skills = self.get_many(skill_names)
        if not skills:
            return ""

        sections = [skill.get_prompt_section() for skill in skills]
        return "<skills>\n" + "\n---\n".join(sections) + "\n</skills>"

    def get_all_skills_prompt(self) -> str:
        """Generate prompt fragment for all skills"""
        return self.get_skills_prompt(self.list_skills())

    def get_skills_summary(self) -> str:
        """
        Generate skills summary list (used by orchestrator for decisions)

        Returns:
            Formatted summary string
        """
        if not self._skills:
            return "<available_skills>\nNo skills registered.\n</available_skills>"

        lines = ["<available_skills>"]
        for name, skill in self._skills.items():
            tags_str = f" [{', '.join(skill.tags)}]" if skill.tags else ""
            lines.append(f"- {name}: {skill.description}{tags_str}")
        lines.append("</available_skills>")

        return "\n".join(lines)

    def get_skills_summary_for(self, skill_names: list[str]) -> str:
        """
        Generate a skills summary for a specific set of skill names.

        Only includes name, description, and tags — no body content.
        This is used by ``BaseAgent.get_system_prompt()`` to give the LLM a
        lightweight overview of available skills so it can decide which to load
        via the ``load_skill`` tool.

        Args:
            skill_names: List of skill names to include

        Returns:
            Formatted summary string
        """
        skills = self.get_many(skill_names)
        if not skills:
            return "<available_skills>\nNo skills available.\n</available_skills>"

        lines = ["<available_skills>"]
        for skill in skills:
            tags_str = f" [{', '.join(skill.tags)}]" if skill.tags else ""
            lines.append(f"- {skill.name}: {skill.description}{tags_str}")
        lines.append("</available_skills>")

        return "\n".join(lines)
