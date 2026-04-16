#!/usr/bin/env python3
"""
简单测试代理执行器修复
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_agent_logic():
    """测试代理逻辑"""
    print("测试代理执行器修复...")

    try:
        from src.agent_executor import AgentExecutor

        # 创建一个简单的模拟代理执行器来测试逻辑
        class MockConfig:
            openai_api_key = "test"
            openai_base_url = "https://api.deepseek.com/v1"
            model_name = "deepseek-chat"
            max_iterations = 10

        class MockToolManager:
            async def fetch_tools(self):
                return []

        class MockSkillManager:
            pass

        config = MockConfig()
        tool_manager = MockToolManager()
        skill_manager = MockSkillManager()

        agent = AgentExecutor(config, tool_manager, skill_manager)

        # 测试 _should_summarize 方法
        print("\n1. 测试 _should_summarize 方法:")
        result = agent._should_summarize([{"tool": "test"}], "test query")
        print(f"   _should_summarize 返回: {result}")
        print(f"   预期: False (因为现在完全由模型控制)")

        if result == False:
            print("   [OK] _should_summarize 修复正确")
        else:
            print("   [ERROR] _should_summarize 仍然有问题")
            return False

        # 检查系统提示词
        print("\n2. 检查系统提示词更新:")
        # 通过读取文件来检查
        with open("src/agent_executor.py", "r", encoding="utf-8") as f:
            content = f.read()

        if "执行流程控制：" in content and "你完全控制执行流程" in content:
            print("   [OK] 系统提示词已更新")
        else:
            print("   [ERROR] 系统提示词可能未正确更新")
            return False

        # 检查代码逻辑修改
        print("\n3. 检查代码逻辑修改:")
        if "if iteration >= self.max_iterations or self._should_summarize" not in content:
            print("   [OK] 移除了自动总结逻辑")
        else:
            print("   [ERROR] 自动总结逻辑可能仍然存在")
            # 检查是否修改为正确的逻辑
            if "if not tool_calls and response.content and len(response.content) > 10:" in content:
                print("   [OK] 已添加模型控制结束逻辑")
            else:
                print("   [ERROR] 未添加模型控制结束逻辑")
                return False

        return True

    except Exception as e:
        print(f"[错误] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("代理执行器修复测试")
    print("=" * 60)

    success = await test_agent_logic()

    print("\n" + "=" * 60)
    if success:
        print("[成功] 代码修复验证通过")
        print("\n修复总结:")
        print("1. 移除了 _should_summarize 自动触发逻辑")
        print("2. 添加了模型控制结束的逻辑")
        print("3. 更新了系统提示词，强调模型完全控制流程")
        print("4. 代理现在应该能处理复合任务而不中途停止")
    else:
        print("[失败] 修复验证失败")

    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)