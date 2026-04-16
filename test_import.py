#!/usr/bin/env python3
"""
测试所有模块能否正常导入
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

    print("测试模块导入...")

    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"[OK] {module_name}")
        except ImportError as e:
            print(f"✗ {module_name}: {e}")
            # 打印更详细的错误信息
            import traceback
            traceback.print_exc()
            return False

    return True

def test_config_creation():
    """测试配置创建"""
    print("\n测试配置创建...")
    try:
        from src.config import config
        print(f"[OK] 配置加载成功")
        print(f"  MCP服务器: {config.mcp_server_url}")
        print(f"  工作空间: {config.workspace_path}")
        return True
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_skill_manager():
    """测试技能管理器"""
    print("\n测试技能管理器...")
    try:
        from src.skill_manager import SkillManager, BaseSkill

        manager = SkillManager()
        skills = manager.list_skills()

        print(f"[OK] 技能管理器初始化成功")
        print(f"  发现 {len(skills)} 个技能:")
        for name, desc in skills.items():
            print(f"    - {name}: {desc}")

        # 测试技能继承
        class TestSkill(BaseSkill):
            def __init__(self):
                super().__init__("test_skill", "测试技能")
                self.required_tools = ["test_tool"]

            async def execute(self, task_description, tool_executor):
                return "测试执行成功"

        print(f"[OK] BaseSkill继承测试通过")
        return True

    except Exception as e:
        print(f"✗ 技能管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_state_manager():
    """测试状态管理器"""
    print("\n测试状态管理器...")
    try:
        from src.state_manager import StateManager
        import asyncio

        # 创建临时文件路径
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            temp_path = tmp.name

        try:
            manager = StateManager(temp_path)

            async def test_async():
                await manager.load_state()
                await manager.record_task("测试任务")
                await manager.record_result("测试任务", "测试结果")
                history = await manager.get_history()

                print(f"[OK] 状态管理器测试通过")
                print(f"  历史记录数: {len(history)}")
                if history:
                    print(f"  最近任务: {history[0]['input']}")

                await manager.clear_history()
                await manager.save_state()

            asyncio.run(test_async())

        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)

        return True

    except Exception as e:
        print(f"✗ 状态管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("DevOps-Agent Project Import Test")
    print("=" * 60)

    results = []

    results.append(test_imports())
    results.append(test_config_creation())
    results.append(test_skill_manager())
    results.append(test_state_manager())

    print("\n" + "=" * 60)
    print("测试结果总结:")
    print(f"总测试数: {len(results)}")
    print(f"通过数: {sum(results)}")
    print(f"失败数: {len(results) - sum(results)}")

    if all(results):
        print("✅ 所有测试通过！")
        return 0
    else:
        print("❌ 部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())