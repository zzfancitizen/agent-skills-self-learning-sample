"""
Skill Registry - 管理和查询已加载的 Skills
"""

from pathlib import Path
from typing import Optional

from .loader import Skill, SkillLoader


class SkillRegistry:
    """
    Skill 注册中心
    
    提供 skill 的注册、查询和 prompt 生成功能
    """

    def __init__(self, skills_dir: Optional[str | Path] = None):
        """
        初始化 Registry
        
        Args:
            skills_dir: 可选的 skills 目录路径，如果提供会自动加载
        """
        self._skills: dict[str, Skill] = {}
        self._tags_index: dict[str, list[str]] = {}  # tag -> skill_names

        if skills_dir:
            self.load_from_directory(skills_dir)

    def load_from_directory(self, skills_dir: str | Path) -> int:
        """
        从目录加载所有 skills
        
        Returns:
            加载的 skill 数量
        """
        skills = SkillLoader.load_skills_from_directory(Path(skills_dir))
        for skill in skills:
            self.register(skill)
        return len(skills)

    def register(self, skill: Skill) -> None:
        """注册一个 skill"""
        self._skills[skill.name] = skill
        
        # 更新 tag 索引
        for tag in skill.tags:
            if tag not in self._tags_index:
                self._tags_index[tag] = []
            if skill.name not in self._tags_index[tag]:
                self._tags_index[tag].append(skill.name)

    def get(self, name: str) -> Optional[Skill]:
        """按名称获取 skill"""
        return self._skills.get(name)

    def get_by_tag(self, tag: str) -> list[Skill]:
        """按 tag 获取所有相关 skills"""
        skill_names = self._tags_index.get(tag, [])
        return [self._skills[name] for name in skill_names if name in self._skills]

    def get_many(self, names: list[str]) -> list[Skill]:
        """获取多个 skills"""
        return [self._skills[name] for name in names if name in self._skills]

    def list_skills(self) -> list[str]:
        """列出所有已注册的 skill 名称"""
        return list(self._skills.keys())

    def list_tags(self) -> list[str]:
        """列出所有 tags"""
        return list(self._tags_index.keys())

    def get_skills_prompt(self, skill_names: list[str]) -> str:
        """
        生成指定 skills 的 prompt 片段
        
        Args:
            skill_names: 要包含的 skill 名称列表
            
        Returns:
            格式化的 prompt 字符串
        """
        skills = self.get_many(skill_names)
        if not skills:
            return ""

        sections = [skill.get_prompt_section() for skill in skills]
        return "<skills>\n" + "\n---\n".join(sections) + "\n</skills>"

    def get_all_skills_prompt(self) -> str:
        """生成所有 skills 的 prompt 片段"""
        return self.get_skills_prompt(self.list_skills())

    def get_skills_summary(self) -> str:
        """
        生成 skills 的摘要列表（用于 orchestrator 做决策）
        
        Returns:
            格式化的摘要字符串
        """
        if not self._skills:
            return "<available_skills>\nNo skills registered.\n</available_skills>"

        lines = ["<available_skills>"]
        for name, skill in self._skills.items():
            tags_str = f" [{', '.join(skill.tags)}]" if skill.tags else ""
            lines.append(f"- {name}: {skill.description}{tags_str}")
        lines.append("</available_skills>")

        return "\n".join(lines)
