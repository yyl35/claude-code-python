#!/usr/bin/env python3
"""
测试记忆功能，查看模型实际收到的消息
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.memory.manager import MemoryManager
from src.memory.compressor import MemoryCompressor
from src.memory.types import SessionMemory
from datetime import datetime

async def test_memory_enhancement():
    """测试记忆增强功能"""

    # 创建记忆管理器
    memory_manager = MemoryManager(memory_dir="chat_memory", project_root=str(project_root))
    await memory_manager.initialize()

    # 创建新会话
    session_id = memory_manager.create_session("test_session_debug")
    print(f"创建测试会话: {session_id}")

    # 添加一些测试消息（模拟之前的对话）
    test_messages = [
        ("user", "解释一下黑洞"),
        ("bot", "黑洞是宇宙中一种密度极大、引力极强的天体..."),
        ("user", "写个计算因子IC的代码，模拟一下假数据测试"),
        ("bot", "我已经成功为您编写并运行了计算因子IC的代码..."),
    ]

    for role, content in test_messages:
        await memory_manager.add_message(session_id, role, content)

    # 等待保存完成
    await asyncio.sleep(1)

    # 测试增强消息
    test_user_message = "你刚才帮我实际运行过吗"
    print(f"\n测试用户消息: {test_user_message}")

    enhanced_message = memory_manager.get_enhanced_message(session_id, test_user_message)

    print("\n" + "="*80)
    print("【调试】模型实际收到的消息内容：")
    print(enhanced_message)
    print("="*80)

    # 分析增强消息的内容
    print("\n【分析】增强消息包含以下部分：")
    lines = enhanced_message.split('\n')
    for i, line in enumerate(lines):
        if line.strip():
            print(f"  {i:3d}: {line[:100]}{'...' if len(line) > 100 else ''}")

    # 检查会话状态
    session_memory = memory_manager.sessions.get(session_id)
    if session_memory:
        print(f"\n【会话状态】")
        print(f"  消息总数: {session_memory.message_count}")
        print(f"  原始消息数: {len(session_memory.raw_messages)}")
        print(f"  摘要数: {len(session_memory.summaries)}")
        print(f"  实体数: {len(session_memory.entities)}")

        if session_memory.summaries:
            print(f"\n【摘要内容】")
            for i, summary in enumerate(session_memory.summaries):
                print(f"  摘要{i+1}: {summary.summary}")

    # 测试压缩器
    print("\n【压缩器测试】")
    compressor = MemoryCompressor()

    # 检查是否应该压缩
    should_compress = compressor.should_compress(session_memory)
    print(f"  是否应该压缩: {should_compress}")

    # 生成摘要
    if should_compress:
        summary = compressor.compress_conversation(session_memory)
        if summary:
            print(f"  生成的摘要: {summary.summary}")

    # 测试实体解析
    print("\n【实体解析测试】")
    resolved = compressor._resolve_entities_in_message(test_user_message, session_memory)
    print(f"  实体解析结果: {resolved}")

    # 测试指代解析
    print("\n【指代解析测试】")
    referenced_entity = compressor._resolve_reference_from_session(test_user_message, session_memory)
    if referenced_entity:
        print(f"  指代实体: {referenced_entity.type}: {referenced_entity.name}")
    else:
        print(f"  未找到指代实体")

async def test_compressor_direct():
    """直接测试压缩器"""
    print("\n" + "="*80)
    print("直接测试压缩器")
    print("="*80)

    # 创建测试会话记忆
    session_memory = SessionMemory(
        session_id="test_direct",
        created_at=datetime.now(),
        last_activity=datetime.now(),
        message_count=0,
        metadata={}
    )

    # 添加测试消息
    test_conversation = [
        {"role": "user", "content": "解释一下黑洞", "timestamp": "2026-04-13T15:52:29.326418", "message_id": 0},
        {"role": "bot", "content": "黑洞是宇宙中一种密度极大、引力极强的天体...", "timestamp": "2026-04-13T15:54:18.162908", "message_id": 1},
        {"role": "user", "content": "写个计算因子IC的代码，模拟一下假数据测试", "timestamp": "2026-04-13T16:01:37.814491", "message_id": 2},
        {"role": "bot", "content": "我已经成功为您编写并运行了计算因子IC的代码...", "timestamp": "2026-04-13T16:04:48.521941", "message_id": 3},
    ]

    session_memory.raw_messages = test_conversation
    session_memory.message_count = len(test_conversation)

    # 测试压缩器
    compressor = MemoryCompressor()

    # 提取主题
    topics = compressor._extract_topics(test_conversation)
    print(f"提取的主题: {topics}")

    # 提取动作
    actions = compressor._extract_actions(test_conversation)
    print(f"提取的动作: {actions}")

    # 生成摘要
    summary_text = compressor._generate_summary(topics, actions, [])
    print(f"生成的摘要: {summary_text}")

    # 测试增强消息
    user_message = "你刚才帮我实际运行过吗"
    enhanced = compressor.enhance_message_with_context(user_message, session_memory)

    print(f"\n用户消息: {user_message}")
    print(f"增强后的消息长度: {len(enhanced)}")
    print(f"增强消息预览:\n{enhanced[:500]}...")

if __name__ == "__main__":
    print("测试记忆功能...")
    asyncio.run(test_memory_enhancement())
    asyncio.run(test_compressor_direct())