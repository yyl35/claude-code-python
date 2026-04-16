#!/usr/bin/env python3
"""
简单测试记忆功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.memory.manager import MemoryManager

async def test_memory_basic():
    """测试基本记忆功能"""

    print("测试基本记忆功能...")

    # 创建记忆管理器
    memory_manager = MemoryManager(memory_dir="chat_memory", project_root=str(project_root))
    await memory_manager.initialize()

    # 创建新会话
    session_id = memory_manager.create_session("test_simple_session")
    print(f"创建会话: {session_id}")

    # 添加对话
    print("\n1. 添加对话:")
    conversations = [
        ("user", "解释一下黑洞"),
        ("bot", "黑洞是宇宙中一种密度极大、引力极强的天体..."),
        ("user", "写个计算因子IC的代码，模拟一下假数据测试"),
        ("bot", "我已经成功为您编写并运行了计算因子IC的代码..."),
    ]

    for role, content in conversations:
        await memory_manager.add_message(session_id, role, content)
        print(f"  添加: {role} - {content[:50]}...")

    # 等待保存
    await asyncio.sleep(1)

    # 测试增强消息
    print("\n2. 测试增强消息:")
    test_message = "你刚才帮我实际运行过吗"
    enhanced = memory_manager.get_enhanced_message(session_id, test_message)

    print(f"   原始消息: {test_message}")
    print(f"   增强消息长度: {len(enhanced)}")
    print(f"   增强消息预览:\n{enhanced[:500]}...")

    # 分析增强消息
    print("\n3. 增强消息分析:")
    if "黑洞" in enhanced:
        print("   [OK] 包含'黑洞'主题")
    else:
        print("   [NO] 未包含'黑洞'主题")

    if "因子IC" in enhanced or "IC" in enhanced:
        print("   [OK] 包含'因子IC'主题")
    else:
        print("   [NO] 未包含'因子IC'主题")

    if "刚才" in enhanced or "之前" in enhanced:
        print("   [OK] 包含指代词解析")
    else:
        print("   [NO] 未包含指代词解析")

    # 检查会话状态
    print("\n4. 会话状态:")
    session_memory = memory_manager.sessions.get(session_id)
    if session_memory:
        print(f"   消息总数: {session_memory.message_count}")
        print(f"   原始消息数: {len(session_memory.raw_messages)}")
        print(f"   摘要数: {len(session_memory.summaries)}")
        print(f"   实体数: {len(session_memory.entities)}")

        if session_memory.summaries:
            print(f"   最新摘要: {session_memory.summaries[-1].summary}")
        else:
            print("   尚未生成摘要")

    # 测试压缩
    print("\n5. 压缩测试:")
    from src.memory.compressor import MemoryCompressor
    compressor = MemoryCompressor()
    should_compress = compressor.should_compress(session_memory)
    print(f"   是否应该压缩: {should_compress}")

    if should_compress:
        summary = compressor.compress_conversation(session_memory)
        if summary:
            print(f"   生成的摘要: {summary.summary}")
            print(f"   关键实体: {summary.key_entities}")

    print("\n测试完成!")

async def test_smart_compressor_integration():
    """测试智能压缩器集成"""

    print("\n" + "="*80)
    print("测试智能压缩器集成")
    print("="*80)

    # 创建LLM实例
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(
        api_key="sk-88b906f7af2d4681aac5451a954360d9",
        base_url="https://api.deepseek.com/v1",
        model_name="deepseek-chat",
        temperature=0.1
    )

    # 创建带LLM的记忆管理器
    memory_manager = MemoryManager(
        memory_dir="chat_memory",
        project_root=str(project_root),
        llm=llm
    )
    await memory_manager.initialize()

    # 创建新会话
    session_id = memory_manager.create_session("test_smart_session")
    print(f"创建智能会话: {session_id}")

    # 添加对话
    conversations = [
        ("user", "什么是机器学习"),
        ("bot", "机器学习是人工智能的一个分支，它使计算机能够从数据中学习并做出预测或决策，而无需明确编程。"),
        ("user", "写一个简单的线性回归Python代码"),
        ("bot", "这是一个简单的线性回归Python代码示例，使用scikit-learn库..."),
    ]

    for role, content in conversations:
        await memory_manager.add_message(session_id, role, content)

    # 等待保存和可能的压缩
    await asyncio.sleep(2)

    # 检查是否生成了智能摘要
    session_memory = memory_manager.sessions.get(session_id)
    if session_memory and session_memory.summaries:
        print(f"\n生成的摘要: {session_memory.summaries[-1].summary}")
        print(f"摘要质量: {'好' if len(session_memory.summaries[-1].summary) > 20 else '一般'}")
    else:
        print("\n未生成摘要或摘要太短")

    print("\n智能压缩器集成测试完成!")

if __name__ == "__main__":
    print("开始测试记忆功能...")

    # 测试基本功能
    asyncio.run(test_memory_basic())

    # 测试智能压缩器集成
    try:
        asyncio.run(test_smart_compressor_integration())
    except Exception as e:
        print(f"智能压缩器测试失败: {e}")
        print("继续使用简单压缩器...")