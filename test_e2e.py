#!/usr/bin/env python3
"""
端到端测试 - 使用模拟MCP工具
"""

import sys
import os
import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_with_mock_tools():
    """使用模拟工具测试"""
    print("Testing with mock MCP tools...")

    # 模拟MCP工具
    mock_tools = [
        Mock(
            name="read_file",
            description="读取文件内容",
            inputSchema={
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "文件路径"
                    }
                }
            }
        ),
        Mock(
            name="execute_command",
            description="执行系统命令",
            inputSchema={
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的命令"
                    }
                }
            }
        ),
        Mock(
            name="get_stock_data",
            description="获取股票数据",
            inputSchema={
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "股票代码"
                    }
                }
            }
        )
    ]

    # 模拟MCP会话
    mock_session = AsyncMock()
    mock_session.list_tools = AsyncMock(return_value=Mock(tools=mock_tools))
    mock_session.call_tool = AsyncMock(side_effect=lambda name, params: Mock(content=[
        Mock(text=f"Mock result for {name} with params: {params}")
    ]))

    # 模拟sse_client
    mock_sse_client = AsyncMock()
    mock_sse_client.__aenter__ = AsyncMock(return_value=(AsyncMock(), AsyncMock()))
    mock_sse_client.__aexit__ = AsyncMock()

    with patch('src.tool_manager.sse_client', return_value=mock_sse_client):
        with patch('src.tool_manager.ClientSession', return_value=mock_session):
            with patch('src.agent_executor.ChatOpenAI') as mock_llm:
                # 模拟LLM响应
                mock_response = Mock()
                mock_response.content = '{"action": "call_tool", "tool": "read_file", "params": {"file_path": "test.txt"}}'
                mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)

                try:
                    # 导入并测试
                    from src.config import config
                    from src.tool_manager import MCPToolManager
                    from src.skill_manager import SkillManager
                    from src.agent_executor import AgentExecutor

                    print("OK  All modules imported successfully")

                    # 创建管理器
                    tool_manager = MCPToolManager("http://mock-server:9999/sse")
                    skill_manager = SkillManager()

                    # 获取工具
                    tools = await tool_manager.fetch_tools()
                    print(f"OK  Tools loaded: {len(tools)} tools")

                    # 检查技能
                    skills = skill_manager.list_skills()
                    print(f"OK  Skills available: {list(skills.keys())}")

                    # 测试代理执行器
                    agent = AgentExecutor(config, tool_manager, skill_manager)
                    await agent.initialize()
                    print("OK  Agent initialized")

                    # 测试直接执行（会使用模拟LLM）
                    result = await agent.execute_direct("读取文件 test.txt")
                    print(f"OK  Direct execution test completed")
                    print(f"  Result preview: {result[:100]}...")

                    return True

                except Exception as e:
                    print(f"FAIL Test failed: {e}")
                    import traceback
                    traceback.print_exc()
                    return False

async def test_main_module():
    """测试主模块"""
    print("\nTesting main module...")

    with patch('src.main.MCPToolManager') as MockToolManager:
        with patch('src.main.ChatOpenAI') as MockLLM:
            with patch('src.main.AgentExecutor') as MockAgentExecutor:
                # 设置模拟
                mock_tools = [Mock(name=f"tool_{i}") for i in range(3)]
                mock_tool_manager = AsyncMock()
                mock_tool_manager.fetch_tools = AsyncMock(return_value=mock_tools)
                mock_tool_manager.get_tool_descriptions = Mock(return_value={
                    "read_file": "读取文件",
                    "execute_command": "执行命令"
                })
                MockToolManager.return_value = mock_tool_manager

                mock_llm_instance = Mock()
                MockLLM.return_value = mock_llm_instance

                mock_agent = AsyncMock()
                mock_agent.initialize = AsyncMock()
                mock_agent.execute_direct = AsyncMock(return_value="Mock execution result")
                MockAgentExecutor.return_value = mock_agent

                try:
                    from src.main import DevOpsAgent

                    agent = DevOpsAgent()
                    init_result = await agent.initialize()

                    if init_result:
                        print("OK  Main module initialization successful")

                        # 测试任务处理
                        result = await agent.process_task("测试任务")
                        print(f"OK  Task processing test completed")
                        print(f"  Result: {result[:50]}...")

                        return True
                    else:
                        print("FAIL Main module initialization failed")
                        return False

                except Exception as e:
                    print(f"FAIL Main module test failed: {e}")
                    import traceback
                    traceback.print_exc()
                    return False

def main():
    print("=" * 60)
    print("DevOps-Agent End-to-End Test")
    print("=" * 60)

    results = []

    # 运行异步测试
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        print("\n[Part 1: Mock MCP Tools Test]")
        result1 = loop.run_until_complete(test_with_mock_tools())
        results.append(result1)

        print("\n[Part 2: Main Module Test]")
        result2 = loop.run_until_complete(test_main_module())
        results.append(result2)

    finally:
        loop.close()

    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"Total tests: {len(results)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")

    if all(results):
        print("\nSUCCESS: All end-to-end tests passed!")
        print("\nNote: This test uses mocked components.")
        print("For full functionality, you need:")
        print("  1. Real OpenAI API key (DeepSeek)")
        print("  2. Real MCP server running")
        print("  3. Real LangChain dependencies")
        return 0
    else:
        print("\nFAILURE: Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())