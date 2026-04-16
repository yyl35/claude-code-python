#!/usr/bin/env python3
"""
测试依赖缺失自动修复功能
"""

import asyncio
import sys
import io

# 设置UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, '.')

async def test_dependency_fix():
    """测试依赖缺失自动修复"""
    from src.config import config
    from src.tool_manager import MCPToolManager
    from src.skill_manager import SkillManager
    from src.agent_executor import AgentExecutor

    print("初始化代理执行器...")
    tool_manager = MCPToolManager(config.mcp_server_url)
    skill_manager = SkillManager()
    agent = AgentExecutor(config, tool_manager, skill_manager)

    await agent.initialize()

    # 测试运行程序（模拟缺少依赖的情况）
    test_query = "运行E:\\project\\max_drawdown_calculator.py程序"
    print(f"\n测试查询: {test_query}")

    result = await agent.execute_direct(test_query)
    print(f"\n结果长度: {len(result)} 字符")
    print(f"前300字符:")
    print(result[:300])

    # 检查代理是否尝试安装依赖
    if "pip install" in result or "安装" in result or "依赖" in result:
        print("\n✅ 成功: 代理识别到缺少依赖并尝试安装！")
    else:
        print("\n❌ 失败: 代理没有尝试安装依赖")

async def main():
    """主函数"""
    print("=" * 60)
    print("依赖缺失自动修复测试")
    print("=" * 60)

    try:
        await test_dependency_fix()
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)