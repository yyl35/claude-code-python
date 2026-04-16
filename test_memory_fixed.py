#!/usr/bin/env python3
"""
测试修复后的记忆系统：验证实体抽取已禁用，摘要生成正常
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.memory.manager import MemoryManager


async def test_fixed_memory():
    """测试修复后的记忆系统"""
    print("=" * 60)
    print("测试修复后的记忆系统")
    print("=" * 60)

    # 创建记忆管理器
    memory_dir = project_root / "chat_memory_test_fixed"
    memory_dir.mkdir(exist_ok=True)

    print(f"使用测试记忆目录: {memory_dir}")

    # 清理之前的测试文件
    for file in memory_dir.glob("*.json"):
        file.unlink()

    # 创建记忆管理器
    memory_manager = MemoryManager(str(memory_dir))
    await memory_manager.initialize()

    # 创建测试会话
    session_id = "test_fixed_session"
    memory_manager.create_session(session_id)

    print(f"\n创建测试会话: {session_id}")

    # 模拟你的实际对话
    conversations = [
        ("user", "解释黑洞"),
        ("bot", "黑洞是宇宙中一种极其致密的天体..."),
        ("user", "查看linux的硬盘占用的命令是什么"),
        ("bot", "df -h 命令可以查看硬盘使用情况..."),
        ("user", "测试记忆，我刚才问了你哪些问题"),
        ("bot", "您刚才问了黑洞解释和Linux命令..."),
        ("user", "解释引力透镜"),
        ("bot", "引力透镜是爱因斯坦广义相对论预言的一种天文现象..."),
        ("user", "我问你解释引力透镜 为什么告诉我金融量化分析项目"),
        ("bot", "抱歉，我不应该提及无关的金融项目..."),
    ]

    print(f"\n模拟对话过程:")
    for i, (role, content) in enumerate(conversations):
        print(f"  {i+1}. {role}: {content[:30]}...")
        await memory_manager.add_message(session_id, role, content)

        # 每添加2条消息检查一次状态
        if (i + 1) % 2 == 0:
            session = memory_manager.sessions[session_id]
            print(f"    当前: 消息数={session.message_count}, 实体数={len(session.entities)}, 摘要数={len(session.summaries)}")

    # 检查最终状态
    session = memory_manager.sessions[session_id]
    print(f"\n" + "=" * 60)
    print(f"最终状态:")
    print(f"  总消息数: {session.message_count}")
    print(f"  实体数: {len(session.entities)} (应该为0)")
    print(f"  摘要数: {len(session.summaries)}")

    # 检查实体
    if session.entities:
        print(f"\n⚠️ 警告: 仍然有实体被抽取:")
        for entity_id, entity in session.entities.items():
            print(f"  - {entity.type}: {entity.name}")
    else:
        print(f"\n[SUCCESS] 实体抽取已禁用")

    # 检查摘要
    if session.summaries:
        print(f"\n生成的摘要:")
        for i, summary in enumerate(session.summaries):
            print(f"  摘要 {i+1}: {summary.summary}")
            print(f"    关键实体: {summary.key_entities} (应该为空)")
            print(f"    消息数: {summary.message_count}")

            # 检查摘要是否包含无关信息
            if "金融" in summary.summary or "量化" in summary.summary:
                print(f"    [WARNING] 摘要包含无关的金融信息")
            else:
                print(f"    [SUCCESS] 摘要内容正常")
    else:
        print(f"\n⚠️ 未生成摘要")

    # 测试增强消息
    print(f"\n" + "=" * 60)
    print(f"测试增强消息:")

    test_messages = [
        "刚才说的黑洞是怎么形成的？",
        "df命令的具体用法是什么？",
        "我第一个问题是什么？"
    ]

    for i, test_msg in enumerate(test_messages):
        print(f"\n测试消息 {i+1}: {test_msg}")
        enhanced = await memory_manager.get_enhanced_message(session_id, test_msg)

        # 检查增强消息
        has_history = "最近的对话历史" in enhanced
        has_entity = "实体解析" in enhanced
        has_summary = "对话摘要" in enhanced

        print(f"  包含对话历史: {'YES' if has_history else 'NO'}")
        print(f"  包含实体解析: {'YES' if has_entity else 'NO'} (应该为NO)")
        print(f"  包含对话摘要: {'YES' if has_summary else 'NO'}")

        if has_entity:
            print(f"  [WARNING] 增强消息仍然包含实体解析")

        # 检查是否包含无关信息
        if "金融" in enhanced or "量化" in enhanced or "最大回撤" in enhanced:
            print(f"  [WARNING] 增强消息包含无关的金融信息")
        else:
            print(f"  [SUCCESS] 增强消息内容正常")

    # 保存并检查文件
    session_file = memory_dir / f"session_{session_id}.json"
    conv_file = memory_dir / f"conversation_{session_id}.json"

    print(f"\n" + "=" * 60)
    print(f"文件保存状态:")
    print(f"  会话文件: {session_file} - {'存在' if session_file.exists() else '不存在'}")
    print(f"  对话文件: {conv_file} - {'存在' if conv_file.exists() else '不存在'}")

    if session_file.exists():
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
            print(f"  会话实体数: {len(session_data.get('entities', {}))} (应该为0)")
            print(f"  会话摘要数: {len(session_data.get('summaries', []))}")

            # 检查摘要内容
            for summary in session_data.get('summaries', []):
                if "金融" in summary.get('summary', '') or "量化" in summary.get('summary', ''):
                    print(f"  [WARNING] 保存的摘要包含无关信息: {summary.get('summary', '')[:50]}...")

    # 清理
    for file in memory_dir.glob("*.json"):
        file.unlink()
    memory_dir.rmdir()

    print(f"\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_fixed_memory())