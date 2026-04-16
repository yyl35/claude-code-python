from typing import List, Dict, Any
from langchain_core.tools import StructuredTool
from pydantic import Field, create_model
from mcp import ClientSession
from mcp.client.sse import sse_client
import asyncio

class MCPToolManager:
    """MCP工具动态加载和管理"""

    def __init__(self, mcp_server_url: str):
        self.mcp_server_url = mcp_server_url
        self._tools_cache = {}
        self._tool_descriptions = {}

    async def fetch_tools(self) -> List[StructuredTool]:
        """从MCP服务器获取工具列表"""
        from langchain_core.tools import tool

        tools = []
        async with sse_client(self.mcp_server_url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                mcp_tools = await session.list_tools()

                for t in mcp_tools.tools:
                    # 缓存工具描述
                    self._tool_descriptions[t.name] = {
                        "description": t.description,
                        "input_schema": t.inputSchema
                    }

                    # 创建动态Pydantic模型
                    properties = t.inputSchema.get("properties", {})
                    fields = {
                        p_name: (
                            str,
                            Field(
                                default=p_info.get("default"),
                                description=p_info.get("description", "")
                            )
                        )
                        for p_name, p_info in properties.items()
                        if p_name != 'ctx'
                    }

                    if fields:
                        args_schema = create_model(f"{t.name}_args", **fields)
                    else:
                        args_schema = create_model(f"{t.name}_args")

                    # 创建工具执行函数
                    async def create_tool_runner(tool_name: str):
                        async def run_tool(**kwargs):
                            async with sse_client(self.mcp_server_url) as (r, w):
                                async with ClientSession(r, w) as s:
                                    await s.initialize()
                                    clean_params = {k: v for k, v in kwargs.items() if v is not None}
                                    try:
                                        res = await s.call_tool(tool_name, clean_params)
                                        output = "\n".join([
                                            str(c.text) if hasattr(c, 'text') else str(c)
                                            for c in res.content
                                        ])
                                        return f"工具 '{tool_name}' 执行成功:\n{output}"
                                    except Exception as e:
                                        return f"工具 '{tool_name}' 执行失败: {str(e)}"
                        return run_tool

                    # 创建LangChain工具
                    tool_runner = await create_tool_runner(t.name)
                    lc_tool = StructuredTool(
                        name=t.name,
                        description=t.description,
                        coroutine=tool_runner,
                        args_schema=args_schema if fields else None
                    )

                    tools.append(lc_tool)
                    self._tools_cache[t.name] = lc_tool

        return tools

    def get_tool_descriptions(self) -> Dict[str, str]:
        """获取所有工具的描述"""
        return {
            name: info["description"]
            for name, info in self._tool_descriptions.items()
        }

    def get_tool_by_category(self) -> Dict[str, List[str]]:
        """按类别组织工具"""
        categories = {
            "file_operations": ["read_file", "write_file", "list_files", "delete_file"],
            "command_execution": ["execute_command", "run_script"],
            "data_fetching": ["get_stock_data", "get_market_data"],
            "code_development": ["create_file", "modify_code", "run_tests"],
            "system_monitoring": ["check_disk", "check_memory", "check_process"]
        }

        return {
            category: [tool for tool in self._tools_cache.keys() if any(t in tool for t in tool_names)]
            for category, tool_names in categories.items()
        }