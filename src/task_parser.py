from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json

class TaskParser:
    """自然语言任务解析器"""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    async def parse_task(self, user_input: str, available_tools: Dict[str, str]) -> Dict[str, Any]:
        """解析用户任务，返回任务结构"""

        system_prompt = f"""
        你是一个任务解析专家。请分析用户的任务需求，并返回结构化的任务分解。

        可用的工具列表：
        {json.dumps(available_tools, indent=2, ensure_ascii=False)}

        任务分解结构：
        1. 主要任务类型（file_operations, command_execution, code_development, devops, data_analysis）
        2. 子任务列表（每个子任务应明确指定使用的工具）
        3. 执行顺序（sequential 或 parallel）
        4. 预期输出

        请返回JSON格式：
        {{
            "task_type": "任务类型",
            "subtasks": [
                {{
                    "description": "子任务描述",
                    "tool": "使用的工具名称",
                    "parameters": {{"param1": "value1"}},
                    "depends_on": []  # 依赖的子任务索引
                }}
            ],
            "execution_order": "sequential/parallel",
            "expected_output": "预期输出描述"
        }}
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"用户任务：{user_input}")
        ]

        response = await self.llm.ainvoke(messages)

        try:
            # 尝试从响应中提取JSON
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                task_plan = json.loads(json_match.group())
            else:
                # 如果没找到JSON，创建默认任务
                task_plan = {
                    "task_type": "unknown",
                    "subtasks": [{
                        "description": user_input,
                        "tool": None,
                        "parameters": {},
                        "depends_on": []
                    }],
                    "execution_order": "sequential",
                    "expected_output": "完成任务"
                }
        except json.JSONDecodeError:
            # JSON解析失败时的备选方案
            task_plan = {
                "task_type": "direct_execution",
                "subtasks": [{
                    "description": user_input,
                    "tool": None,
                    "parameters": {},
                    "depends_on": []
                }],
                "execution_order": "sequential",
                "expected_output": "完成任务"
            }

        return task_plan

    async def identify_skill(self, user_input: str) -> Optional[str]:
        """识别任务对应的预定义技能"""

        skill_prompt = """
        识别以下任务最适合的预定义技能：

        可用技能：
        1. file_operations - 文件操作（创建、读取、写入、删除文件）
        2. command_execution - 命令执行（运行脚本、系统命令）
        3. code_development - 代码开发（创建代码文件、修改代码）
        4. devops_tasks - 运维任务（部署、监控、日志检查）
        5. data_fetching - 数据获取（获取股票数据、市场数据）
        6. custom_workflow - 自定义工作流

        返回技能名称，如果不匹配任何技能则返回null。
        只返回技能名称或null，不要其他内容。
        """

        messages = [
            SystemMessage(content=skill_prompt),
            HumanMessage(content=f"任务：{user_input}")
        ]

        response = await self.llm.ainvoke(messages)
        skill_name = response.content.strip().lower()

        if skill_name == "null":
            return None
        return skill_name

    async def parse_composite_task(self, user_input: str) -> Dict[str, Any]:
        """解析复合任务为多个子任务"""

        composite_prompt = """
        你是一个任务分解专家。请分析用户的复合任务，将其分解为多个可执行的子任务。

        常见复合任务模式：
        1. 获取数据 + 写代码 + 运行测试
        2. 读取文件 + 分析数据 + 生成报告
        3. 获取股票数据 + 计算指标 + 保存结果
        4. 创建文件 + 写入代码 + 执行测试

        任务分解要求：
        1. 每个子任务必须是具体可执行的
        2. 子任务之间要有逻辑顺序
        3. 标明每个子任务需要使用的工具类型
        4. 子任务描述要清晰明确

        工具类型：
        - data_fetching: 获取数据（股票数据、文件内容等）
        - file_operations: 文件操作（创建、写入、读取文件）
        - code_development: 代码开发（写Python代码、创建脚本）
        - command_execution: 命令执行（运行测试、执行脚本）

        返回JSON格式：
        {
            "is_composite": true,
            "subtasks": [
                {
                    "step": 1,
                    "description": "具体子任务描述",
                    "tool_type": "工具类型",
                    "expected_output": "期望输出"
                }
            ],
            "total_steps": 子任务数量
        }

        如果任务不是复合任务，返回：
        {
            "is_composite": false,
            "subtasks": [],
            "total_steps": 0
        }

        只返回JSON，不要其他内容。
        """

        messages = [
            SystemMessage(content=composite_prompt),
            HumanMessage(content=f"用户任务：{user_input}")
        ]

        try:
            response = await self.llm.ainvoke(messages)

            # 尝试从响应中提取JSON
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                task_plan = json.loads(json_match.group())
                return task_plan
            else:
                # JSON解析失败时的备选方案
                return {
                    "is_composite": False,
                    "subtasks": [],
                    "total_steps": 0
                }
        except json.JSONDecodeError:
            # JSON解析失败
            return {
                "is_composite": False,
                "subtasks": [],
                "total_steps": 0
            }
        except Exception as e:
            print(f"复合任务解析失败: {e}")
            return {
                "is_composite": False,
                "subtasks": [],
                "total_steps": 0
            }