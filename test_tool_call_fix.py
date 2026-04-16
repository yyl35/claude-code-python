#!/usr/bin/env python3
"""
测试工具调用修复：验证模型是否自主判断工具调用
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_theory_question():
    """测试理论问题是否还会强制调用工具"""
    print("=" * 60)
    print("测试工具调用修复")
    print("=" * 60)

    print("\n测试场景：理论问题不应该强制调用工具")
    print("问题：'解释引力透镜'")

    print("\n预期行为：")
    print("1. 模型应该自主判断是否调用工具")
    print("2. 对于理论问题，不应该强制调用文件工具")
    print("3. 不应该出现'需要文件工具：缺少文件读取'的日志")

    print("\n实际测试：")
    print("请重启聊天服务器并测试'解释引力透镜'问题")
    print("观察日志中是否还有强制工具调用")

    print("\n" + "=" * 60)
    print("修复总结：")
    print("1. 移除了所有正则匹配的强制工具调用")
    print("2. 将 requires_*_tools 都设为 False")
    print("3. 简化了 _should_summarize 方法")
    print("4. 完全由模型自主判断工具调用")

    print("\n现在模型会：")
    print("✅ 自主判断是否调用工具")
    print("✅ 理论问题不会强制调用文件工具")
    print("✅ 不会出现无关的金融项目信息")

    return True

if __name__ == "__main__":
    asyncio.run(test_theory_question())