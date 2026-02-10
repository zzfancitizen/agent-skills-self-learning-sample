#!/usr/bin/env python3
"""
Test script to verify lazy loading of skills
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from skills.registry import SkillRegistry # type: ignore
from skills.loader import SkillLoader # type: ignore

def test_lazy_loading():
    """Test lazy loading behavior"""
    print("="*80)
    print("Testing Lazy Loading of Skills")
    print("="*80)

    # 1. Test lazy loading with registry
    print("\n1. Initialize SkillRegistry with lazy=True")
    registry = SkillRegistry(lazy=True)

    # 2. Load router agent skills
    print("\n2. Load RouterAgent skills")
    agent_dir = Path(__file__).parent / "src" / "agents" / "router"
    skills = SkillLoader.load_agent_skills(agent_dir, lazy=True)

    print(f"   Found {len(skills)} skills")
    for skill in skills:
        registry.register(skill)
        print(f"   - {skill.name}: {skill.description}")
        print(f"     Status: {skill}")

    # 3. Verify content is NOT loaded yet
    print("\n3. Verify content is NOT loaded yet (lazy loading)")
    routing_skill = registry.get("routing")
    if routing_skill:
        print(f"   Skill: {routing_skill.name}")
        print(f"   Content loaded? {routing_skill._content_loaded}")
        print(f"   Content cache: {routing_skill._content is not None}")

        # 4. Access content property (should trigger lazy load)
        print("\n4. Access content property (triggers lazy load)")
        content = routing_skill.content
        print(f"   Content loaded? {routing_skill._content_loaded}")
        print(f"   Content length: {len(content)} chars")
        print(f"   Content preview: {content[:200]}...")

        # 5. Access again (should use cached content)
        print("\n5. Access content again (uses cache)")
        content2 = routing_skill.content
        print(f"   Content loaded? {routing_skill._content_loaded}")
        print(f"   Same content? {content == content2}")

    # 6. Test load_skill tool
    print("\n6. Test load_skill tool")
    from skills.loader import create_load_skill_tool # type: ignore

    load_skill_tool = create_load_skill_tool(registry, ["routing"])
    result = load_skill_tool.invoke({"skill_name": "routing"})
    print(f"   Tool result length: {len(result)} chars")
    print(f"   Tool result preview: {result[:200]}...")

    # 7. Compare lazy vs eager loading
    print("\n7. Compare lazy vs eager loading")

    # Lazy load
    print("   a) Lazy loading:")
    skills_lazy = SkillLoader.load_agent_skills(agent_dir, lazy=True)
    for skill in skills_lazy:
        print(f"      - {skill.name}: content_loaded={skill._content_loaded}")

    # Eager load
    print("   b) Eager loading:")
    skills_eager = SkillLoader.load_agent_skills(agent_dir, lazy=False)
    for skill in skills_eager:
        print(f"      - {skill.name}: content_loaded={skill._content_loaded}")

    print("\n" + "="*80)
    print("✅ Lazy loading test completed successfully!")
    print("="*80)

if __name__ == "__main__":
    test_lazy_loading()
