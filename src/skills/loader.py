"""
Skill Loader - 解析和加载 SKILL.md 文件

SKILL.md 格式:
---
name: skill_name
description: 简短描述
tags: [tag1, tag2]
---

# Skill 详细内容...
"""

import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

import yaml


@dataclass
class Skill:
    """表示一个已加载的 Skill"""
    name: str
    description: str
    content: str
    path: Path
    tags: list[str] = field(default_factory=list)
    scripts_dir: Optional[Path] = None
    resources_dir: Optional[Path] = None

    def get_prompt_section(self) -> str:
        """生成用于注入 system prompt 的内容"""
        return f"""## Skill: {self.name}
{self.description}

{self.content}
"""


class SkillLoader:
    """加载单个 Skill 或整个 Skill 目录"""

    FRONTMATTER_PATTERN = re.compile(
        r'^---\s*\n(.*?)\n---\s*\n(.*)$',
        re.DOTALL
    )

    @classmethod
    def load_skill(cls, skill_dir: Path) -> Optional[Skill]:
        """
        从 skill 目录加载一个 skill
        
        Args:
            skill_dir: skill 目录路径，必须包含 SKILL.md
            
        Returns:
            Skill 对象，如果加载失败返回 None
        """
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            return None

        raw_content = skill_file.read_text(encoding="utf-8")
        metadata, content = cls._parse_frontmatter(raw_content)

        # 从元数据或目录名获取 skill 名称
        name = metadata.get("name", skill_dir.name)
        description = metadata.get("description", "")
        tags = metadata.get("tags", [])

        # 检查可选的子目录
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
        从目录加载所有 skills
        
        Args:
            skills_root: skills 根目录
            
        Returns:
            Skill 对象列表
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
        解析 YAML frontmatter
        
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
        
        # 没有 frontmatter 或解析失败
        return {}, content
