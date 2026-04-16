#!/usr/bin/env python3
"""
测试创建目录功能
"""

import asyncio
import sys

sys.path.insert(0, '.')

async def test_create_directory():
    """测试创建目录"""
    from src.config import config
    from src.tool_manager import MCPToolManager
    from src.skill_manager import SkillManager
    from src.agent_executor import AgentExecutor

    print("初始化代理执行器...")
    tool_manager = MCPToolManager(config.mcp_server_url)
    skill_manager = SkillManager()
    agent = AgentExecutor(config, tool_manager, skill_manager)

    await agent.initialize()

    # 测试创建目录
    test_query = "在D盘帮我创建一个新目录swdownload"
    print(f"\n测试查询: {test_query}")

    result = await agent.execute_direct(test_query)
    print(f"\n结果 (前500字符):")
    print(result[:500] if len(result) > 500 else result)

    # 检查结果是否包含模型总结
    if "工具" in result and "执行成功" in result and "根据" not in result:
        print("\n警告: 返回的是原始工具输出，不是模型总结！")
    elif "根据" in result or "我来为您" in result or "总结" in result:
        print("\n成功: 返回的是模型总结结果！")
    else:
        print("\n未知: 无法确定返回格式")

async def main():
    """主函数"""
    print("=" * 60)
    print("创建目录功能测试")
    print("=" * 60)

    try:
        await test_create_directory()
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