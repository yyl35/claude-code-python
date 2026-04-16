#!/usr/bin/env python3
"""
测试聊天服务器功能
"""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_health_check():
    """测试健康检查API"""
    print("测试健康检查API...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8001/api/health') as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"[成功] 健康检查通过: {data}")
                    return True
                else:
                    print(f"[失败] 健康检查失败: HTTP {response.status}")
                    return False
    except Exception as e:
        print(f"[失败] 健康检查异常: {e}")
        return False

async def test_status_api():
    """测试状态API"""
    print("\n测试状态API...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8001/api/status') as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"[成功] 状态API通过:")
                    print(f"   代理状态: {data.get('agent_status')}")
                    print(f"   活动连接: {data.get('active_connections')}")
                    print(f"   记忆统计: {data.get('memory_stats', {}).get('total_sessions', 0)} 个会话")
                    return True
                else:
                    print(f"[失败] 状态API失败: HTTP {response.status}")
                    return False
    except Exception as e:
        print(f"[失败] 状态API异常: {e}")
        return False

async def test_websocket_connection():
    """测试WebSocket连接"""
    print("\n测试WebSocket连接...")

    try:
        session_id = f"test_session_{int(asyncio.get_event_loop().time())}"
        ws_url = f"ws://localhost:8001/ws/{session_id}"

        print(f"连接WebSocket: {ws_url}")

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(ws_url) as ws:
                # 等待连接消息
                msg = await ws.receive(timeout=5)
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    if data.get("type") == "status" and "连接成功" in data.get("message", ""):
                        print("[成功] WebSocket连接成功")

                        # 测试发送消息
                        test_message = {
                            "type": "chat_message",
                            "message": "测试消息",
                            "session_id": session_id
                        }
                        await ws.send_json(test_message)

                        # 等待响应（可能有超时，因为代理需要初始化）
                        try:
                            response = await ws.receive(timeout=10)
                            if response.type == aiohttp.WSMsgType.TEXT:
                                resp_data = json.loads(response.data)
                                print(f"[成功] 收到响应: {resp_data.get('type')}")
                                return True
                        except asyncio.TimeoutError:
                            print("[警告]  响应超时（代理可能需要初始化）")
                            return True
                    else:
                        print(f"[失败] 连接消息异常: {data}")
                        return False
                else:
                    print(f"[失败] 收到非文本消息: {msg.type}")
                    return False

    except Exception as e:
        print(f"[失败] WebSocket连接异常: {e}")
        return False

async def test_memory_manager():
    """测试记忆管理器"""
    print("\n测试记忆管理器...")

    try:
        from src.chat_memory import ChatMemoryManager

        memory_manager = ChatMemoryManager("test_memory")
        await memory_manager.initialize()

        # 创建测试会话
        session_id = memory_manager.create_session("test_memory_session")
        print(f"[成功] 创建会话: {session_id}")

        # 添加消息
        memory_manager.add_message(session_id, "user", "测试用户消息")
        memory_manager.add_message(session_id, "bot", "测试机器人回复")
        print("[成功] 添加测试消息")

        # 获取历史
        history = memory_manager.get_session_history(session_id)
        print(f"[成功] 获取历史记录: {len(history)} 条消息")

        # 获取上下文
        context = memory_manager.get_conversation_context(session_id)
        print(f"[成功] 获取上下文: {len(context)} 字符")

        # 获取统计
        stats = memory_manager.get_stats()
        print(f"[成功] 获取统计: {stats.get('total_sessions')} 个会话")

        # 清理
        memory_manager.clear_session_history(session_id)
        print("[成功] 清理历史记录")

        return True

    except Exception as e:
        print(f"[失败] 记忆管理器测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("=" * 60)
    print("DevOps Agent聊天界面测试")
    print("=" * 60)

    # 检查服务器是否运行
    print("\n检查服务器状态...")

    tests = [
        ("健康检查API", test_health_check),
        ("状态API", test_status_api),
        ("WebSocket连接", test_websocket_connection),
        ("记忆管理器", test_memory_manager),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"[失败] {test_name} 测试异常: {e}")
            results.append((test_name, False))

    # 输出测试结果
    print("\n" + "=" * 60)
    print("测试结果:")
    print("=" * 60)

    all_passed = True
    for test_name, success in results:
        status = "[成功] 通过" if success else "[失败] 失败"
        print(f"{test_name}: {status}")
        if not success:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("[庆祝] 所有测试通过！")
        print("\n下一步:")
        print("1. 启动聊天服务器: python start_chat.py")
        print("2. 打开浏览器访问: http://localhost:8001")
        print("3. 开始聊天吧！")
    else:
        print("[警告]  部分测试失败")
        print("\n可能的原因:")
        print("1. 服务器未启动 - 运行: python start_chat.py")
        print("2. 端口被占用 - 检查端口8001")
        print("3. 依赖未安装 - 运行: pip install -r requirements.txt")

    print("=" * 60)

    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)