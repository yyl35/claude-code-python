#!/usr/bin/env python3
"""
简单演示 - 不依赖外部API
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置环境变量（使用测试值）
os.environ["OPENAI_API_KEY"] = "sk-test-key-demo"
os.environ["OPENAI_BASE_URL"] = "https://api.deepseek.com/v1"
os.environ["MCP_SERVER_URL"] = "http://127.0.0.1:8000/sse"
os.environ["WORKSPACE_PATH"] = "./test_workspace"
os.environ["MEMORY_PATH"] = "test_memory.json"

def test_config():
    """测试配置加载"""
    print("1. 测试配置加载...")
    try:
        from src.config import config
        print(f"   OK 配置加载成功")
        print(f"     MCP服务器: {config.mcp_server_url}")
        print(f"     工作空间: {config.workspace_path}")
        print(f"     模型名称: {config.model_name}")
        return True
    except Exception as e:
        print(f"   FAIL 配置加载失败: {e}")
        return False

def test_skill_manager():
    """测试技能管理器"""
    print("\n2. 测试技能管理器...")
    try:
        from src.skill_manager import SkillManager

        manager = SkillManager()
        skills = manager.list_skills()

        print(f"   OK 技能管理器初始化成功")
        print(f"     可用技能: {list(skills.keys())}")

        for name, desc in skills.items():
            print(f"     - {name}: {desc}")

        return True
    except Exception as e:
        print(f"   FAIL 技能管理器测试失败: {e}")
        return False

def test_state_manager():
    """测试状态管理器"""
    print("\n3. 测试状态管理器...")
    try:
        from src.state_manager import StateManager
        import tempfile

        # 使用临时文件
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as tmp:
            temp_path = tmp.name

        try:
            manager = StateManager(temp_path)

            async def test():
                await manager.load_state()
                await manager.record_task("演示任务1")
                await manager.record_task("演示任务2")
                await manager.record_result("演示任务1", "成功完成")

                history = await manager.get_history()
                print(f"   OK 状态管理器工作正常")
                print(f"     历史记录数: {len(history)}")

                if history:
                    print(f"     最近任务: {history[0]['input'][:30]}...")
                    print(f"     任务状态: {history[0]['status']}")

                await manager.save_state()
                print(f"   ✓ 状态保存成功")

            asyncio.run(test())
            return True
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    except Exception as e:
        print(f"   ✗ 状态管理器测试失败: {e}")
        return False

def test_module_structure():
    """测试模块结构"""
    print("\n4. 测试模块结构...")

    modules = [
        ("配置模块", "src.config"),
        ("技能管理器", "src.skill_manager"),
        ("状态管理器", "src.state_manager"),
        ("任务解析器", "src.task_parser"),
        ("工具管理器", "src.tool_manager"),
        ("代理执行器", "src.agent_executor"),
        ("主模块", "src.main"),
    ]

    all_ok = True
    for name, module_path in modules:
        try:
            __import__(module_path)
            print(f"   ✓ {name}导入成功")
        except ImportError as e:
            if "langchain" in str(e) or "mcp" in str(e):
                print(f"   ⚠ {name}需要外部依赖: {e}")
            else:
                print(f"   ✗ {name}导入失败: {e}")
                all_ok = False
        except Exception as e:
            print(f"   ✗ {name}导入失败: {e}")
            all_ok = False

    return all_ok

def main():
    print("=" * 60)
    print("DevOps-Agent 简单演示")
    print("=" * 60)
    print("这个演示测试核心模块，不依赖外部API")
    print("=" * 60)

    tests = [
        ("配置测试", test_config),
        ("技能管理器测试", test_skill_manager),
        ("状态管理器测试", test_state_manager),
        ("模块结构测试", test_module_structure),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n[{name}]")
        result = test_func()
        results.append(result)

    print("\n" + "=" * 60)
    print("演示结果:")
    print("=" * 60)

    for i, (name, _) in enumerate(tests):
        status = "通过" if results[i] else "失败"
        print(f"  {name:20} {status}")

    print(f"\n总计: {len(tests)} 项测试")
    print(f"通过: {sum(results)} 项")
    print(f"失败: {len(results) - sum(results)} 项")

    if all(results):
        print("\n✅ 所有核心模块测试通过!")
        print("\n下一步:")
        print("1. 设置真实的DeepSeek API密钥")
        print("2. 启动MCP服务器 (127.0.0.1:8000)")
        print("3. 运行: python -m src.main --interactive")
    else:
        print("\n❌ 部分测试失败，请检查错误信息")

    return 0 if all(results) else 1

if __name__ == "__main__":
    sys.exit(main())