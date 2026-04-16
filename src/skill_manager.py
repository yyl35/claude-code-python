from typing import Dict, List, Any, Callable, Optional
from abc import ABC, abstractmethod
import asyncio

class BaseSkill(ABC):
    """技能基类"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.required_tools: List[str] = []

    @abstractmethod
    async def execute(self, task_description: str, tool_executor: Callable) -> str:
        """执行技能"""
        pass

    def get_requirements(self) -> Dict[str, Any]:
        """获取技能要求"""
        return {
            "name": self.name,
            "description": self.description,
            "required_tools": self.required_tools
        }

class FileOperationsSkill(BaseSkill):
    """文件操作技能"""

    def __init__(self):
        super().__init__(
            name="file_operations",
            description="处理文件创建、读取、写入、删除等操作"
        )
        self.required_tools = ["read_file", "write_file", "list_files", "delete_path", "create_dir"]

    async def execute(self, task_description: str, tool_executor: Callable) -> str:
        """执行文件操作"""
        # 这里可以实现具体的文件操作逻辑
        # 例如：解析任务，决定使用哪个工具
        if "读取" in task_description or "查看" in task_description:
            # 提取文件路径
            return await tool_executor("read_file", {"file_path": "extracted_path"})
        elif "写入" in task_description or "创建" in task_description:
            # 对于创建目录，应该使用create_dir工具
            if "目录" in task_description or "文件夹" in task_description:
                return await tool_executor("create_dir", {"path": "extracted_path"})
            else:
                return await tool_executor("write_file", {"file_path": "extracted_path", "content": "content"})
        elif "删除" in task_description:
            return await tool_executor("delete_path", {"path": "extracted_path"})
        elif "列出" in task_description or "目录" in task_description:
            return await tool_executor("list_files", {"path": "extracted_path"})
        else:
            return "无法识别的文件操作"

class CommandExecutionSkill(BaseSkill):
    """命令执行技能 - 智能工具选择"""

    def __init__(self, llm=None):
        super().__init__(
            name="command_execution",
            description="执行系统命令和脚本（智能工具选择）"
        )
        self.llm = llm
        self.required_tools = ["execute_shell_command"]

    async def execute(self, task_description: str, tool_executor: Callable) -> str:
        """执行命令 - 智能工具选择"""
        if not self.llm:
            # 如果没有LLM，使用简单的启发式规则作为回退
            return await self._execute_with_heuristic(task_description, tool_executor)

        # 使用LLM智能选择工具和命令
        return await self._execute_with_llm(task_description, tool_executor)

    async def _execute_with_heuristic(self, task_description: str, tool_executor: Callable) -> str:
        """使用启发式规则执行命令（原有逻辑）"""
        # 根据任务描述智能选择命令
        command_map = {
            "硬盘空间": "df -h",
            "磁盘空间": "df -h",
            "硬盘使用": "df -h",
            "磁盘使用": "df -h",
            "大文件": "find / -type f -size +100M 2>/dev/null | head -20",
            "大文件情况": "find / -type f -size +100M 2>/dev/null | head -20",
            "大文件查找": "find / -type f -size +100M 2>/dev/null | head -20",
            "内存": "free -h",
            "内存使用": "free -h",
            "内存情况": "free -h",
            "进程": "ps aux --sort=-%cpu | head -10",
            "进程情况": "ps aux --sort=-%cpu | head -10",
            "CPU使用": "top -bn1 | head -20",
            "CPU情况": "top -bn1 | head -20",
            "系统负载": "uptime",
            "负载": "uptime",
            "网络": "netstat -tuln",
            "网络连接": "netstat -tuln",
            "端口": "netstat -tuln",
            "日志": "tail -50 /var/log/syslog",
            "系统日志": "tail -50 /var/log/syslog",
            "错误日志": "tail -50 /var/log/syslog",
        }

        # 查找匹配的命令
        selected_command = None
        for keyword, cmd in command_map.items():
            if keyword in task_description:
                selected_command = cmd
                break

        if selected_command:
            print(f"执行命令: {selected_command}")
            try:
                result = await tool_executor("execute_shell_command", {"command": selected_command})
                return self._format_command_result(result, selected_command, "execute_shell_command")
            except Exception as e:
                return f"命令执行失败: {str(e)}"

        # 如果没有匹配的命令，尝试提取自定义命令
        if "运行" in task_description or "执行" in task_description or "检查" in task_description:
            # 这里可以添加更复杂的命令提取逻辑
            # 暂时返回一个通用的系统检查命令
            print("执行系统检查命令")
            try:
                # 执行多个系统检查命令
                commands = [
                    "df -h",
                    "free -h",
                    "uptime"
                ]
                results = []
                for cmd in commands:
                    raw_result = await tool_executor("execute_shell_command", {"command": cmd})
                    formatted_result = self._format_command_result(raw_result, cmd, "execute_shell_command")
                    results.append(f"命令: {cmd}\n{formatted_result}\n")
                return "\n".join(results)
            except Exception as e:
                return f"系统检查失败: {str(e)}"

        return "未指定命令"

    def _format_command_result(self, result: str, command: str, tool_name: str) -> str:
        """格式化命令执行结果"""
        if not result:
            return "命令执行没有返回结果"

        # 尝试修复常见的编码问题
        result = self._fix_encoding_issues(result)

        # 检查是否是工具执行器的标准格式
        if f"工具 '{tool_name}' 执行成功:" in result:
            # 提取实际输出部分
            lines = result.split('\n')
            actual_output_start = -1
            for i, line in enumerate(lines):
                if line.strip().startswith('[') or '**Command:**' in line:
                    actual_output_start = i
                    break

            if actual_output_start != -1:
                # 提取命令输出部分
                output_lines = lines[actual_output_start:]
                result = '\n'.join(output_lines)

        # 格式化输出
        formatted = f"命令执行完成: {command}\n\n"
        formatted += "输出结果:\n"
        formatted += "```\n"
        formatted += result[:2000]  # 限制长度
        if len(result) > 2000:
            formatted += f"\n...(输出过长，已截断，原始长度: {len(result)} 字符)"
        formatted += "\n```"

        return formatted

    def _fix_encoding_issues(self, text: str) -> str:
        """尝试修复编码问题"""
        if not text:
            return text

        # 常见乱码模式修复
        # '�����ڲ����ⲿ���Ҳ���ǿ����еĳ���' -> '不是内部或外部命令，也不是可运行的程序'
        # 实际上这些是GBK编码的字符被当作UTF-8解码产生的乱码

        try:
            # 尝试用不同编码解码
            encodings_to_try = ['gbk', 'utf-8', 'cp936', 'latin-1']

            for encoding in encodings_to_try:
                try:
                    # 如果文本已经是字符串，尝试重新编码再解码
                    encoded = text.encode('latin-1', errors='replace')
                    decoded = encoded.decode(encoding, errors='strict')
                    # 如果解码成功且包含中文字符，返回解码结果
                    if any('\u4e00' <= char <= '\u9fff' for char in decoded):
                        return decoded
                except:
                    continue
        except:
            pass

        # 如果无法修复，返回原始文本
        return text

    async def _execute_with_llm(self, task_description: str, tool_executor: Callable) -> str:
        """使用LLM智能选择工具和命令"""
        from langchain_core.messages import SystemMessage, HumanMessage

        # 定义可用工具及其描述
        tool_descriptions = {
            "execute_shell_command": "执行shell命令并返回输出",
        }

        # 常见命令示例
        command_examples = {
            "系统监控": ["df -h", "free -h", "uptime", "top -bn1"],
            "进程管理": ["ps aux", "ps aux --sort=-%cpu", "ps aux --sort=-%mem"],
            "网络检查": ["netstat -tuln", "ss -tuln", "ping -c 4 google.com"],
            "文件操作": ["ls -la", "find / -type f -size +100M", "du -sh *"],
            "日志查看": ["tail -50 /var/log/syslog", "journalctl -xe", "dmesg | tail -20"],
            "服务管理": ["systemctl status", "service --status-all"],
            "用户管理": ["who", "w", "last"],
            "包管理": ["dpkg -l | head -20", "rpm -qa | head -20", "apt list --installed"],
        }

        # 构建工具选择提示
        tool_list = "\n".join([f"- {name}: {desc}" for name, desc in tool_descriptions.items()])

        example_list = "\n".join([f"- {category}: {', '.join(cmds[:3])}" for category, cmds in command_examples.items()])

        system_prompt = f"""你是一个系统管理员助手。请根据用户的任务描述，选择最合适的工具和命令来执行。

