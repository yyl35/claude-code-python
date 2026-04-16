#!/usr/bin/env python3
"""
测试WebSocket连接和消息处理
"""

import asyncio
import websockets
import json
import uuid
import time

async def test_websocket():
    """测试WebSocket连接"""
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

            # 发送测试消息
            test_message = {
                "type": "chat_message",
                "message": "用powershell命令帮我查一下电脑剩余硬盘空间",
                "session_id": session_id
            }

            print(f"发送消息: {json.dumps(test_message, ensure_ascii=False)}")
            await websocket.send(json.dumps(test_message))

            # 等待响应（最多30秒）
            print("等待响应...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=120.0)
                print(f"收到响应: {response[:500]}...")

                # 解析响应
                data = json.loads(response)
                response_type = data.get("type")
                message = data.get("message", "")

                print(f"响应类型: {response_type}")
                print(f"响应内容长度: {len(message)} 字符")
                print(f"前200字符: {message[:200]}...")

                # 如果有错误
                if response_type == "error":
                    print(f"错误: {message}")
                elif response_type == "chat_response":
                    print("聊天响应成功！")
                else:
                    print(f"未知响应类型: {response_type}")

            except asyncio.TimeoutError:
                print("错误: 等待响应超时（120秒）")
                return False

            # 等待可能的多条消息
            print("等待额外消息...")
            try:
                while True:
                    extra = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    print(f"额外消息: {extra[:200]}...")
            except asyncio.TimeoutError:
                print("没有更多消息")

            return True

    except Exception as e:
        print(f"连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("=" * 60)
    print("WebSocket连接测试")
    print("=" * 60)

    success = await test_websocket()

    print("\n" + "=" * 60)
    if success:
        print("测试通过！WebSocket连接正常")
    else:
        print("测试失败！")
    print("=" * 60)

    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)