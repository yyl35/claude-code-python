#!/usr/bin/env python3
"""
测试日期问题：确保代理获取的是2026年的数据而不是2024年的
"""

import asyncio
import sys
import os
from datetime import datetime

# 在Windows上设置UTF-8编码
if sys.platform == "win32":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

# 添加项目根目录到Python路径
sys.path.insert(0, '.')

async def test_date_issue():
    '''测试日期问题'''
    print('测试股票查询日期问题...')
    print(f'当前系统日期: {datetime.now().strftime("%Y-%m-%d")}')
    print('期望: 代理应该获取2026年的数据，而不是2024年的')

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
        query = '查一下600095.sh最新收盘价'
        print(f'\n查询: {query}')

        # 直接调用代理执行器，查看工具调用参数
        print('\n[调试] 开始执行...')
        result = await agent.execute_direct(query)

        # 检查结果中的日期
        print(f'\n结果分析:')
        print(f'结果长度: {len(result)} 字符')

        # 检查是否包含2024年或2026年
        if '2024' in result:
            print('[问题] 结果包含2024年数据，而不是最新的2026年数据')
        elif '2026' in result:
            print('[成功] 结果包含2026年数据，日期正确')
        else:
            print('[信息] 结果中没有明确的年份信息')

        # 显示部分结果
        print(f'\n结果片段:')
        print(result[:500] if len(result) > 500 else result)

        # 检查原始表格数据中的日期
        if '| date |' in result:
            # 提取表格中的日期
            lines = result.split('\n')
            for line in lines:
                if '2026-' in line and '|' in line:
                    print(f'\n找到2026年数据行: {line}')
                    break
                elif '2024-' in line and '|' in line:
                    print(f'\n找到2024年数据行: {line}')
                    break

    except Exception as e:
        print(f'[错误] 测试失败: {e}')
        import traceback
        traceback.print_exc()
        return False

    return True

async def test_tool_direct():
    '''直接测试工具，验证工具能获取2026年数据'''
    print('\n' + '='*60)
    print('直接测试MCP工具，验证能获取2026年数据')
    print('='*60)

    try:
        from src.config import config
        from src.tool_manager import MCPToolManager

        tool_manager = MCPToolManager(config.mcp_server_url)
        tools = await tool_manager.fetch_tools()

        # 查找get_historical_k_data工具
        k_data_tool = None
        for tool in tools:
            if tool.name == 'get_historical_k_data':
                k_data_tool = tool
                break

        if k_data_tool:
            print('测试工具: get_historical_k_data')

            # 测试获取2026年数据
            result = await k_data_tool.coroutine(
                code='sh.600095',
                start_date='2026-01-01',
                end_date='2026-04-12',
                frequency='d',
                adjust_flag='3'
            )

            print(f'\n工具调用结果 (前500字符):')
            print(result[:500])

            # 检查是否包含2026年数据
            if '2026-' in result:
                print('\n[成功] 工具能正确获取2026年数据')
            else:
                print('\n[问题] 工具没有返回2026年数据')
        else:
            print('[错误] 未找到get_historical_k_data工具')

    except Exception as e:
        print(f'[错误] 直接工具测试失败: {e}')
        return False

    return True

async def main():
    '''主函数'''
    print('股票查询日期问题测试')
    print('=' * 60)

    # 测试直接工具调用
    tool_ok = await test_tool_direct()

    print('\n' + '='*60)
    print('测试代理执行器日期处理')
    print('='*60)

    # 测试代理执行器
    agent_ok = await test_date_issue()

    print('\n' + '='*60)
    if tool_ok and agent_ok:
        print('[总结] 工具能获取2026年数据，但代理可能使用了错误的日期参数')
        print('需要检查代理生成工具参数时的日期逻辑')
    else:
        print('[总结] 测试发现问题')

    return 0 if tool_ok else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)