可用工具列表：
{tool_list}

常见命令示例（按类别）：
{example_list}

选择规则：
1. 如果用户请求执行单个命令，使用 execute_command
2. 如果用户请求运行脚本文件，使用 run_script
3. 根据任务描述选择最合适的命令

请返回JSON格式：
{{
    "tool": "工具名称",
    "command": "要执行的命令",
    "reason": "选择理由"
}}

只返回JSON，不要其他内容。"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"用户任务：{task_description}")
        ]

        try:
            # 调用LLM选择工具和命令
            response = await self.llm.ainvoke(messages)

            # 尝试解析JSON响应
            import json
            import re

            # 从响应中提取JSON
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group())
                selected_tool = decision.get("tool", "").strip()
                selected_command = decision.get("command", "").strip()
                reason = decision.get("reason", "").strip()

                print(f"智能选择: 工具={selected_tool}, 命令={selected_command}")
                if reason:
                    print(f"理由: {reason}")

                # 验证工具名称是否有效
                if selected_tool not in tool_descriptions:
                    print(f"LLM返回了无效的工具名称: {selected_tool}，使用启发式规则")
                    return await self._execute_with_heuristic(task_description, tool_executor)

                if not selected_command:
                    print(f"LLM没有返回命令，使用启发式规则")
                    return await self._execute_with_heuristic(task_description, tool_executor)

                # 执行工具
                try:
                    if selected_tool == "execute_shell_command":
                        result = await tool_executor(selected_tool, {"command": selected_command})
                    else:
                        result = await tool_executor(selected_tool, {"command": selected_command})

                    # 格式化命令输出
                    return self._format_command_result(result, selected_command, selected_tool)
                except Exception as e:
                    return f"工具执行失败: {str(e)}"
            else:
                print(f"LLM没有返回有效的JSON，使用启发式规则")
                return await self._execute_with_heuristic(task_description, tool_executor)

        except Exception as e:
            print(f"LLM工具选择失败: {e}，使用启发式规则")
            return await self._execute_with_heuristic(task_description, tool_executor)

