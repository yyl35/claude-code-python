#!/usr/bin/env python3
"""
测试记忆系统集成
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.memory.manager import MemoryManager
from src.memory.compressor import MemoryCompressor


async def test_memory_integration():
    """测试记忆系统集成"""
    print("=" * 60)
    print("测试记忆系统集成")
    print("=" * 60)

    # 创建记忆管理器
    memory_dir = "test_memory_integration"
    memory_manager = MemoryManager(memory_dir=memory_dir, project_root=str(project_root))

    # 初始化
    print("\n1. 初始化记忆管理器...")
    success = await memory_manager.initialize()
    if not success:
        print("[ERROR] 初始化失败")
        return

    print("[OK] 初始化成功")

    # 创建测试会话
    print("\n2. 创建测试会话并模拟对话...")
    session_id = "test_memory_session"
    memory_manager.create_session(session_id)

    # 模拟用户和AI的对话
    conversation = [
        ("user", "windows查看硬盘空间的命令是什么"),
        ("bot", "Windows查看硬盘空间的常用命令有：1. PowerShell: Get-PSDrive -PSProvider FileSystem 2. CMD: wmic logicaldisk get size,freespace,caption 3. 图形界面: 文件资源管理器右键属性"),
        ("user", "测试记忆 我刚才问你什么问题"),
    ]

    print("   模拟对话:")
    for role, content in conversation:
        await memory_manager.add_message(session_id, role, content)
        print(f"     {role}: {content[:50]}...")

    # 等待保存
    await asyncio.sleep(1)

    # 测试消息增强
    print("\n3. 测试消息增强功能...")
    compressor = MemoryCompressor()
    session_memory = memory_manager.sessions.get(session_id)

    if session_memory:
        print("   获取会话记忆...")
        print(f"   原始消息数: {len(session_memory.raw_messages)}")
        print(f"   摘要数: {len(session_memory.summaries)}")
        print(f"   实体数: {len(session_memory.entities)}")

        # 测试增强最后一个用户消息
        last_user_message = "测试记忆 我刚才问你什么问题"
        enhanced_message = compressor.enhance_message_with_context(
            last_user_message, session_memory, None
        )

        print("\n   [原始消息]")
        print(f"   {last_user_message}")

        print("\n   [增强后的消息]")
        print("-" * 40)
        print(enhanced_message)
        print("-" * 40)

        # 检查增强消息是否包含历史
        if "刚才" in last_user_message and "对话历史" in enhanced_message:
            print("\n   [OK] 增强消息成功包含对话历史")
        else:
            print("\n   [ERROR] 增强消息可能没有正确包含历史")

        # 测试记忆管理器的增强方法
        print("\n4. 测试记忆管理器的增强方法...")
        enhanced_from_manager = memory_manager.get_enhanced_message(session_id, last_user_message)
        print(f"   增强消息长度: {len(enhanced_from_manager)}")
        print(f"   是否包含'对话历史': {'对话历史' in enhanced_from_manager}")

        # 显示增强消息的前500个字符
        print("\n   [增强消息预览]")
        print(enhanced_from_manager[:500] + "...")

    else:
        print("[ERROR] 无法获取会话记忆")

    # 测试指代解析
    print("\n5. 测试指代解析...")
    test_messages = [
        "这个命令的具体用法是什么",
        "刚才说的那个命令",
        "上面提到的查看硬盘空间的方法",
    ]

    for test_msg in test_messages:
        enhanced = memory_manager.get_enhanced_message(session_id, test_msg)
        print(f"\n   测试消息: {test_msg}")
        print(f"   增强后长度: {len(enhanced)}")
        if "对话历史" in enhanced:
            print("   [OK] 包含对话历史")
        else:
            print("   [WARN] 可能不包含对话历史")

    # 清理
    print("\n6. 清理测试数据...")
    import shutil
    test_dir = Path(memory_dir)
    if test_dir.exists():
        shutil.rmtree(test_dir)
        print("   [OK] 清理测试目录")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


async def test_real_conversation():
    """测试真实对话场景"""
    print("\n" + "=" * 60)
    print("测试真实对话场景")
    print("=" * 60)

    # 创建记忆管理器
    memory_dir = "test_real_conversation"
    memory_manager = MemoryManager(memory_dir=memory_dir, project_root=str(project_root))
    await memory_manager.initialize()

    # 创建会话
    session_id = "real_conversation_1"
    memory_manager.create_session(session_id)

    # 模拟真实对话
    print("\n模拟真实对话场景:")
    print("-" * 40)

    scenarios = [
        {
            "user": "帮我查一下贵州茅台的股价",
            "bot": "贵州茅台(600519)当前价格: 1680.50元，今日涨幅: +2.5%"
        },
        {
            "user": "这个股票的历史最高价是多少？",
            "bot": "贵州茅台历史最高价是2586.91元，发生在2021年2月。"
        },
        {
            "user": "刚才说的那个股票，它的市盈率是多少？",
            "bot": "贵州茅台当前市盈率(PE)约为32.5倍。"
        },
        {
            "user": "测试一下，你还记得我问的第一个问题是什么吗？",
            "bot": "您问的第一个问题是关于贵州茅台股价的查询。"
        }
    ]

    for i, scenario in enumerate(scenarios, 1):
        user_msg = scenario["user"]
        bot_msg = scenario["bot"]

        print(f"\n回合 {i}:")
        print(f"  用户: {user_msg}")
        print(f"  AI: {bot_msg}")

        # 添加到记忆
        await memory_manager.add_message(session_id, "user", user_msg)
        await memory_manager.add_message(session_id, "bot", bot_msg)

        # 测试增强
        if i >= 2:  # 从第二回合开始测试
            enhanced = memory_manager.get_enhanced_message(session_id, user_msg)
            print(f"\n  增强消息预览:")
            print(f"  {enhanced[:200]}...")

            # 检查关键元素
            checks = [
                ("对话历史" in enhanced, "包含对话历史"),
                ("贵州茅台" in enhanced or "600519" in enhanced, "包含股票信息"),
                ("用户:" in enhanced and "助手:" in enhanced, "包含角色标签"),
            ]

            for check_result, check_name in checks:
                if check_result:
                    print(f"  [OK] {check_name}")
                else:
                    print(f"  [WARN] 可能缺少: {check_name}")

    # 测试最终的记忆状态
    print("\n最终记忆状态:")
    session_memory = memory_manager.sessions.get(session_id)
    if session_memory:
        print(f"  总消息数: {session_memory.message_count}")
        print(f"  原始消息数: {len(session_memory.raw_messages)}")
        print(f"  实体数: {len(session_memory.entities)}")
        print(f"  摘要数: {len(session_memory.summaries)}")

        # 显示所有实体
        if session_memory.entities:
            print("\n  识别的实体:")
            for entity_id, entity in session_memory.entities.items():
                print(f"    - {entity.type}: {entity.name} (引用{entity.reference_count}次)")

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
        await test_memory_integration()
        await test_real_conversation()
    except Exception as e:
        print(f"[ERROR] 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())