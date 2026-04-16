#!/usr/bin/env python3
"""
测试摘要保存功能
"""

import asyncio
import sys
from pathlib import Path
import json

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.memory.manager import MemoryManager
from langchain_openai import ChatOpenAI

async def test_summary_saving():
    """测试摘要保存功能"""

    print("=" * 80)
    print("测试摘要保存功能")
    print("=" * 80)

    try:
        # 创建LLM实例
        llm = ChatOpenAI(
            api_key="sk-88b906f7af2d4681aac5451a954360d9",
            base_url="https://api.deepseek.com/v1",
            model_name="deepseek-chat",
            temperature=0.1
        )

        # 创建记忆管理器
        memory_manager = MemoryManager(
            memory_dir="chat_memory_test_summary",
            project_root=str(project_root),
            llm=llm
        )
        await memory_manager.initialize()

        # 创建新会话
        session_id = memory_manager.create_session("test_summary_save")
        print(f"创建会话: {session_id}")

        # 添加足够多的消息以触发压缩
        print("\n1. 添加测试对话（触发压缩）:")

        test_conversations = [
            ("user", "什么是机器学习"),
            ("bot", "机器学习是人工智能的一个分支，它使计算机能够从数据中学习并做出预测或决策，而无需明确编程。"),
            ("user", "机器学习有哪些主要类型？"),
            ("bot", "机器学习主要有三种类型：监督学习、无监督学习和强化学习。"),
            ("user", "监督学习的具体例子有哪些？"),
            ("bot", "监督学习的例子包括分类问题（如垃圾邮件检测）和回归问题（如房价预测）。"),
        ]

        for i, (role, content) in enumerate(test_conversations):
            await memory_manager.add_message(session_id, role, content)
            print(f"  添加消息 {i+1}: {role} - {content[:50]}...")

        # 等待保存完成
        print("\n2. 等待保存完成...")
        await asyncio.sleep(3)

        # 检查会话状态
        print("\n3. 检查会话状态:")
        session_memory = memory_manager.sessions.get(session_id)
        if session_memory:
            print(f"   消息总数: {session_memory.message_count}")
            print(f"   原始消息数: {len(session_memory.raw_messages)}")
            print(f"   摘要数: {len(session_memory.summaries)}")

            if session_memory.summaries:
                print(f"\n4. 生成的摘要:")
                for i, summary in enumerate(session_memory.summaries):
                    print(f"   摘要{i+1}: {summary.summary}")
                    print(f"     时间戳: {summary.timestamp}")
                    print(f"     关键实体: {summary.key_entities}")
                    print(f"     消息数量: {summary.message_count}")
            else:
                print("\n4. 未生成摘要")
                print("   可能原因:")
                print("   - 消息数量不足（需要至少3条消息）")
                print("   - 压缩阈值未达到")
                print("   - 压缩器返回了None")

        # 检查文件是否保存
        print("\n5. 检查文件保存:")
        session_file = Path("chat_memory_test_summary") / f"session_{session_id}.json"
        if session_file.exists():
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            if "summaries" in session_data and session_data["summaries"]:
                print(f"   ✓ 摘要已保存到文件")
                print(f"   文件中的摘要数量: {len(session_data['summaries'])}")
                for i, summary in enumerate(session_data["summaries"]):
                    print(f"   摘要{i+1}: {summary['summary'][:100]}...")
            else:
                print(f"   ✗ 文件中未找到摘要")
                print(f"   文件内容摘要键: {list(session_data.keys())}")
        else:
            print(f"   ✗ 会话文件不存在: {session_file}")

        # 测试简单压缩器（没有LLM）
        print("\n" + "="*80)
        print("测试简单压缩器（没有LLM）")
        print("="*80)

        memory_manager_simple = MemoryManager(
            memory_dir="chat_memory_test_simple",
            project_root=str(project_root),
            llm=None  # 没有LLM
        )
        await memory_manager_simple.initialize()

        session_id_simple = memory_manager_simple.create_session("test_simple_summary")

        # 添加测试对话
        simple_conversations = [
            ("user", "读取文件"),
            ("bot", "已读取文件"),
            ("user", "修改文件"),
            ("bot", "已修改文件"),
            ("user", "删除文件"),
            ("bot", "已删除文件"),
        ]

        for i, (role, content) in enumerate(simple_conversations):
            await memory_manager_simple.add_message(session_id_simple, role, content)

        # 等待保存
        await asyncio.sleep(2)

        # 检查简单压缩器的摘要
        session_memory_simple = memory_manager_simple.sessions.get(session_id_simple)
        if session_memory_simple and session_memory_simple.summaries:
            print(f"   简单压缩器生成的摘要: {session_memory_simple.summaries[-1].summary}")
        else:
            print("   简单压缩器未生成摘要")

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*80)
    print("测试完成!")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_summary_saving())