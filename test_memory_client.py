#!/usr/bin/env python3
"""
测试记忆功能的客户端
"""

import asyncio
import websockets
import json
import sys
from pathlib import Path

async def test_memory_function():
    """测试记忆功能"""

    # WebSocket URL
    ws_url = "ws://localhost:8004/ws/new"

    print(f"连接到: {ws_url}")

    try:
        async with websockets.connect(ws_url) as websocket:
            print("连接成功!")

            # 接收连接确认
            response = await websocket.recv()
            data = json.loads(response)
            print(f"连接确认: {data.get('message')}")
            session_id = data.get('session_id')
            print(f"会话ID: {session_id}")

            # 接收历史记录
            response = await websocket.recv()
            data = json.loads(response)
            print(f"历史记录数量: {len(data.get('messages', []))}")

            # 测试1: 发送第一个消息
            print("\n" + "="*80)
            print("测试1: 发送第一个消息")
            print("="*80)

            message1 = "解释一下黑洞"
            await websocket.send(json.dumps({
                "type": "chat_message",
                "message": message1
            }))
            print(f"发送: {message1}")

            # 接收处理状态
            response = await websocket.recv()
            data = json.loads(response)
            print(f"状态: {data.get('message')}")

            # 接收回复
            response = await websocket.recv()
            data = json.loads(response)
            print(f"回复长度: {len(data.get('message', ''))}")
            print(f"回复预览: {data.get('message', '')[:200]}...")

            # 等待一下
            await asyncio.sleep(1)

            # 测试2: 发送第二个消息（测试记忆）
            print("\n" + "="*80)
            print("测试2: 发送第二个消息（测试记忆）")
            print("="*80)

            message2 = "写个计算因子IC的代码，模拟一下假数据测试"
            await websocket.send(json.dumps({
                "type": "chat_message",
                "message": message2
            }))
            print(f"发送: {message2}")

            # 接收处理状态
            response = await websocket.recv()
            data = json.loads(response)
            print(f"状态: {data.get('message')}")

            # 接收回复
            response = await websocket.recv()
            data = json.loads(response)
            print(f"回复长度: {len(data.get('message', ''))}")
            print(f"回复预览: {data.get('message', '')[:200]}...")

            # 等待一下
            await asyncio.sleep(1)

            # 测试3: 发送第三个消息（测试指代和记忆）
            print("\n" + "="*80)
            print("测试3: 发送第三个消息（测试指代和记忆）")
            print("="*80)

            message3 = "你刚才帮我实际运行过吗"
            await websocket.send(json.dumps({
                "type": "chat_message",
                "message": message3
            }))
            print(f"发送: {message3}")

            # 接收处理状态
            response = await websocket.recv()
            data = json.loads(response)
            print(f"状态: {data.get('message')}")

            # 接收回复
            response = await websocket.recv()
            data = json.loads(response)
            reply = data.get('message', '')
            print(f"回复长度: {len(reply)}")
            print(f"完整回复:\n{reply}")

            # 分析回复是否包含记忆
            print("\n" + "="*80)
            print("记忆功能分析:")
            print("="*80)

            keywords = ["刚才", "之前", "提到", "说过", "黑洞", "因子IC", "代码", "运行", "测试"]
            found_keywords = []
            for keyword in keywords:
                if keyword in reply:
                    found_keywords.append(keyword)

            if found_keywords:
                print(f"✓ 回复中包含记忆关键词: {', '.join(found_keywords)}")
            else:
                print("✗ 回复中未找到明显的记忆关键词")

            # 检查是否回答了问题
            if "没有" in reply or "未" in reply or "不" in reply or "否" in reply:
                print("✓ 明确回答了是否运行过的问题")
            else:
                print("✗ 未明确回答是否运行过的问题")

            print("\n测试完成!")

    except Exception as e:
        print(f"连接失败: {e}")
        print("请确保聊天服务器正在运行 (python start_chat.py)")

async def test_existing_session():
    """测试现有会话"""

    # 使用现有的会话ID
    existing_session_id = "session_1776043332808_7yb6611ds"
    ws_url = f"ws://localhost:8004/ws/{existing_session_id}"

    print(f"\n" + "="*80)
    print(f"测试现有会话: {existing_session_id}")
    print("="*80)

    try:
        async with websockets.connect(ws_url) as websocket:
            print("连接成功!")

            # 接收连接确认
            response = await websocket.recv()
            data = json.loads(response)
            print(f"连接确认: {data.get('message')}")
            actual_session_id = data.get('session_id')
            print(f"实际会话ID: {actual_session_id}")

            # 接收历史记录
            response = await websocket.recv()
            data = json.loads(response)
            messages = data.get('messages', [])
            print(f"历史记录数量: {len(messages)}")

            if messages:
                print("最近的历史消息:")
                for msg in messages[-3:]:  # 显示最近3条
                    print(f"  {msg.get('sender')}: {msg.get('text', '')[:50]}...")

            # 测试记忆
            test_message = "我们之前讨论过什么话题？"
            await websocket.send(json.dumps({
                "type": "chat_message",
                "message": test_message
            }))
            print(f"\n发送: {test_message}")

            # 接收回复
            response = await websocket.recv()  # 状态
            response = await websocket.recv()  # 回复
            data = json.loads(response)
            reply = data.get('message', '')
            print(f"回复:\n{reply[:500]}...")

    except Exception as e:
        print(f"连接失败: {e}")

if __name__ == "__main__":
    print("测试记忆功能客户端...")

    # 测试新会话
    asyncio.run(test_memory_function())

    # 测试现有会话
    # asyncio.run(test_existing_session())