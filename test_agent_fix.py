#!/usr/bin/env python3
"""
测试代理修复：确保代理调用工具而不是凭空回答
"""

import asyncio
import sys
from src.main import DevOpsAgent

async def test_agent():
    """测试代理是否调用工具"""
    print("初始化代理...")
    agent = DevOpsAgent()

    if not await agent.initialize():
        print("代理初始化失败")
        return

    # 测试股票查询
    test_cases = [
        "湘财证券的股票价格",
        "读取/etc/hosts文件",
        "执行ls -la命令",
    ]

    for test_input in test_cases:
        print(f"\n{'='*60}")
        print(f"测试: {test_input}")
        print('='*60)

        try:
            result = await agent.process_task(test_input)
            # 使用repr打印以避免编码问题
            print(f"\n结果 (长度: {len(result)}):")
            print(repr(result[:500]))  # 只打印前500字符

            # 检查结果是否包含工具调用指示
            if "工具" in result or "执行" in result or "获取" in result:
                print("✓ 代理似乎调用了工具")
            else:
                print("⚠ 代理可能没有调用工具")

        except Exception as e:
            print(f"测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent())