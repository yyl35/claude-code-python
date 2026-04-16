#!/usr/bin/env python3
"""
基本使用示例 - 修复版本
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ["OPENAI_API_KEY"] = "sk-88b906f7af2d4681aac5451a954360d9"
os.environ["OPENAI_BASE_URL"] = "https://api.deepseek.com/v1"
os.environ["MCP_SERVER_URL"] = "http://127.0.0.1:8000/sse"
os.environ["WORKSPACE_PATH"] = "./test_workspace"
os.environ["MEMORY_PATH"] = "test_memory.json"

from src.main import DevOpsAgent

async def main():
    """示例：使用DevOps代理执行任务"""

    # 创建代理实例
    agent = DevOpsAgent()

    # 初始化
    print("初始化代理...")
    try:
        if not await agent.initialize():
            print("初始化失败")
            return
    except Exception as e:
        print(f"初始化错误: {e}")
        print("注意: 需要真实的API密钥和MCP服务器才能完全运行")
        return

    # 示例任务
    tasks = [
        "查一下平安银行.sh 2024年的净利润",
    ]

    for task in tasks:
        print(f"\n{'='*60}")
        print(f"执行任务: {task}")
        print(f"{'='*60}")

        try:
            result = await agent.process_task(task)
            print(f"\n结果长度: {len(result)} 字符")
            print(f"\n结果:\n{result[:2000]}")  # 显示更多字符
            if len(result) > 2000:
                print(f"... (还有 {len(result) - 2000} 字符未显示)")
        except Exception as e:
            print(f"任务执行失败: {e}")
            print("这可能是由于缺少真实的API密钥或MCP服务器未运行")

    print("\n所有任务完成！")

if __name__ == "__main__":
    asyncio.run(main())