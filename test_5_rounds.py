#!/usr/bin/env python3
"""
测试5轮对话：验证模型是否收到完整历史
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.memory.manager import MemoryManager


async def test_5_rounds():
    """测试5轮对话"""
    print("=" * 60)
    print("测试5轮对话：验证模型是否收到完整历史")
    print("=" * 60)

    # 创建记忆管理器
    memory_dir = project_root / "chat_memory_test_5"
    memory_dir.mkdir(exist_ok=True)

    print(f"使用测试记忆目录: {memory_dir}")

    # 清理之前的测试文件
    for file in memory_dir.glob("*.json"):
        file.unlink()

    # 创建记忆管理器
    memory_manager = MemoryManager(str(memory_dir))
    await memory_manager.initialize()

    # 创建测试会话
    session_id = "test_5_rounds_session"
    memory_manager.create_session(session_id)

    print(f"\n创建测试会话: {session_id}")

    # 进行5轮对话
    conversations = [
        ("第一轮：什么是Python？", "Python是一种高级编程语言..."),
        ("第二轮：Python有什么特点？", "Python有简洁易读、跨平台等特点..."),
        ("第三轮：Python适合做什么？", "Python适合Web开发、数据分析、AI等..."),
        ("第四轮：如何学习Python？", "可以通过官方文档、在线课程学习..."),
        ("第五轮：刚才说的Python特点能再详细点吗？", "")
    ]

    for i, (user_msg, bot_msg) in enumerate(conversations):
        print(f"\n" + "-" * 60)
        print(f"第{i+1}轮对话")
        print("-" * 60)

        print(f"用户消息: {user_msg}")

        # 添加用户消息
        await memory_manager.add_message(session_id, "user", user_msg)

        # 获取增强后的消息
        enhanced = await memory_manager.get_enhanced_message(session_id, user_msg)

        # 检查增强消息
        print(f"\n增强消息分析（第{i+1}轮）:")

        # 检查是否包含历史
        if "最近的对话历史" in enhanced:
            # 提取历史部分
            lines = enhanced.split('\n')
            history_start = -1
            for idx, line in enumerate(lines):
                if "最近的对话历史" in line:
                    history_start = idx
                    break

            if history_start >= 0:
                print(f"  包含对话历史: YES")
                # 显示历史内容
                history_lines = []
                for line in lines[history_start+1:]:
                    if line.strip() and not line.startswith("【"):
                        history_lines.append(line)
                    else:
                        break

                print(f"  历史消息数: {len(history_lines)}")
                print(f"  历史内容预览:")
                for line in history_lines[:3]:  # 只显示前3行
                    print(f"    {line}")
                if len(history_lines) > 3:
                    print(f"    ...（还有{len(history_lines)-3}条）")
            else:
                print(f"  包含对话历史: NO（格式异常）")
        else:
            print(f"  包含对话历史: NO")

        # 检查是否包含摘要
        has_summary = "对话摘要" in enhanced
        print(f"  包含对话摘要: {'YES' if has_summary else 'NO'}")

        # 模拟模型回复（除了最后一轮）
        if bot_msg:
            print(f"\n模型回复: {bot_msg[:50]}...")
            await memory_manager.add_message(session_id, "bot", bot_msg)

    # 检查最终状态
    session = memory_manager.sessions[session_id]
    print(f"\n" + "=" * 60)
    print(f"最终状态:")
    print(f"  总消息数: {session.message_count}")
    print(f"  原始消息数: {len(session.raw_messages)}")
    print(f"  摘要数: {len(session.summaries)}")

    print(f"\n所有原始消息:")
    for i, msg in enumerate(session.raw_messages):
        role = "用户" if msg.get('role') == 'user' else "助手"
        content = msg.get('content', '')
        preview = content[:40] + ('...' if len(content) > 40 else '')
        print(f"  {i+1}. {role}: {preview}")

    # 清理
    for file in memory_dir.glob("*.json"):
        file.unlink()
    memory_dir.rmdir()

    print(f"\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_5_rounds())