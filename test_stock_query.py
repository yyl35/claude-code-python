#!/usr/bin/env python3
"""
测试股票查询功能
"""

import asyncio
import sys
import os
from pathlib import Path

# 在Windows上设置UTF-8编码
if sys.platform == "win32":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_stock_query():
    """测试股票查询"""
    print("测试股票查询功能...")

    try:
        from src.config import config
        from src.tool_manager import MCPToolManager
        from src.skill_manager import SkillManager
        from src.agent_executor import AgentExecutor

        # 创建代理执行器
        tool_manager = MCPToolManager(config.mcp_server_url)
        skill_manager = SkillManager()
        agent = AgentExecutor(config, tool_manager, skill_manager)

        # 初始化
        await agent.initialize()

        # 测试查询
        test_queries = [
            "查一下600095.sh最新收盘价",
            "获取贵州茅台(600519)的股票数据",
            "查看平安银行(000001)的股价"
        ]

        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"查询: {query}")
            print(f"{'='*60}")

            try:
                result = await agent.execute_direct(query)
                print(f"结果:\n{result}")
                print(f"结果长度: {len(result)} 字符")

                # 检查结果是否包含原始表格数据
                if "| date | code |" in result or "|:-----------|:----------|" in result:
                    print("[警告] 结果包含原始表格数据，总结功能可能未正常工作")
                elif "执行成功" in result and len(result) < 1000:
                    print("[成功] 结果看起来已经过总结")
                else:
                    print("[信息] 返回了处理后的结果")

            except Exception as e:
                print(f"[错误] 查询失败: {e}")

    except ImportError as e:
        print(f"[错误] 导入失败: {e}")
        return False
    except Exception as e:
        print(f"[错误] 测试失败: {e}")
        return False

    return True

async def main():
    """主函数"""
    print("股票查询功能测试")
    print("=" * 60)

    success = await test_stock_query()

    print("\n" + "=" * 60)
    if success:
        print("[成功] 测试完成")
        print("\n说明:")
        print("1. 如果看到原始表格数据，说明总结功能未正常工作")
        print("2. 如果看到简洁的分析结果，说明修复成功")
        print("3. 结果应该类似: '600095.sh最新收盘价为X元，较昨日变化Y%...'")
    else:
        print("[失败] 测试失败")

    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)