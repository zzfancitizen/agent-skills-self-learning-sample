"""
Skill-enabled Multi-Agent System

主入口点
"""

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(
        description="Skill-enabled Multi-Agent System"
    )
    parser.add_argument(
        "--skills-dir",
        type=str,
        default="./skills",
        help="Skills 目录路径"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="sap/anthropic--claude-4.5-opus",
        help="使用的模型"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="运行测试模式"
    )
    parser.add_argument(
        "--list-skills",
        action="store_true",
        help="列出所有可用的 skills"
    )
    parser.add_argument(
        "query",
        nargs="?",
        type=str,
        help="用户查询"
    )

    args = parser.parse_args()

    # 确保 skills 目录存在
    skills_path = Path(args.skills_dir)
    if not skills_path.exists():
        print(f"错误：Skills 目录不存在: {skills_path}")
        return 1

    # 加载 skills
    from src.skills import SkillRegistry
    registry = SkillRegistry(skills_path)

    # 列出 skills
    if args.list_skills:
        print("可用的 Skills:")
        print(registry.get_skills_summary())
        return 0

    # 测试模式
    if args.test:
        return run_test(registry, args.model)

    # 交互模式或单次查询
    if args.query:
        return run_single_query(args.query, registry, args.model)
    else:
        return run_interactive(registry, args.model)


def run_test(registry, model: str) -> int:
    """运行测试"""
    print("=" * 50)
    print("Skill-enabled Multi-Agent System 测试")
    print("=" * 50)

    # 测试 1: Skill 加载
    print("\n[测试 1] Skill 加载")
    skills = registry.list_skills()
    print(f"  已加载 {len(skills)} 个 skills: {skills}")

    # 测试 2: Skill prompt 生成
    print("\n[测试 2] Skill Prompt 生成")
    prompt = registry.get_skills_prompt(["routing"])
    print(f"  Routing skill prompt 长度: {len(prompt)} 字符")

    # 测试 3: 工作流创建
    print("\n[测试 3] 工作流创建")
    try:
        from src.graph import create_workflow
        workflow = create_workflow(registry, model=model)
        print("  工作流创建成功 ✓")
    except Exception as e:
        print(f"  工作流创建失败: {e}")
        return 1

    # 测试 4: 端到端测试（需要 API key）
    if os.getenv("ANTHROPIC_API_KEY"):
        print("\n[测试 4] 端到端测试")
        try:
            from src.graph import run_workflow
            result = run_workflow(
                "什么是机器学习？",
                skills_dir=str(registry._skills[list(registry._skills.keys())[0]].path.parent) if registry._skills else "./skills",
                model=model
            )
            print(f"  响应: {result[:200]}..." if len(result) > 200 else f"  响应: {result}")
            print("  端到端测试成功 ✓")
        except Exception as e:
            print(f"  端到端测试失败: {e}")
            return 1
    else:
        print("\n[测试 4] 端到端测试 (跳过 - 未设置 ANTHROPIC_API_KEY)")

    print("\n" + "=" * 50)
    print("所有测试通过 ✓")
    print("=" * 50)
    return 0


def run_single_query(query: str, registry, model: str) -> int:
    """运行单次查询"""
    from src.graph import run_workflow

    print(f"处理查询: {query}\n")
    result = run_workflow(
        query,
        skills_dir=str(list(registry._skills.values())[0].path.parent) if registry._skills else "./skills",
        model=model
    )
    print(result)
    return 0


def run_interactive(registry, model: str) -> int:
    """交互模式"""
    from src.graph import run_workflow

    print("Skill-enabled Multi-Agent System")
    print("输入 'quit' 或 'exit' 退出")
    print("-" * 40)

    skills_dir = str(list(registry._skills.values())[0].path.parent) if registry._skills else "./skills"

    while True:
        try:
            query = input("\n你: ").strip()
            if not query:
                continue
            if query.lower() in ("quit", "exit", "q"):
                print("再见！")
                break

            result = run_workflow(query, skills_dir=skills_dir, model=model)
            print(f"\nAgent: {result}")

        except KeyboardInterrupt:
            print("\n再见！")
            break
        except Exception as e:
            print(f"\n错误: {e}")

    return 0


if __name__ == "__main__":
    exit(main())
