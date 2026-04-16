import asyncio
import sys
from typing import Optional
import argparse

from .config import config
from .tool_manager import MCPToolManager
from .task_parser import TaskParser
from .skill_manager import SkillManager
from .agent_executor import AgentExecutor
from .state_manager import StateManager

class DevOpsAgent:
    """DevOps智能代理主类"""

    def __init__(self):
        self.config = config
        self.tool_manager = MCPToolManager(config.mcp_server_url)
        self.llm = self._create_llm()
        self.task_parser = TaskParser(self.llm)
        self.skill_manager = SkillManager(self.llm)
        self.agent_executor = AgentExecutor(config, self.tool_manager, self.skill_manager)
        self.state_manager = StateManager(config.memory_path)

    def _create_llm(self):
        """创建LLM实例"""
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            api_key=self.config.openai_api_key,
            base_url=self.config.openai_base_url,
            model_name=self.config.model_name,
            temperature=self.config.model_temperature
        )

    async def initialize(self):
        """初始化所有组件"""
        print("初始化DevOps代理...")

        # 测试MCP连接
        try:
            tools = await self.tool_manager.fetch_tools()
            print(f"[OK] 已连接MCP服务器，发现 {len(tools)} 个工具")
        except Exception as e:
            print(f"[FAIL] MCP连接失败: {e}")
            return False

        # 初始化代理执行器
        await self.agent_executor.initialize()
        print("[OK] 代理执行器初始化完成")

        # 加载状态
        await self.state_manager.load_state()
        print("[OK] 状态管理器初始化完成")

        print("\n可用技能:")
        for name, desc in self.skill_manager.list_skills().items():
            print(f"  - {name}: {desc}")

        print("\nDevOps代理就绪！")
        return True

    async def process_task(self, user_input: str, use_skill: Optional[str] = None) -> str:
        """处理用户任务"""

        # 记录任务
        await self.state_manager.record_task(user_input)

        # 如果指定了技能，使用技能执行
        if use_skill:
            print(f"使用技能执行: {use_skill}")
            result = await self.agent_executor.execute_with_skill(user_input, use_skill)

        else:
            # 尝试识别技能
            identified_skill = await self.task_parser.identify_skill(user_input)

            if identified_skill:
                print(f"自动识别技能: {identified_skill}")
                # 对于所有技能，都使用execute_direct以便获得智能总结结果
                print(f"{identified_skill}技能，使用execute_direct进行智能总结...")
                result = await self.agent_executor.execute_direct(user_input)
            else:
                # 使用React代理直接执行
                print("使用React代理执行...")

                # 获取工具描述供任务解析
                tool_descriptions = self.tool_manager.get_tool_descriptions()

                # 解析任务
                task_plan = await self.task_parser.parse_task(user_input, tool_descriptions)

                if task_plan["execution_order"] == "parallel" and len(task_plan["subtasks"]) > 1:
                    # 并行执行
                    print(f"并行执行 {len(task_plan['subtasks'])} 个子任务")
                    results = await self.agent_executor.parallel_execute(task_plan["subtasks"])
                    result = "\n".join(results)
                else:
                    # 直接执行
                    result = await self.agent_executor.execute_direct(user_input)

        # 保存结果到状态
        await self.state_manager.record_result(user_input, result)

        return result

    async def interactive_mode(self):
        """交互式模式"""
        print("\n" + "="*50)
        print("DevOps智能代理 - 交互模式")
        print("输入 'quit' 或 'exit' 退出")
        print("输入 'help' 查看帮助")
        print("="*50)

        while True:
            try:
                user_input = input("\n>>> ").strip()

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("再见！")
                    break

                elif user_input.lower() == 'help':
                    self._show_help()
                    continue

                elif user_input.lower() == 'tools':
                    await self._list_tools()
                    continue

                elif user_input.lower() == 'skills':
                    self._list_skills()
                    continue

                elif user_input.lower() == 'history':
                    await self._show_history()
                    continue

                if not user_input:
                    continue

                # 处理任务
                print("处理中...")
                result = await self.process_task(user_input)
                print(f"\n结果:\n{result}")

            except KeyboardInterrupt:
                print("\n\n中断执行")
                break
            except Exception as e:
                print(f"错误: {e}")

    def _show_help(self):
        """显示帮助信息"""
        help_text = """
        可用命令:
          help      - 显示此帮助信息
          tools     - 列出所有可用工具
          skills    - 列出所有可用技能
          history   - 显示任务历史
          quit/exit - 退出程序

        示例任务:
          - "读取 /etc/hosts 文件"
          - "在当前目录执行 ls -la 命令"
          - "获取贵州茅台(600519)的股票数据"
          - "创建Python脚本文件 test.py"
        """
        print(help_text)

    async def _list_tools(self):
        """列出所有工具"""
        tools = await self.tool_manager.fetch_tools()
        categories = self.tool_manager.get_tool_by_category()

        print("\n可用工具分类:")
        for category, tool_names in categories.items():
            print(f"\n{category}:")
            for tool_name in tool_names:
                for tool in tools:
                    if tool.name == tool_name:
                        print(f"  - {tool.name}: {tool.description}")
                        break

    def _list_skills(self):
        """列出所有技能"""
        skills = self.skill_manager.list_skills()
        print("\n可用技能:")
        for name, desc in skills.items():
            print(f"  - {name}: {desc}")

    async def _show_history(self):
        """显示历史记录"""
        history = await self.state_manager.get_history()
        if not history:
            print("暂无历史记录")
            return

        print("\n任务历史:")
        for i, task in enumerate(history[-10:], 1):  # 显示最近10条
            print(f"{i}. {task['input'][:50]}...")

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="DevOps智能代理")
    parser.add_argument("--task", type=str, help="直接执行的任务")
    parser.add_argument("--skill", type=str, help="指定使用的技能")
    parser.add_argument("--interactive", action="store_true", help="交互模式")

    args = parser.parse_args()

    # 创建代理实例
    agent = DevOpsAgent()

    # 初始化
    if not await agent.initialize():
        print("初始化失败，退出程序")
        return 1

    # 执行模式
    if args.task:
        # 单任务模式
        result = await agent.process_task(args.task, args.skill)
        print(result)

    elif args.interactive or (not args.task and not args.skill):
        # 交互模式
        await agent.interactive_mode()

    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))