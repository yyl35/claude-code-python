#!/usr/bin/env python3
"""
测试智能压缩器
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from langchain_openai import ChatOpenAI
from src.memory.smart_compressor import SmartMemoryCompressor
from src.memory.types import SessionMemory, Entity

async def test_smart_compressor():
    """测试智能压缩器"""

    # 创建LLM实例
    llm = ChatOpenAI(
        api_key="sk-88b906f7af2d4681aac5451a954360d9",  # 使用.env文件中的密钥
        base_url="https://api.deepseek.com/v1",
        model_name="deepseek-chat",
        temperature=0.1
    )

    # 创建智能压缩器
    compressor = SmartMemoryCompressor(llm)

    # 创建测试会话记忆
    session_memory = SessionMemory(
        session_id="test_smart_session",
        created_at=datetime.now(),
        last_activity=datetime.now(),
        message_count=0,
        metadata={}
    )

    # 添加测试对话（模拟之前的对话）
    test_conversation = [
        {"role": "user", "content": "解释一下黑洞", "timestamp": "2026-04-13T15:52:29.326418", "message_id": 0},
        {"role": "bot", "content": "黑洞是宇宙中一种密度极大、引力极强的天体，其引力场如此强大，以至于连光都无法逃脱它的引力束缚。黑洞的边界称为'事件视界'，一旦物质或信息越过这个边界，就永远无法返回。", "timestamp": "2026-04-13T15:54:18.162908", "message_id": 1},
        {"role": "user", "content": "写个计算因子IC的代码，模拟一下假数据测试", "timestamp": "2026-04-13T16:01:37.814491", "message_id": 2},
        {"role": "bot", "content": "我已经成功为您编写并运行了计算因子IC的代码。代码包含数据模拟、IC计算、统计分析和可视化功能。测试结果显示价值因子表现最佳，平均IC=0.31，信息比率3.68。", "timestamp": "2026-04-13T16:04:48.521941", "message_id": 3},
    ]

    session_memory.raw_messages = test_conversation
    session_memory.message_count = len(test_conversation)

    # 添加一些测试实体
    entities = [
        Entity(
            id="entity_1",
            type="stock",
            name="600519",
            aliases=["600519.sh"],
            metadata={"source": "test"},
            created_at=datetime.now(),
            last_referenced=datetime.now(),
            reference_count=3
        ),
        Entity(
            id="entity_2",
            type="file",
            name="factor_ic_calculator.py",
            aliases=["ic_calculator.py"],
            metadata={"source": "test"},
            created_at=datetime.now(),
            last_referenced=datetime.now(),
            reference_count=2
        )
    ]

    for entity in entities:
        session_memory.entities[entity.id] = entity

    print("=" * 80)
    print("测试智能压缩器")
    print("=" * 80)

    # 测试压缩对话
    print("\n1. 测试对话压缩和摘要生成:")
    summary = await compressor.compress_conversation(session_memory)
    if summary:
        print(f"   生成的摘要: {summary.summary}")
        print(f"   关键实体: {summary.key_entities}")
        print(f"   消息数量: {summary.message_count}")
    else:
        print("   未生成摘要（可能消息太少）")

    # 测试上下文增强
    print("\n2. 测试上下文增强:")
    test_message = "你刚才帮我实际运行过吗"
    enhanced_message = await compressor.enhance_message_with_context(test_message, session_memory)

    print(f"   原始消息: {test_message}")
    print(f"   增强后的消息长度: {len(enhanced_message)}")
    print(f"   增强消息预览:\n{enhanced_message[:500]}...")

    # 分析增强消息的内容
    print("\n3. 增强消息内容分析:")
    lines = enhanced_message.split('\n')
    for i, line in enumerate(lines[:20]):  # 只显示前20行
        if line.strip():
            print(f"   {i:3d}: {line[:100]}{'...' if len(line) > 100 else ''}")

    # 测试是否应该压缩
    print("\n4. 压缩检查:")
    should_compress = compressor.should_compress(session_memory)
    print(f"   是否应该压缩: {should_compress}")
    print(f"   当前消息数: {len(session_memory.raw_messages)}")

    # 测试格式化压缩上下文
    print("\n5. 格式化压缩上下文:")
    compressed_context = compressor.format_compressed_context(session_memory, char_budget=300)
    print(f"   压缩上下文长度: {len(compressed_context)}")
    print(f"   压缩上下文内容:\n{compressed_context}")

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)

async def test_without_llm():
    """测试没有LLM的情况"""
    print("\n" + "=" * 80)
    print("测试没有LLM的情况（回退到简单压缩器）")
    print("=" * 80)

    # 创建没有LLM的智能压缩器
    compressor = SmartMemoryCompressor(llm=None)

    # 创建测试会话记忆
    session_memory = SessionMemory(
        session_id="test_simple_session",
        created_at=datetime.now(),
        last_activity=datetime.now(),
        message_count=0,
        metadata={}
    )

    # 添加测试对话
    test_conversation = [
        {"role": "user", "content": "读取/etc/hosts文件", "timestamp": "2026-04-13T10:00:00.000000", "message_id": 0},
        {"role": "bot", "content": "已读取/etc/hosts文件，文件内容包含本地主机配置。", "timestamp": "2026-04-13T10:01:00.000000", "message_id": 1},
    ]

    session_memory.raw_messages = test_conversation
    session_memory.message_count = len(test_conversation)

    # 测试压缩对话
    summary = await compressor.compress_conversation(session_memory)
    if summary:
        print(f"   生成的摘要: {summary.summary}")
    else:
        print("   未生成摘要")

    # 测试上下文增强
    test_message = "刚才读取的文件内容是什么"
    enhanced_message = await compressor.enhance_message_with_context(test_message, session_memory)
    print(f"\n   增强消息预览:\n{enhanced_message[:300]}...")

if __name__ == "__main__":
    print("开始测试智能压缩器...")

    # 测试有LLM的情况
    try:
        asyncio.run(test_smart_compressor())
    except Exception as e:
        print(f"智能压缩器测试失败: {e}")
        print("可能原因: API密钥无效或网络连接问题")
        print("将测试回退到简单压缩器...")

    # 测试没有LLM的情况
    asyncio.run(test_without_llm())