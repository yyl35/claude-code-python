#!/usr/bin/env python3
"""
测试MCP工具列表
"""

import asyncio
import sys

sys.path.insert(0, '.')

async def test_tools():
    """测试工具列表"""
    from src.tool_manager import MCPToolManager

    tm = MCPToolManager('http://127.0.0.1:8000/sse')
    tools = await tm.fetch_tools()

    print(f'Total tools: {len(tools)}')
    print('\nTool names (first 30):')
    for i, t in enumerate(tools[:30], 1):
        print(f'{i}. {t.name}')

    print('\nSearching for file/directory related tools:')
    file_tools = []
    for t in tools:
        if 'file' in t.name.lower() or 'dir' in t.name.lower() or 'path' in t.name.lower():
            file_tools.append(t.name)

    for name in file_tools:
        print(f'  - {name}')

async def main():
    """主函数"""
    print("=" * 60)
    print("MCP工具列表测试")
    print("=" * 60)

    try:
        await test_tools()
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)