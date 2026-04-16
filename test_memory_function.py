#!/usr/bin/env python3
"""
测试记忆功能：验证两轮对话中模型是否能收到历史消息
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.memory.manager import MemoryManager
from src.memory.compressor import MemoryCompressor


async def test_memory_function():
    """测试记忆功能"""
    print("=" * 60)
    print("测试记忆功能：验证两轮对话中的历史消息传递")
    print("=" * 60)

    # 创建记忆管理器
    memory_dir = project_root / "chat_memory_test"
    memory_dir.mkdir(exist_ok=True)

    print(f"使用测试记忆目录: {memory_dir}")

    # 清理之前的测试文件
    for file in memory_dir.glob("*.json"):
        file.unlink()

    # 创建记忆管理器
    memory_manager = MemoryManager(str(memory_dir))
    await memory_manager.initialize()

    # 创建测试会话
    session_id = "test_session_123"
    memory_manager.create_session(session_id)

    print(f"\n创建测试会话: {session_id}")

    # 第一轮对话
    print("\n" + "-" * 60)
    print("第一轮对话")
    print("-" * 60)

    user_message_1 = "解释黑洞是什么"
    print(f"用户消息1: {user_message_1}")

    # 添加用户消息
    await memory_manager.add_message(session_id, "user", user_message_1)

    # 获取增强后的消息（模拟模型接收）
    enhanced_message_1 = await memory_manager.get_enhanced_message(session_id, user_message_1)
    print(f"\n增强后的消息1（发送给模型）:")
    print("-" * 40)
    print(enhanced_message_1)
    print("-" * 40)

    # 模拟模型回复
    bot_response_1 = "黑洞是宇宙中一种极其致密的天体，其引力场如此之强，以至于连光都无法逃脱。"
    print(f"\n模型回复1: {bot_response_1}")
    await memory_manager.add_message(session_id, "bot", bot_response_1)

    # 检查当前状态
    session = memory_manager.sessions[session_id]
    print(f"\n第一轮后状态:")
    print(f"  消息总数: {session.message_count}")
    print(f"  原始消息数: {len(session.raw_messages)}")
    print(f"  摘要数: {len(session.summaries)}")

    # 第二轮对话
    print("\n" + "-" * 60)
    print("第二轮对话")
    print("-" * 60)

    user_message_2 = "刚才说的黑洞是怎么形成的？"
    print(f"用户消息2: {user_message_2}")

    # 添加用户消息
    await memory_manager.add_message(session_id, "user", user_message_2)

    # 获取增强后的消息（检查是否包含历史）
    enhanced_message_2 = await memory_manager.get_enhanced_message(session_id, user_message_2)
    print(f"\n增强后的消息2（发送给模型）:")
    print("-" * 40)
    print(enhanced_message_2)
    print("-" * 40)

    # 检查增强消息中是否包含历史
    has_history = "最近的对话历史" in enhanced_message_2
    has_entity_resolution = "实体解析" in enhanced_message_2
    has_summary = "对话摘要" in enhanced_message_2

    print(f"\n增强消息分析:")
    print(f"  包含对话历史: {'YES' if has_history else 'NO'}")
    print(f"  包含实体解析: {'YES' if has_entity_resolution else 'NO'}")
    print(f"  包含对话摘要: {'YES' if has_summary else 'NO'}")

    # 检查原始消息是否保存
    print(f"\n会话原始消息:")
    for i, msg in enumerate(session.raw_messages):
        role = msg.get('role', 'unknown')
        content_preview = msg.get('content', '')[:50] + ('...' if len(msg.get('content', '')) > 50 else '')
        print(f"  {i+1}. {role}: {content_preview}")

    # 检查文件是否保存
    session_file = memory_dir / f"session_{session_id}.json"
    conv_file = memory_dir / f"conversation_{session_id}.json"

    print(f"\n文件保存状态:")
    print(f"  会话文件: {session_file} - {'存在' if session_file.exists() else '不存在'}")
    print(f"  对话文件: {conv_file} - {'存在' if conv_file.exists() else '不存在'}")

    if session_file.exists():
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
            print(f"  会话摘要数: {len(session_data.get('summaries', []))}")

    # 测试摘要生成（模拟更多消息）
    print("\n" + "-" * 60)
    print("测试摘要生成（模拟10条消息）")
    print("-" * 60)

    # 添加更多消息以达到摘要生成阈值
    for i in range(8):  # 已经2条，再加8条达到10条
        user_msg = f"测试消息 {i+1}"
        bot_msg = f"测试回复 {i+1}"
        await memory_manager.add_message(session_id, "user", user_msg)
        await memory_manager.add_message(session_id, "bot", bot_msg)

    # 检查是否生成了摘要
    session = memory_manager.sessions[session_id]
    print(f"消息总数: {session.message_count}")
    print(f"原始消息数: {len(session.raw_messages)}")
    print(f"摘要数: {len(session.summaries)}")

    if session.summaries:
        print(f"\n生成的摘要:")
        for i, summary in enumerate(session.summaries):
            print(f"  摘要 {i+1}: {summary.summary}")
            print(f"    关键实体: {summary.key_entities}")
            print(f"    消息数: {summary.message_count}")
    else:
        print("\n⚠️ 未生成摘要（可能阈值设置问题）")

    # 清理测试文件
    print(f"\n清理测试文件...")
    for file in memory_dir.glob("*.json"):
        file.unlink()
    memory_dir.rmdir()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

    return {
        "has_history": has_history,
        "has_entity_resolution": has_entity_resolution,
        "has_summary": has_summary,
        "total_messages": session.message_count,
        "summary_count": len(session.summaries)
    }


if __name__ == "__main__":
    result = asyncio.run(test_memory_function())

    print(f"\n测试结果总结:")
    print(f"  模型是否能收到历史消息: {'YES' if result['has_history'] else 'NO'}")
    print(f"  实体解析功能: {'YES' if result['has_entity_resolution'] else 'NO'}")
    print(f"  摘要生成: {result['summary_count']} 个摘要")

    if not result['has_history']:
        print("\n[WARNING] 模型可能无法收到完整的历史消息！")
        print("可能的原因:")
        print("  1. 压缩器未正确配置")
        print("  2. 增强消息功能未启用")
        print("  3. 消息数量未达到阈值")
    else:
        print("\n[SUCCESS] 记忆功能正常：模型可以收到历史消息")