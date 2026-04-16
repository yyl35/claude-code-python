#!/usr/bin/env python3
"""
测试记忆系统功能
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.memory.manager import MemoryManager
from src.config import config


async def test_memory_system():
    """测试记忆系统"""
    print("=" * 60)
    print("测试记忆系统")
    print("=" * 60)

    # 创建记忆管理器
    memory_dir = "test_memory"
    memory_manager = MemoryManager(memory_dir=memory_dir, project_root=str(project_root))

    # 初始化
    print("\n1. 初始化记忆管理器...")
    success = await memory_manager.initialize()
    if not success:
        print("[ERROR] 初始化失败")
        return

    print("[OK] 初始化成功")
    print(f"   已加载会话数: {len(memory_manager.sessions)}")

    # 创建测试会话
    print("\n2. 创建测试会话...")
    session_id = "test_session_123"
    memory_manager.create_session(session_id)
    print(f"[OK] 创建会话: {session_id}")

    # 添加测试消息
    print("\n3. 添加测试消息...")
    test_messages = [
        ("user", "查一下600519.sh的股票价格"),
        ("bot", "贵州茅台(600519.sh)当前价格: 1680.50元"),
        ("user", "读取/etc/hosts文件"),
        ("bot", "已读取/etc/hosts文件，包含127.0.0.1 localhost"),
    ]

    for role, content in test_messages:
        await memory_manager.add_message(session_id, role, content)
        print(f"   [OK] 添加消息: {role} - {content[:30]}...")

    # 等待异步保存完成
    await asyncio.sleep(1)

    # 获取历史记录
    print("\n4. 获取历史记录...")
    history = memory_manager.get_session_history(session_id)
    print(f"[OK] 获取到 {len(history)} 条历史记录")
    for i, msg in enumerate(history, 1):
        print(f"   {i}. {msg['sender']}: {msg['text'][:40]}...")

    # 测试会话恢复
    print("\n5. 测试会话恢复...")

    # 模拟重新初始化（如服务器重启）
    print("   重新初始化记忆管理器...")
    memory_manager2 = MemoryManager(memory_dir=memory_dir, project_root=str(project_root))
    await memory_manager2.initialize()

    # 检查是否能恢复会话
    if session_id in memory_manager2.sessions:
        session = memory_manager2.sessions[session_id]
        print(f"[OK] 成功恢复会话: {session_id}")
        print(f"   消息数: {session.message_count}")
        print(f"   原始消息数: {len(session.raw_messages)}")

        # 获取恢复后的历史
        restored_history = memory_manager2.get_session_history(session_id)
        print(f"   恢复的历史记录数: {len(restored_history)}")
    else:
        print("[ERROR] 无法恢复会话")

    # 测试增强消息
    print("\n6. 测试消息增强...")
    user_message = "这个股票的最新财报"
    enhanced = memory_manager.get_enhanced_message(session_id, user_message)
    print(f"[OK] 原始消息: {user_message}")
    print(f"[OK] 增强消息长度: {len(enhanced)}")
    print(f"[OK] 增强消息预览:\n{enhanced[:200]}...")

    # 测试会话合并
    print("\n7. 测试会话合并...")
    session_id2 = "test_session_456"
    memory_manager.create_session(session_id2)

    # 添加一些消息到第二个会话
    await memory_manager.add_message(session_id2, "user", "执行命令: ls -la")
    await memory_manager.add_message(session_id2, "bot", "已执行ls -la命令")

    # 合并会话
    success = memory_manager.merge_sessions(session_id2, session_id)
    if success:
        print(f"[OK] 成功合并会话 {session_id2} -> {session_id}")

        # 检查合并后的历史
        merged_history = memory_manager.get_session_history(session_id)
        print(f"   合并后的历史记录数: {len(merged_history)}")
    else:
        print("[ERROR] 会话合并失败")

    # 测试会话搜索
    print("\n8. 测试会话搜索...")
    search_results = memory_manager.search_conversations("股票", limit=5)
    print(f"[OK] 搜索'股票'找到 {len(search_results)} 条结果")
    for result in search_results:
        print(f"   会话: {result['session_id']}, 角色: {result['role']}, 内容: {result['content'][:40]}...")

    # 测试最近会话查找
    print("\n9. 测试最近会话查找...")
    recent_session = memory_manager.find_recent_session(hours=24)
    if recent_session:
        print(f"[OK] 找到最近会话: {recent_session}")
    else:
        print("[ERROR] 未找到最近会话")

    # 清理测试数据
    print("\n10. 清理测试数据...")
    import shutil
    test_memory_dir = Path(memory_dir)
    if test_memory_dir.exists():
        shutil.rmtree(test_memory_dir)
        print("[OK] 清理测试目录")
    else:
        print("[WARN] 测试目录不存在")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


async def test_chat_server_integration():
    """测试聊天服务器集成"""
    print("\n" + "=" * 60)
    print("测试聊天服务器集成")
    print("=" * 60)

    try:
        from src.chat_server import ChatServer

        print("\n1. 创建聊天服务器...")
        server = ChatServer()

        print("2. 初始化服务器...")
        success = await server.initialize()
        if not success:
            print("[ERROR] 服务器初始化失败")
            return

        print("[OK] 服务器初始化成功")

        # 检查记忆管理器
        if server.memory_manager:
            print(f"[OK] 记忆管理器已初始化")
            print(f"   已加载会话数: {len(server.memory_manager.sessions)}")

            # 测试创建会话
            test_session = server.memory_manager.create_session("integration_test")
            print(f"[OK] 创建集成测试会话: {test_session}")

            # 添加测试消息
            await server.memory_manager.add_message(test_session, "user", "集成测试消息")
            await server.memory_manager.add_message(test_session, "bot", "集成测试回复")

            # 获取历史
            history = server.memory_manager.get_session_history(test_session)
            print(f"[OK] 获取集成测试历史: {len(history)} 条消息")
        else:
            print("[ERROR] 记忆管理器未初始化")

    except Exception as e:
        print(f"[ERROR] 集成测试失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主函数"""
    try:
        await test_memory_system()
        await test_chat_server_integration()
    except Exception as e:
        print(f"[ERROR] 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())