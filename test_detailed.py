#!/usr/bin/env python3
"""
详细测试代理响应
"""

import asyncio
import json
from src.main import DevOpsAgent

async def test_agent():
    """测试代理响应"""
    print("初始化代理...")
    agent = DevOpsAgent()

    if not await agent.initialize():
        print("代理初始化失败")
        return

    # 测试股票查询
    test_input = "湘财证券的股票价格"

    print(f"\n测试: {test_input}")
    print('='*60)

    try:
        result = await agent.process_task(test_input)

        # 保存完整结果
        with open("detailed_result.txt", "w", encoding="utf-8") as f:
            f.write(f"输入: {test_input}\n")
            f.write(f"结果长度: {len(result)}\n")
            f.write("="*80 + "\n")
            f.write(result)

        print(f"结果长度: {len(result)} 字符")
        print(f"结果已保存到 detailed_result.txt")

        # 检查关键部分
        if len(result) < 100:
            print("警告: 结果太短!")

        # 检查是否包含工具调用信息
        lines = result.split('\n')
        print(f"行数: {len(lines)}")
        print("前10行:")
        for i, line in enumerate(lines[:10]):
            print(f"{i+1}: {line[:100]}...")

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent())