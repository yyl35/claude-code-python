#!/usr/bin/env python3
"""
测试会话恢复功能
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.memory.manager import MemoryManager


async def test_session_recovery():
    """测试会话恢复"""
    print("=" * 60)
    print("测试会话恢复功能")
    print("=" * 60)

    # 创建记忆管理器
    memory_dir = "test_session_recovery"
    memory_manager = MemoryManager(memory_dir=memory_dir, project_root=str(project_root))

    # 初始化
    print("\n1. 初始化记忆管理器...")
    success = await memory_manager.initialize()
    if not success:
        print("[ERROR] 初始化失败")
        return

    print("[OK] 初始化成功")

    # 模拟用户有多个会话
    print("\n2. 创建多个测试会话...")
    sessions = []
    for i in range(3):
        session_id = f"user_session_{i}"
        memory_manager.create_session(session_id)

        # 添加一些消息
        await memory_manager.add_message(session_id, "user", f"测试消息 {i} - 用户")
        await memory_manager.add_message(session_id, "bot", f"测试回复 {i} - 机器人")

        sessions.append(session_id)
        print(f"   [OK] 创建会话 {session_id}")

    # 等待保存
    await asyncio.sleep(1)

    # 测试会话恢复
    print("\n3. 测试会话恢复...")

    # 模拟用户使用新的session_id连接
    new_session_id = "user_new_session"

    # 查找最近的会话
    recent_session = memory_manager.find_recent_session(hours=24)
    if recent_session:
        print(f"   [OK] 找到最近会话: {recent_session}")

        # 获取该会话的历史
        history = memory_manager.get_session_history(recent_session)
        print(f"   [OK] 最近会话的历史记录: {len(history)} 条消息")

        # 模拟合并会话
        if new_session_id not in memory_manager.sessions:
            memory_manager.create_session(new_session_id)

        # 合并最近会话到新会话
        success = memory_manager.merge_sessions(recent_session, new_session_id)
        if success:
            print(f"   [OK] 成功合并会话 {recent_session} -> {new_session_id}")

            # 检查合并后的历史
            merged_history = memory_manager.get_session_history(new_session_id)
            print(f"   [OK] 合并后的历史记录: {len(merged_history)} 条消息")
        else:
            print(f"   [ERROR] 会话合并失败")
    else:
        print("   [ERROR] 未找到最近会话")

    # 测试 get_or_create_session 方法
    print("\n4. 测试 get_or_create_session 方法...")

    # 测试1: 使用现有的session_id
    existing_session = sessions[0]
    result1 = memory_manager.get_or_create_session(existing_session, restore_recent=True)
    print(f"   [OK] 使用现有会话 {existing_session} -> {result1}")

    # 测试2: 使用新的session_id，但恢复最近的
    new_session = "completely_new_session"
    result2 = memory_manager.get_or_create_session(new_session, restore_recent=True)
    print(f"   [OK] 使用新会话ID {new_session} -> {result2}")

    # 测试3: 不提供session_id，自动恢复最近的
    result3 = memory_manager.get_or_create_session(None, restore_recent=True)
    print(f"   [OK] 自动恢复会话 -> {result3}")

    # 测试会话搜索
    print("\n5. 测试会话搜索...")
    search_results = memory_manager.search_conversations("测试", limit=5)
    print(f"   [OK] 搜索'测试'找到 {len(search_results)} 条结果")

    for result in search_results[:3]:  # 显示前3个
        print(f"      会话: {result['session_id']}, 内容: {result['content'][:30]}...")

    # 清理
    print("\n6. 清理测试数据...")
    import shutil
    test_dir = Path(memory_dir)
    if test_dir.exists():
        shutil.rmtree(test_dir)
        print("   [OK] 清理测试目录")
    else:
        print("   [WARN] 测试目录不存在")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


async def test_real_scenario():
    """测试真实场景：用户重新连接"""
    print("\n" + "=" * 60)
    print("测试真实场景：用户重新连接")
    print("=" * 60)

    # 创建记忆管理器
    memory_dir = "test_real_scenario"
    memory_manager = MemoryManager(memory_dir=memory_dir, project_root=str(project_root))

    # 初始化
    await memory_manager.initialize()

    # 场景1: 用户第一次使用
    print("\n场景1: 用户第一次使用")
    user_session_1 = "session_1775994810057_q7dn7f3fs"  # 类似前端生成的ID
    memory_manager.create_session(user_session_1)

    # 用户进行一些对话
    await memory_manager.add_message(user_session_1, "user", "查一下贵州茅台的股价")
    await memory_manager.add_message(user_session_1, "bot", "贵州茅台(600519)当前价格: 1680.50元")
    await memory_manager.add_message(user_session_1, "user", "这个股票的历史最高价是多少？")
    await memory_manager.add_message(user_session_1, "bot", "贵州茅台历史最高价: 2586.91元")

    print(f"   [OK] 用户完成第一次对话，会话ID: {user_session_1}")
    print(f"       消息数: {memory_manager.sessions[user_session_1].message_count}")

    # 等待保存
    await asyncio.sleep(1)

    # 场景2: 用户第二天重新连接（可能清除了localStorage）
    print("\n场景2: 用户第二天重新连接")

    # 模拟用户生成了新的session_id
    user_session_2 = "session_1776081210057_abc123def"  # 新的session_id

    # 查找用户最近的会话
    recent_session = memory_manager.find_recent_session(hours=48)  # 48小时内
    if recent_session:
        print(f"   [OK] 找到用户最近的会话: {recent_session}")

        # 将新会话合并到旧会话（或者直接使用旧会话）
        if user_session_2 not in memory_manager.sessions:
            memory_manager.create_session(user_session_2)

        # 合并历史
        success = memory_manager.merge_sessions(user_session_2, recent_session)
        if success:
            print(f"   [OK] 成功恢复用户历史到会话: {recent_session}")

            # 用户继续对话
            await memory_manager.add_message(recent_session, "user", "我还想查一下五粮液的股价")
            await memory_manager.add_message(recent_session, "bot", "五粮液(000858)当前价格: 145.30元")

            # 获取完整历史
            full_history = memory_manager.get_session_history(recent_session)
            print(f"   [OK] 恢复后的完整历史: {len(full_history)} 条消息")

            # 显示历史
            print("\n   对话历史:")
            for i, msg in enumerate(full_history, 1):
                print(f"     {i}. {msg['sender']}: {msg['text'][:40]}...")
        else:
            print("   [ERROR] 无法恢复用户历史")
    else:
        print("   [ERROR] 未找到用户历史")

    # 清理
    import shutil
    test_dir = Path(memory_dir)
    if test_dir.exists():
        shutil.rmtree(test_dir)

    print("\n" + "=" * 60)
    print("真实场景测试完成")
    print("=" * 60)


async def main():
    """主函数"""
    try:
        await test_session_recovery()
        await test_real_scenario()
    except Exception as e:
        print(f"[ERROR] 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())