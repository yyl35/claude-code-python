#!/usr/bin/env python3
"""
简单测试代理修复
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

    # 只测试股票查询
    test_input = "湘财证券的股票价格"

    print(f"\n测试: {test_input}")
    print('='*60)

    try:
        result = await agent.process_task(test_input)
        print(f"\n结果 (长度: {len(result)}):")
        print("="*60)
        print(result[:1000])  # 只打印前1000字符
        print("="*60)

        # 保存结果到文件
        with open("test_result.txt", "w", encoding="utf-8") as f:
            f.write(result)
        print("结果已保存到 test_result.txt")

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent())