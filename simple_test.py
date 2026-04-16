#!/usr/bin/env python3
"""
简单导入测试 - 使用ASCII字符
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试导入所有模块"""
    modules_to_test = [
        "src.config",
        "src.tool_manager",
        "src.task_parser",
        "src.skill_manager",
        "src.agent_executor",
        "src.state_manager",
        "src.main"
    ]

    print("Testing module imports...")

    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"OK  {module_name}")
        except ImportError as e:
            print(f"FAIL {module_name}: {e}")
            import traceback
            traceback.print_exc()
            return False
        except Exception as e:
            print(f"ERROR {module_name}: {e}")
            import traceback
            traceback.print_exc()
            return False

    return True

def test_basic_components():
    """测试基本组件"""
    print("\nTesting basic components...")

    try:
        # 测试配置
        from src.config import config
        print(f"OK  Config loaded: MCP server = {config.mcp_server_url}")

        # 测试技能管理器
        from src.skill_manager import SkillManager
        manager = SkillManager()
        skills = manager.list_skills()
        print(f"OK  Skill manager: {len(skills)} skills found")

        # 测试状态管理器
        from src.state_manager import StateManager
        import tempfile
        import asyncio

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            temp_path = tmp.name

        try:
            manager = StateManager(temp_path)

            async def test():
                await manager.load_state()
                await manager.record_task("test task")
                history = await manager.get_history()
                print(f"OK  State manager: {len(history)} tasks in history")

            asyncio.run(test())
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

        return True

    except Exception as e:
        print(f"FAIL Basic components: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("DevOps-Agent Simple Test")
    print("=" * 60)

    results = []
    results.append(test_imports())
    results.append(test_basic_components())

    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"Total tests: {len(results)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")

    if all(results):
        print("SUCCESS: All tests passed!")
        return 0
    else:
        print("FAILURE: Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())