#!/usr/bin/env python3
"""
测试简单命令的WebSocket响应
"""

import asyncio
import websockets
import json
import time

async def test_simple_command():
    """测试简单命令"""
    session_id = f"test_session_{int(time.time())}"
    uri = f"ws://localhost:8003/ws/{session_id}"

    print(f"连接到: {uri}")
    print(f"会话ID: {session_id}")

    try:
        async with websockets.connect(uri) as websocket:
            print("连接成功，等待欢迎消息...")

            # 接收欢迎消息
            welcome = await websocket.recv()
            print(f"收到欢迎消息: {welcome[:200]}...")

            # 发送简单测试消息
            test_message = {
                "type": "chat_message",
                "message": "测试连接",
                "session_id": session_id
            }

            print(f"发送消息: {json.dumps(test_message, ensure_ascii=False)}")
            await websocket.send(json.dumps(test_message))

            # 等待响应（最多30秒）
            print("等待响应...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                print(f"收到响应: {response[:500]}...")

                # 解析响应
                data = json.loads(response)
                response_type = data.get("type")
                message = data.get("message", "")

                print(f"响应类型: {response_type}")
                print(f"响应内容长度: {len(message)} 字符")
                print(f"前200字符: {message[:200]}...")

                if response_type == "chat_response":
                    print("聊天响应成功！")
                    return True
                elif response_type == "error":
                    print(f"错误: {message}")
                    return False
                else:
                    print(f"未知响应类型: {response_type}")
                    return False

            except asyncio.TimeoutError:
                print("错误: 等待响应超时（30秒）")
                return False

    except Exception as e:
        print(f"连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_echo_command():
    """测试echo命令"""
    session_id = f"test_session_{int(time.time())}_echo"
    uri = f"ws://localhost:8003/ws/{session_id}"

    print(f"\n测试echo命令...")
    print(f"连接到: {uri}")

    try:
        async with websockets.connect(uri) as websocket:
            # 接收欢迎消息
            await websocket.recv()
            await websocket.recv()  # 历史消息

            # 发送echo命令
            test_message = {
                "type": "chat_message",
                "message": "执行命令：echo hello world",
                "session_id": session_id
            }

            print(f"发送消息: {json.dumps(test_message, ensure_ascii=False)}")
            await websocket.send(json.dumps(test_message))

            # 等待响应
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                print(f"收到响应: {response[:500]}...")

                data = json.loads(response)
                if data.get("type") == "chat_response":
                    print("Echo命令响应成功！")
                    return True
                else:
                    print(f"非预期响应类型: {data.get('type')}")
                    return False

            except asyncio.TimeoutError:
                print("错误: 等待响应超时（60秒）")
                return False

    except Exception as e:
        print(f"连接失败: {e}")
        return False

async def main():
    """主函数"""
    print("=" * 60)
    print("WebSocket简单命令测试")
    print("=" * 60)

    # 测试简单连接
    print("\n1. 测试简单连接...")
    success1 = await test_simple_command()

    # 测试echo命令
    print("\n2. 测试echo命令...")
    success2 = await test_echo_command()

    print("\n" + "=" * 60)
    if success1 and success2:
        print("所有测试通过！")
    else:
        print(f"测试结果: 连接测试={success1}, echo测试={success2}")
    print("=" * 60)

    return 0 if (success1 and success2) else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)