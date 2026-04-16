#!/usr/bin/env python3
"""
测试两轮对话，查看模型实际收到的消息
"""

import asyncio
import websockets
import json
import sys
from pathlib import Path

async def test_two_round_conversation():
    """测试两轮对话"""

    # WebSocket URL - 使用新会话
    ws_url = "ws://localhost:8004/ws/new"

    print("=" * 80)
    print("测试两轮对话 - 查看模型实际收到的消息")
    print("=" * 80)

    try:
        async with websockets.connect(ws_url) as websocket:
            print("连接成功!")

            # 接收连接确认
            response = await websocket.recv()
            data = json.loads(response)
            session_id = data.get('session_id')
            print(f"会话ID: {session_id}")

            # 接收历史记录（新会话应该为空）
            response = await websocket.recv()
            data = json.loads(response)
            print(f"初始历史记录数量: {len(data.get('messages', []))}")

            # 第一轮对话
            print("\n" + "="*80)
            print("第一轮对话")
            print("="*80)

            message1 = "解释一下黑洞"
            print(f"发送: {message1}")

            await websocket.send(json.dumps({
                "type": "chat_message",
                "message": message1
            }))

            # 接收处理状态
            response = await websocket.recv()
            data = json.loads(response)
            print(f"状态: {data.get('message')}")

            # 接收回复
            response = await websocket.recv()
            data = json.loads(response)
            reply1 = data.get('message', '')
            print(f"回复长度: {len(reply1)} 字符")
            print(f"回复预览: {reply1[:200]}...")

            # 等待一下，让服务器处理完成
            await asyncio.sleep(2)

            # 第二轮对话
            print("\n" + "="*80)
            print("第二轮对话")
            print("="*80)

            message2 = "你刚才解释的黑洞，它的形成过程是怎样的？"
            print(f"发送: {message2}")
            print("注意：这次模型应该收到包含第一轮对话历史的增强消息")

            await websocket.send(json.dumps({
                "type": "chat_message",
                "message": message2
            }))

            # 接收处理状态
            response = await websocket.recv()
            data = json.loads(response)
            print(f"状态: {data.get('message')}")

            # 接收回复
            response = await websocket.recv()
            data = json.loads(response)
            reply2 = data.get('message', '')
            print(f"回复长度: {len(reply2)} 字符")
            print(f"回复预览: {reply2[:200]}...")

            # 分析第二轮对话的记忆效果
            print("\n" + "="*80)
            print("记忆功能分析")
            print("="*80)

            # 检查回复是否引用了第一轮内容
            memory_indicators = [
                ("刚才", "刚才"),
                ("之前", "之前"),
                ("提到", "提到"),
                ("解释", "解释"),
                ("黑洞", "黑洞"),
                ("形成", "形成"),
                ("过程", "过程"),
            ]

            found_indicators = []
            for indicator, display in memory_indicators:
                if indicator in reply2:
                    found_indicators.append(display)

            if found_indicators:
                print(f"✓ 回复中包含记忆关键词: {', '.join(found_indicators)}")
            else:
                print("✗ 回复中未找到明显的记忆关键词")

            # 检查回复是否连贯
            if len(reply2) > 100 and ("形成" in reply2 or "过程" in reply2):
                print("✓ 回复内容连贯，回答了关于形成过程的问题")
            else:
                print("✗ 回复可能不够连贯或未直接回答问题")

            print("\n测试完成!")
            print("请查看服务器日志中的【调试】部分，查看模型实际收到的消息内容")

    except Exception as e:
        print(f"连接失败: {e}")
        print("请确保聊天服务器正在运行 (python start_chat.py)")

async def test_with_existing_session():
    """测试现有会话的记忆功能"""

    # 使用现有的会话ID
    existing_session_id = "session_1776043332808_7yb6611ds"
    ws_url = f"ws://localhost:8004/ws/{existing_session_id}"

    print("\n" + "="*80)
    print(f"测试现有会话: {existing_session_id}")
    print("="*80)

    try:
        async with websockets.connect(ws_url) as websocket:
            print("连接成功!")

            # 接收连接确认
            response = await websocket.recv()
            data = json.loads(response)
            print(f"连接确认: {data.get('message')}")

            # 接收历史记录
            response = await websocket.recv()
            data = json.loads(response)
            messages = data.get('messages', [])
            print(f"历史记录数量: {len(messages)}")

            if messages:
                print("现有的历史消息:")
                for msg in messages[-2:]:  # 显示最近2条
                    sender = "用户" if msg.get('sender') == 'user' else "助手"
                    text = msg.get('text', '')
                    print(f"  {sender}: {text[:50]}...")

            # 测试记忆
            test_message = "我们之前讨论过黑洞吗？"
            print(f"\n发送: {test_message}")

            await websocket.send(json.dumps({
                "type": "chat_message",
                "message": test_message
            }))

            # 接收回复
            response = await websocket.recv()  # 状态
            response = await websocket.recv()  # 回复
            data = json.loads(response)
            reply = data.get('message', '')
            print(f"回复:\n{reply[:300]}...")

    except Exception as e:
        print(f"连接失败: {e}")

if __name__ == "__main__":
    print("开始测试两轮对话...")

    # 测试新会话的两轮对话
    asyncio.run(test_two_round_conversation())

    # 测试现有会话
    # asyncio.run(test_with_existing_session())