class CodeDevelopmentSkill(BaseSkill):
    """代码开发技能"""

    def __init__(self):
        super().__init__(
            name="code_development",
            description="代码文件创建、修改和测试"
        )
        self.required_tools = ["create_file", "modify_code", "run_tests"]

    async def execute(self, task_description: str, tool_executor: Callable) -> str:
        """执行代码开发任务"""
        if "创建代码" in task_description or "新建文件" in task_description:
            return await tool_executor("create_file", {"file_path": "path", "template": "code"})
        elif "修改" in task_description or "编辑" in task_description:
            return await tool_executor("modify_code", {"file_path": "path", "changes": "changes"})
        elif "测试" in task_description:
            return await tool_executor("run_tests", {"test_command": "pytest"})
        return "无法识别的代码开发任务"


class DataFetchingSkill(BaseSkill):
    """数据获取技能 - 智能工具选择"""

    def __init__(self, llm=None):
        super().__init__(
            name="data_fetching",
            description="获取股票数据、市场数据等（智能工具选择）"
        )
        self.llm = llm
        # 列出所有可能的数据获取工具
        self.required_tools = [
            "get_historical_k_data",
            "get_stock_basic_info",
            "get_dividend_data",
            "get_adjust_factor_data",
            "get_profit_data",
            "get_operation_data",
            "get_growth_data",
            "get_balance_data",
            "get_cash_flow_data",
            "get_dupont_data",
            "get_performance_express_report",
            "get_forecast_report",
            "get_fina_indicator",
            "get_stock_industry",
            "get_sz50_stocks",
            "get_hs300_stocks",
            "get_zz500_stocks",
            "get_index_constituents",
            "list_industries",
            "get_industry_members",
            "get_trade_dates",
            "get_all_stock",
            "search_stocks",
            "get_suspensions",
            "get_deposit_rate_data",
            "get_loan_rate_data",
            "get_required_reserve_ratio_data",
            "get_money_supply_data_month",
            "get_money_supply_data_year",
            "get_latest_trading_date",
            "get_market_analysis_timeframe",
            "is_trading_day",
            "previous_trading_day",
            "next_trading_day",
            "get_last_n_trading_days",
            "get_recent_trading_range",
            "get_month_end_trading_dates",
            "get_stock_analysis",
            "normalize_stock_code",
            "normalize_index_code",
            "list_tool_constants"
        ]

    async def execute(self, task_description: str, tool_executor: Callable) -> str:
        """执行数据获取任务 - 智能工具选择"""
        if not self.llm:
            # 如果没有LLM，使用简单的启发式规则作为回退
            return await self._execute_with_heuristic(task_description, tool_executor)

        # 使用LLM智能选择工具
        return await self._execute_with_llm(task_description, tool_executor)

    async def _execute_with_heuristic(self, task_description: str, tool_executor: Callable) -> str:
        """使用启发式规则执行任务（原有逻辑）"""
        # 提取股票代码
        stock_code = self._extract_stock_code(task_description)

        # 简单的启发式规则：根据任务描述选择工具
        if ("最新" in task_description or "实时" in task_description or "当前" in task_description or "今日" in task_description) and \
           ("价格" in task_description or "行情" in task_description or "报价" in task_description or "收盘价" in task_description or "开盘价" in task_description):
            # 获取最新价格数据 - 使用最近30天的数据
            import datetime
            end_date = datetime.datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
            result = await tool_executor("get_historical_k_data", {"code": stock_code, "frequency": "d", "start_date": start_date, "end_date": end_date})
            return self._format_result_with_data_check(result, stock_code, "近期价格数据")

        elif "历史" in task_description or "K线" in task_description:
            result = await tool_executor("get_historical_k_data", {"code": stock_code, "frequency": "d", "start_date": "2023-01-01", "end_date": "2023-12-31"})
            return self._format_result_with_data_check(result, stock_code, "历史K线数据")

        elif "分红" in task_description:
            result = await tool_executor("get_dividend_data", {"code": stock_code, "year": "2023"})
            return self._format_result_with_data_check(result, stock_code, "分红数据")

        elif "财务报告" in task_description or "业绩报告" in task_description or "业绩快报" in task_description:
            # 使用财务指标工具获取财务报告
            import datetime

            # 先尝试查询最近5年的数据
            current_year = datetime.datetime.now().year
            result = None

            # 从当前年份往前查询，最多查询5年
            for year_offset in range(0, 5):
                target_year = current_year - year_offset
                start_date = f"{target_year}-01-01"
                end_date = f"{target_year}-12-31"

                result = await tool_executor("get_fina_indicator", {"code": stock_code, "start_date": start_date, "end_date": end_date})

                # 检查结果是否有数据
                if not self._is_result_empty(result):
                    # 提取并格式化最新的财务数据
                    formatted_result = self._extract_latest_financial_data(result, stock_code, target_year)
                    if formatted_result:
                        return formatted_result
                    break

            # 如果所有年份都为空，返回原始结果
            return self._format_result_with_data_check(result, stock_code, "财务报告")

        elif "财务" in task_description or "指标" in task_description:
            result = await tool_executor("get_fina_indicator", {"code": stock_code, "start_date": "2023-01-01", "end_date": "2023-12-31"})
            return self._format_result_with_data_check(result, stock_code, "财务指标")

        elif "行业" in task_description:
            result = await tool_executor("get_stock_industry", {"code": stock_code})
            return self._format_result_with_data_check(result, stock_code, "行业分类")

        elif "基本" in task_description or "信息" in task_description:
            result = await tool_executor("get_stock_basic_info", {"code": stock_code})
            return self._format_result_with_data_check(result, stock_code, "基本信息")

        elif "股票" in task_description and ("数据" in task_description or "获取" in task_description):
            # 默认使用股票基本信息
            result = await tool_executor("get_stock_basic_info", {"code": stock_code})
            return self._format_result_with_data_check(result, stock_code, "股票数据")

        else:
            # 默认使用股票基本信息
            result = await tool_executor("get_stock_basic_info", {"code": stock_code})
            return self._format_result_with_data_check(result, stock_code, "股票数据")

    async def _execute_with_llm(self, task_description: str, tool_executor: Callable) -> str:
        """使用LLM智能选择工具执行任务"""
        from langchain_core.messages import SystemMessage, HumanMessage

        # 提取股票代码
        stock_code = self._extract_stock_code(task_description)

        # 定义可用工具及其描述
        tool_descriptions = {
            "get_historical_k_data": "获取股票历史K线数据（开盘价、收盘价、最高价、最低价、成交量等）",
            "get_stock_basic_info": "获取股票基本信息（名称、上市日期、状态等）",
            "get_fina_indicator": "获取财务指标数据（ROE、净利率、净利润、每股收益等）",
            "get_dividend_data": "获取分红数据",
            "get_stock_industry": "获取股票行业分类信息",
            "get_performance_express_report": "获取业绩快报",
            "get_forecast_report": "获取业绩预告",
            "get_profit_data": "获取盈利能力数据",
            "get_operation_data": "获取运营能力数据",
            "get_growth_data": "获取成长能力数据",
            "get_balance_data": "获取资产负债表数据",
            "get_cash_flow_data": "获取现金流量表数据",
            "get_adjust_factor_data": "获取复权因子数据",
            "get_sz50_stocks": "获取上证50成分股",
            "get_hs300_stocks": "获取沪深300成分股",
            "get_zz500_stocks": "获取中证500成分股",
            "get_index_constituents": "获取指数成分股",
            "get_trade_dates": "获取交易日历",
            "get_all_stock": "获取所有股票列表",
            "get_latest_trading_date": "获取最新交易日",
            "get_stock_analysis": "获取股票分析报告"
        }

        # 构建工具选择提示
        tool_list = "\n".join([f"- {name}: {desc}" for name, desc in tool_descriptions.items()])

        system_prompt = f"""你是一个股票数据分析专家。请根据用户的任务描述，选择最合适的工具来获取数据。

可用工具列表：
{tool_list}

选择规则：
1. 如果用户请求价格、行情、K线数据，使用 get_historical_k_data
2. 如果用户请求财务数据、财务指标、财务报告，使用 get_fina_indicator
3. 如果用户请求股票基本信息，使用 get_stock_basic_info
4. 如果用户请求行业信息，使用 get_stock_industry
5. 如果用户请求分红数据，使用 get_dividend_data
6. 如果用户请求业绩快报，使用 get_performance_express_report
7. 如果用户请求业绩预告，使用 get_forecast_report

请只返回工具名称，不要其他内容。"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"用户任务：{task_description}")
        ]

        try:
            # 调用LLM选择工具
            response = await self.llm.ainvoke(messages)
            selected_tool = response.content.strip()

            # 验证工具名称是否有效
            if selected_tool not in tool_descriptions:
                # 如果LLM返回了无效的工具，使用启发式规则
                print(f"LLM返回了无效的工具名称: {selected_tool}，使用启发式规则")
                return await self._execute_with_heuristic(task_description, tool_executor)

            print(f"智能选择工具: {selected_tool}")

            # 根据选择的工具准备参数
            params = {"code": stock_code}

            if selected_tool == "get_historical_k_data":
                import datetime
                if "最近一个月" in task_description or "最近30天" in task_description:
                    end_date = datetime.datetime.now().strftime("%Y-%m-%d")
                    start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
                elif "最新" in task_description or "实时" in task_description or "当前" in task_description:
                    end_date = datetime.datetime.now().strftime("%Y-%m-%d")
                    start_date = (datetime.datetime.now() - datetime.timedelta(days=90)).strftime("%Y-%m-%d")
                else:
                    # 默认获取最近一年的数据
                    end_date = datetime.datetime.now().strftime("%Y-%m-%d")
                    start_date = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime("%Y-%m-%d")

                params.update({
                    "frequency": "d",
                    "start_date": start_date,
                    "end_date": end_date
                })

            elif selected_tool == "get_fina_indicator":
                import datetime
                current_year = datetime.datetime.now().year
                # 尝试查询最近5年的数据
                for year_offset in range(0, 5):
                    target_year = current_year - year_offset
                    start_date = f"{target_year}-01-01"
                    end_date = f"{target_year}-12-31"

                    result = await tool_executor(selected_tool, {"code": stock_code, "start_date": start_date, "end_date": end_date})

                    if not self._is_result_empty(result):
                        # 提取并格式化最新的财务数据
                        formatted_result = self._extract_latest_financial_data(result, stock_code, target_year)
                        if formatted_result:
                            return formatted_result
                        break

                # 如果所有年份都为空，返回原始结果
                return self._format_result_with_data_check(result, stock_code, "财务指标")

            elif selected_tool == "get_dividend_data":
                import datetime
                current_year = datetime.datetime.now().year
                params["year"] = str(current_year)

            elif selected_tool in ["get_performance_express_report", "get_forecast_report"]:
                import datetime
                end_date = datetime.datetime.now().strftime("%Y-%m-%d")
                start_date = (datetime.datetime.now() - datetime.timedelta(days=1095)).strftime("%Y-%m-%d")
                params.update({
                    "start_date": start_date,
                    "end_date": end_date
                })

            # 执行工具
            result = await tool_executor(selected_tool, params)

            # 根据工具类型确定数据类型
            data_type_map = {
                "get_historical_k_data": "价格数据",
                "get_stock_basic_info": "基本信息",
                "get_fina_indicator": "财务指标",
                "get_dividend_data": "分红数据",
                "get_stock_industry": "行业分类",
                "get_performance_express_report": "业绩快报",
                "get_forecast_report": "业绩预告",
                "get_profit_data": "盈利能力数据",
                "get_operation_data": "运营能力数据",
                "get_growth_data": "成长能力数据",
                "get_balance_data": "资产负债表数据",
                "get_cash_flow_data": "现金流量表数据"
            }

            data_type = data_type_map.get(selected_tool, "股票数据")
            return self._format_result_with_data_check(result, stock_code, data_type)

        except Exception as e:
            print(f"LLM工具选择失败: {e}，使用启发式规则")
            return await self._execute_with_heuristic(task_description, tool_executor)

    def _extract_stock_code(self, task_description: str) -> str:
        """从任务描述中提取股票代码"""
        # 常见股票映射
        stock_map = {
            "贵州茅台": "sh.600519",
            "茅台": "sh.600519",
            "600519": "sh.600519",
            "中国平安": "sh.601318",
            "平安": "sh.601318",
            "601318": "sh.601318",
            "招商银行": "sh.600036",
            "招行": "sh.600036",
            "600036": "sh.600036",
            "宁德时代": "sz.300750",
            "宁德": "sz.300750",
            "300750": "sz.300750",
            "腾讯": "hk.00700",
            "阿里巴巴": "hk.09988",
            "阿里": "hk.09988",
        }

        # 检查是否包含映射中的关键词
        for name, code in stock_map.items():
            if name in task_description:
                return code

        # 尝试提取股票代码，支持格式：600095、sh.600095、600095.sh、sz.300750等
        import re

        # 模式1: 数字代码后跟.sh或.sz（如600095.sh）
        match = re.search(r'(\d{6})\.(sh|sz)', task_description, re.IGNORECASE)
        if match:
            code = match.group(1)
            market = match.group(2).lower()
            return f"{market}.{code}"

        # 模式2: sh.或sz.后跟数字代码（如sh.600095）
        match = re.search(r'(sh|sz)\.(\d{6})', task_description, re.IGNORECASE)
        if match:
            market = match.group(1).lower()
            code = match.group(2)
            return f"{market}.{code}"

        # 模式3: 纯6位数字代码
        match = re.search(r'(\d{6})', task_description)
        if match:
            code = match.group(1)
            # 判断是沪市还是深市
            if code.startswith('6'):
                return f"sh.{code}"
            elif code.startswith('0') or code.startswith('3'):
                return f"sz.{code}"
            else:
                return f"sh.{code}"  # 默认

        # 默认返回贵州茅台
        return "sh.600519"

    def _format_result_with_data_check(self, result: str, stock_code: str, data_type: str) -> str:
        """格式化结果并检查数据是否为空"""
        if not result:
            return f"获取 {stock_code} 的{data_type}失败：返回结果为空"

        # 检查结果是否为空
        if self._is_result_empty(result):
            # 检查是否有错误信息
            if 'Error:' in result or 'error' in result.lower() or 'empty' in result.lower():
                return f"获取 {stock_code} 的{data_type}：未找到相关数据\n\n原始响应：{result[:500]}..."
            else:
                # 返回原始结果，但添加说明
                return f"获取 {stock_code} 的{data_type}：返回结果中未识别到有效数据\n\n原始响应：{result[:500]}..."

        # 如果是表格数据，尝试进行格式化以提高可读性
        if '|' in result and '---' in result:
            formatted_result = self._format_table_data(result, data_type)
            if formatted_result:
                return formatted_result

        return result

    def _is_result_empty(self, result: str) -> bool:
        """检查结果是否为空"""
        if not result:
            return True

        # 检查常见空结果模式
        empty_patterns = [
            '无数据', '空', 'empty', 'no data', 'not found', 'empty result',
            '0 rows', '0 行', '没有数据'
        ]

        result_lower = result.lower()
        for pattern in empty_patterns:
            if pattern in result_lower:
                return True

        # 检查表格数据行
        lines = result.split('\n')
        data_lines = 0

        for line in lines:
            # 检查是否包含表格数据行（包含竖线字符且不是纯表头）
            if '|' in line:
                # 检查是否可能包含数据（排除纯分隔线或表头）
                # 分隔线通常包含大量的 "-"
                if '----' not in line and '---' not in line:
                    # 检查是否包含数字或日期（可能是数据行）
                    if any(char.isdigit() for char in line):
                        data_lines += 1
                    # 检查是否包含中文文本（可能是数据）
                    elif any('\u4e00' <= char <= '\u9fff' for char in line):
                        data_lines += 1

        # 如果没有任何数据行，则认为是空的
        return data_lines == 0

    def _format_table_data(self, result: str, data_type: str) -> str:
        """格式化表格数据以提高可读性"""
        lines = result.split('\n')

        # 查找表格开始位置
        table_start = -1
        for i, line in enumerate(lines):
            if '|' in line and '---' in line:
                table_start = i
                break

        if table_start == -1:
            return result  # 没有找到表格格式

        # 提取表头行和分隔线
        header_line = lines[table_start-1] if table_start > 0 else ""
        separator_line = lines[table_start]

        # 检查表头行是否包含表格格式
        if '|' not in header_line:
            # 尝试在更早的行中查找表头
            for i in range(table_start-2, max(-1, table_start-5), -1):
                if i >= 0 and '|' in lines[i] and '---' not in lines[i]:
                    header_line = lines[i]
                    break

        # 解析表头
        headers = [h.strip() for h in header_line.split('|') if h.strip()]

        # 如果仍然没有表头，返回原始结果
        if not headers:
            return result

        # 提取数据行
        data_lines = []
        for i in range(table_start + 1, len(lines)):
            line = lines[i]
            if '|' not in line:
                continue
            if '---' in line:  # 跳过分隔线
                continue
            data_lines.append(line)

        if not data_lines:
            return result

        # 根据数据类型进行格式化
        if 'forecast' in data_type.lower() or '财务报告' in data_type or '业绩' in data_type:
            return self._format_financial_forecast_table(header_line, separator_line, data_lines, headers)

        # 默认返回原始结果，但尝试简化长列
        return self._simplify_table_columns(result, headers)

    def _format_financial_forecast_table(self, header_line: str, separator_line: str, data_lines: List[str], headers: List[str]) -> str:
        """格式化财务预测表格为更易读的文本格式"""
        formatted_lines = []

        # 添加标题
        formatted_lines.append("财务预测报告")
        formatted_lines.append("=" * 60)

        for i, line in enumerate(data_lines, 1):
            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            if len(cells) < 6:
                continue

            # 提取关键字段
            pub_date = cells[1] if len(cells) > 1 else ""
            stat_date = cells[2] if len(cells) > 2 else ""
            forecast_type = cells[3] if len(cells) > 3 else ""
            abstract = cells[4] if len(cells) > 4 else ""
            chg_up = cells[5] if len(cells) > 5 else ""
            chg_down = cells[6] if len(cells) > 6 else ""

            # 简化摘要文本
            if len(abstract) > 80:
                abstract = abstract[:80] + "..."

            # 构建格式化行
            formatted_lines.append(f"\n报告 #{i}:")
            formatted_lines.append(f"  发布日: {pub_date}")
            formatted_lines.append(f"  统计期: {stat_date}")
            formatted_lines.append(f"  预测类型: {forecast_type}")
            formatted_lines.append(f"  摘要: {abstract}")

            # 显示变化百分比（如果有）
            if chg_up or chg_down:
                change_info = []
                if chg_up:
                    change_info.append(f"增长上限: {chg_up}%")
                if chg_down:
                    change_info.append(f"增长下限: {chg_down}%")
                if change_info:
                    formatted_lines.append(f"  预期变化: {', '.join(change_info)}")

            formatted_lines.append("-" * 40)

        if not formatted_lines:
            # 如果没有格式化任何行，返回原始表格
            simplified_lines = []
            for line in data_lines:
                cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                if len(cells) >= 5 and len(cells[4]) > 60:
                    cells[4] = cells[4][:60] + "..."
                simplified_line = "| " + " | ".join(cells) + " |"
                simplified_lines.append(simplified_line)
            return "\n".join([header_line, separator_line] + simplified_lines)

        return "\n".join(formatted_lines)

    def _simplify_table_columns(self, result: str, headers: List[str]) -> str:
        """简化表格列宽"""
        lines = result.split('\n')
        formatted_lines = []

        for line in lines:
            if '|' not in line or '---' in line:
                formatted_lines.append(line)
                continue

            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            if len(cells) != len(headers):
                formatted_lines.append(line)
                continue

            # 简化长单元格
            simplified_cells = []
            for cell in cells:
                if len(cell) > 80:
                    simplified_cells.append(cell[:80] + "...")
                else:
                    simplified_cells.append(cell)

            # 重新构建行
            simplified_line = "| " + " | ".join(simplified_cells) + " |"
            formatted_lines.append(simplified_line)

        return "\n".join(formatted_lines)

    def _extract_latest_financial_data(self, result: str, stock_code: str, year: int) -> str:
        """从财务指标结果中提取最新的财务数据"""
        lines = result.split('\n')

        # 查找表格开始位置
        table_start = -1
        for i, line in enumerate(lines):
            if '|' in line and '---' in line:
                table_start = i
                break

        if table_start == -1:
            return None

        # 提取表头行
        header_line = lines[table_start-1] if table_start > 0 else ""

        # 查找表头索引
        headers = [h.strip() for h in header_line.split('|') if h.strip()]
        if not headers:
            return None

        # 确定关键字段的索引
        try:
            year_idx = headers.index("year")
            quarter_idx = headers.index("quarter") if "quarter" in headers else -1
            pub_date_idx = headers.index("profit_pubDate") if "profit_pubDate" in headers else -1
            stat_date_idx = headers.index("profit_statDate") if "profit_statDate" in headers else -1
            roe_avg_idx = headers.index("profit_roeAvg") if "profit_roeAvg" in headers else -1
            np_margin_idx = headers.index("profit_npMargin") if "profit_npMargin" in headers else -1
            net_profit_idx = headers.index("profit_netProfit") if "profit_netProfit" in headers else -1
            eps_idx = headers.index("profit_epsTTM") if "profit_epsTTM" in headers else -1
        except ValueError:
            # 如果没有找到关键字段，返回原始格式的简化版本
            return self._simplify_table_columns(result, headers)

        # 收集所有数据行
        data_rows = []
        for i in range(table_start + 1, len(lines)):
            line = lines[i]
            if '|' not in line or '---' in line:
                continue

            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            if len(cells) < len(headers):
                continue

            data_rows.append({
                "year": cells[year_idx] if year_idx < len(cells) else "",
                "quarter": cells[quarter_idx] if quarter_idx < len(cells) and quarter_idx != -1 else "",
                "pub_date": cells[pub_date_idx] if pub_date_idx < len(cells) and pub_date_idx != -1 else "",
                "stat_date": cells[stat_date_idx] if stat_date_idx < len(cells) and stat_date_idx != -1 else "",
                "roe_avg": cells[roe_avg_idx] if roe_avg_idx < len(cells) and roe_avg_idx != -1 else "",
                "np_margin": cells[np_margin_idx] if np_margin_idx < len(cells) and np_margin_idx != -1 else "",
                "net_profit": cells[net_profit_idx] if net_profit_idx < len(cells) and net_profit_idx != -1 else "",
                "eps": cells[eps_idx] if eps_idx < len(cells) and eps_idx != -1 else "",
                "raw_line": line
            })

        if not data_rows:
            return None

        # 按年份和季度排序（最新的排前面）
        sorted_rows = sorted(data_rows, key=lambda x: (
            int(x["year"]) if x["year"] and x["year"].isdigit() else 0,
            int(x["quarter"]) if x["quarter"] and x["quarter"].isdigit() else 0
        ), reverse=True)

        # 获取最新数据
        latest_row = sorted_rows[0]

        # 构建格式化输出
        formatted_lines = []
        formatted_lines.append(f"股票 {stock_code} - 最新财务数据")
        formatted_lines.append("=" * 60)

        # 添加基本信息
        if latest_row["year"]:
            formatted_lines.append(f"报告年份: {latest_row['year']}")
        if latest_row["quarter"]:
            formatted_lines.append(f"报告季度: Q{latest_row['quarter']}")
        if latest_row["pub_date"]:
            formatted_lines.append(f"发布日期: {latest_row['pub_date']}")
        if latest_row["stat_date"]:
            formatted_lines.append(f"统计截止: {latest_row['stat_date']}")

        formatted_lines.append("\n关键财务指标:")
        formatted_lines.append("-" * 40)

        # 添加财务指标
        if latest_row["roe_avg"]:
            try:
                roe_value = float(latest_row["roe_avg"])
                formatted_lines.append(f"平均净资产收益率(ROE): {roe_value:.2f}%")
            except (ValueError, TypeError):
                formatted_lines.append(f"平均净资产收益率(ROE): {latest_row['roe_avg']}")

        if latest_row["np_margin"]:
            try:
                np_margin_value = float(latest_row["np_margin"])
                formatted_lines.append(f"净利率: {np_margin_value:.2f}%")
            except (ValueError, TypeError):
                formatted_lines.append(f"净利率: {latest_row['np_margin']}")

        if latest_row["net_profit"]:
            try:
                net_profit_value = float(latest_row["net_profit"])
                if abs(net_profit_value) >= 100000000:
                    formatted_value = f"{net_profit_value/100000000:.2f}亿元"
                elif abs(net_profit_value) >= 10000:
                    formatted_value = f"{net_profit_value/10000:.2f}万元"
                else:
                    formatted_value = f"{net_profit_value:.2f}元"
                formatted_lines.append(f"净利润: {formatted_value}")
            except (ValueError, TypeError):
                formatted_lines.append(f"净利润: {latest_row['net_profit']}")

        if latest_row["eps"]:
            try:
                eps_value = float(latest_row["eps"])
                formatted_lines.append(f"每股收益(TTM): {eps_value:.3f}元")
            except (ValueError, TypeError):
                formatted_lines.append(f"每股收益(TTM): {latest_row['eps']}")

        # 如果有多个季度的数据，显示简要概览
        if len(sorted_rows) > 1:
            formatted_lines.append(f"\n其他可用数据: 共 {len(sorted_rows)} 个报告期")
            # 显示最近几个报告期
            for i, row in enumerate(sorted_rows[:3], 1):
                if row["year"] and row["quarter"]:
                    quarter_info = f"{row['year']}年Q{row['quarter']}"
                    if row["net_profit"]:
                        try:
                            profit = float(row["net_profit"])
                            if abs(profit) >= 100000000:
                                profit_str = f"{profit/100000000:.1f}亿"
                            elif abs(profit) >= 10000:
                                profit_str = f"{profit/10000:.1f}万"
                            else:
                                profit_str = f"{profit:.0f}"
                        except:
                            profit_str = row["net_profit"]
                        formatted_lines.append(f"  {i}. {quarter_info}: 净利润 {profit_str}")
                    else:
                        formatted_lines.append(f"  {i}. {quarter_info}")

        return "\n".join(formatted_lines)

class SkillManager:
    """技能管理器"""

    def __init__(self, llm=None):
        self.llm = llm
        self.skills: Dict[str, BaseSkill] = {}
        self._register_default_skills()

    def _register_default_skills(self):
        """注册默认技能"""
        default_skills = [
            FileOperationsSkill(),
            CommandExecutionSkill(self.llm),  # 传递LLM给CommandExecutionSkill
            CodeDevelopmentSkill(),
            DataFetchingSkill(self.llm)  # 传递LLM给DataFetchingSkill
        ]

        for skill in default_skills:
            self.register_skill(skill)

    def register_skill(self, skill: BaseSkill):
        """注册新技能"""
        self.skills[skill.name] = skill

    def get_skill(self, skill_name: str) -> Optional[BaseSkill]:
        """获取技能"""
        return self.skills.get(skill_name)

    def list_skills(self) -> Dict[str, str]:
        """列出所有技能"""
        return {name: skill.description for name, skill in self.skills.items()}

    def get_skills_for_tools(self, available_tools: List[str]) -> List[str]:
        """根据可用工具返回可用的技能"""
        available_skills = []

        for skill_name, skill in self.skills.items():
            # 检查技能所需工具是否都可用
            if all(tool in available_tools for tool in skill.required_tools):
                available_skills.append(skill_name)

        return available_skills