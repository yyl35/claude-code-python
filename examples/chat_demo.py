#!/usr/bin/env python3
"""
聊天界面使用示例
演示如何通过编程方式使用聊天服务器
"""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def chat_with_agent():
    """通过WebSocket与代理聊天"""
    print("[机器人] DevOps Agent 聊天演示")
    print("=" * 60)

    # WebSocket连接参数
    session_id = f"demo_session_{int(asyncio.get_event_loop().time())}"
    ws_url = f"ws://localhost:8001/ws/{session_id}"

    print(f"会话ID: {session_id}")
    print(f"WebSocket地址: {ws_url}")
    print("\n开始聊天 (输入 'quit' 退出)")
    print("=" * 60)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(ws_url) as ws:
                # 等待连接成功
                print("连接服务器...")
                msg = await ws.receive()
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    if data.get("type") == "status":
                        print(f"[成功] {data.get('message')}")

                # 聊天循环
                while True:
                    try:
                        # 获取用户输入
                        user_input = await asyncio.get_event_loop().run_in_executor(
                            None, input, "\n你: "
                        )

                        if user_input.lower() in ['quit', 'exit', 'q']:
                            print("[再见] 再见！")
                            break

                        if not user_input.strip():
                            continue

                        # 发送消息
                        message = {
                            "type": "chat_message",
                            "message": user_input,
                            "session_id": session_id
                        }
                        await ws.send_json(message)

                        print("代理正在处理...")

                        # 接收响应
                        while True:
                            response = await ws.receive(timeout=30)
                            if response.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(response.data)

                                if data.get("type") == "chat_response":
                                    print(f"\n[机器人] 代理: {data.get('message')}")
                                    break
                                elif data.get("type") == "error":
                                    print(f"\n[错误] 错误: {data.get('message')}")
                                    break
                                elif data.get("type") == "status":
                                    # 状态更新，继续等待
                                    continue
                            else:
                                print(f"收到非文本消息: {response.type}")
                                break

                    except asyncio.TimeoutError:
                        print("[超时] 响应超时，请重试")
                    except KeyboardInterrupt:
                        print("\n\n中断聊天")
                        break
                    except Exception as e:
                        print(f"[错误] 错误: {e}")
                        break

    except aiohttp.ClientConnectorError:
        print("[错误] 无法连接到服务器")
        print("请先启动聊天服务器:")
        print("  python start_chat.py")
    except Exception as e:
        print(f"[错误] 连接失败: {e}")

async def check_server_status():
    """检查服务器状态"""
    print("检查服务器状态...")

    try:
        async with aiohttp.ClientSession() as session:
            # 健康检查
            async with session.get('http://localhost:8001/api/health') as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"[成功] 服务器健康: {data.get('status')}")
                    return True
                else:
                    print(f"[错误] 服务器异常: HTTP {response.status}")
                    return False
    except Exception as e:
        print(f"[错误] 无法连接到服务器: {e}")
        return False

async def main():
    """主函数"""
    print("DevOps Agent 聊天界面编程示例")
    print("=" * 60)

    # 检查服务器状态
    if not await check_server_status():
        print("\n⚠️  请先启动聊天服务器:")
        print("  python start_chat.py")
        print("\n然后重新运行此示例")
        return 1

    # 开始聊天
    await chat_with_agent()

    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[再见] 示例结束")
        sys.exit(0)