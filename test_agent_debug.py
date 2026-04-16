#!/usr/bin/env python3
"""
调试代理工具调用
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def debug_agent():
    """调试代理工具调用"""
    print("调试代理工具调用...")

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

        # 测试不同的查询方式
        test_queries = [
            # 明确指定工具参数
            "使用get_historical_k_data工具获取sh.600095的最新收盘价，时间范围从2026-01-01到2026-04-12",
            # 简单查询
            "sh.600095的最新收盘价是多少？",
            # 中文查询
            "查一下600095.sh最新收盘价",
            # 详细查询
            "获取贵州茅台(600519)过去3个月的股票数据，包括开盘价、收盘价、最高价、最低价"
        ]

        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*60}")
            print(f"测试 {i}: {query}")
            print(f"{'='*60}")

            try:
                result = await agent.execute_direct(query)
                print(f"结果长度: {len(result)} 字符")
                print(f"结果预览: {result[:200]}...")

                # 分析结果
                if "| date | code |" in result:
                    print("[警告] 包含原始表格数据")
                elif "执行成功" in result and "工具" in result:
                    print("[信息] 包含工具执行结果")
                elif "收盘" in result or "价格" in result:
                    print("[成功] 包含价格信息")
                else:
                    print("[信息] 其他类型的结果")

            except Exception as e:
                print(f"[错误] 查询失败: {e}")
                import traceback
                traceback.print_exc()

    except Exception as e:
        print(f"[错误] 调试失败: {e}")
        import traceback
        traceback.print_exc()

async def test_tool_with_correct_params():
    """使用正确参数测试工具"""
    print("\n\n使用正确参数测试工具...")

    try:
        from src.config import config
        from src.tool_manager import MCPToolManager

        tool_manager = MCPToolManager(config.mcp_server_url)
        tools = await tool_manager.fetch_tools()

        # 找到股票数据工具
        stock_tool = next((t for t in tools if t.name == "get_historical_k_data"), None)
        if not stock_tool:
            print("未找到get_historical_k_data工具")
            return

        print(f"找到工具: {stock_tool.name}")

        # 使用正确参数调用
        result = await stock_tool.coroutine(
            code="sh.600095",
            start_date="2026-01-01",
            end_date="2026-04-12",
            frequency="d",
            adjust_flag="3"  # 字符串，不是数字
        )

        print(f"工具调用成功!")
        print(f"结果长度: {len(str(result))} 字符")
        print(f"结果前300字符:\n{str(result)[:300]}...")

        # 检查结果格式
        if "| date | code |" in str(result):
            print("[成功] 返回了表格数据")
        else:
            print("[警告] 未返回表格数据")

    except Exception as e:
        print(f"[错误] 工具测试失败: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    print("代理工具调用调试")
    print("=" * 60)

    await debug_agent()
    await test_tool_with_correct_params()

    print("\n" + "=" * 60)
    print("调试完成")

if __name__ == "__main__":
    asyncio.run(main())