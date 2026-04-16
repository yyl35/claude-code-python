#!/usr/bin/env python3
"""
直接测试工具调用
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_tool_direct():
    """直接测试工具调用"""
    print("直接测试工具调用...")

    try:
        from src.config import config
        from src.tool_manager import MCPToolManager

        # 创建工具管理器
        tool_manager = MCPToolManager(config.mcp_server_url)

        # 获取工具
        print("获取工具列表...")
        tools = await tool_manager.fetch_tools()
        print(f"找到 {len(tools)} 个工具")

        # 列出所有工具
        for i, tool in enumerate(tools, 1):
            print(f"{i}. {tool.name}: {tool.description}")

        # 查找股票数据工具
        stock_tools = [t for t in tools if "stock" in t.name.lower() or "k_data" in t.name.lower()]

        if not stock_tools:
            print("未找到股票数据工具")
            return False

        stock_tool = stock_tools[0]
        print(f"\n使用工具: {stock_tool.name}")

        # 测试调用工具
        print("\n测试调用股票数据工具...")
        try:
            # 尝试调用工具
            result = await stock_tool.coroutine(
                code="sh.600095",
                start_date="2026-01-01",
                end_date="2026-04-12",
                frequency="d",
                adjust_flag=3
            )

            print(f"工具调用成功!")
            print(f"结果长度: {len(str(result))} 字符")
            print(f"结果前200字符: {str(result)[:200]}...")

            return True

        except Exception as e:
            print(f"工具调用失败: {e}")
            return False

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_agent_with_tools():
    """测试代理使用工具"""
    print("\n\n测试代理使用工具...")

    try:
        from src.config import config
        from src.tool_manager import MCPToolManager
        from src.skill_manager import SkillManager
        from src.agent_executor import AgentExecutor

        # 创建代理
        tool_manager = MCPToolManager(config.mcp_server_url)
        skill_manager = SkillManager()
        agent = AgentExecutor(config, tool_manager, skill_manager)

        # 初始化
        await agent.initialize()

        # 测试查询
        query = "查一下600095.sh最新收盘价"
        print(f"查询: {query}")

        result = await agent.execute_direct(query)
        print(f"结果:\n{result}")
        print(f"结果长度: {len(result)} 字符")

        # 检查结果
        if "执行成功" in result and "|" in result:
            print("[警告] 返回了原始表格数据")
            return False
        elif len(result) > 100 and ("收盘" in result or "价格" in result):
            print("[成功] 返回了总结后的结果")
            return True
        else:
            print("[信息] 返回了其他类型的结果")
            return True

    except Exception as e:
        print(f"代理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("工具调用测试")
    print("=" * 60)

    # 测试直接工具调用
    tool_success = await test_tool_direct()

    # 测试代理使用工具
    agent_success = await test_agent_with_tools()

    print("\n" + "=" * 60)
    print("测试结果总结:")
    print(f"直接工具调用: {'成功' if tool_success else '失败'}")
    print(f"代理使用工具: {'成功' if agent_success else '失败'}")

    if tool_success and agent_success:
        print("\n[成功] 所有测试通过!")
        return 0
    else:
        print("\n[失败] 部分测试失败")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)