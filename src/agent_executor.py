from typing import List, Dict, Any, Callable, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import asyncio
import json
import re
from .task_parser import TaskParser

class AgentExecutor:
    """代理执行引擎（简化版，支持工具结果总结）"""

    def __init__(self, config, tool_manager, skill_manager):
        self.config = config
        self.tool_manager = tool_manager
        self.skill_manager = skill_manager
        self.llm = ChatOpenAI(
            api_key=config.openai_api_key,
            base_url=config.openai_base_url,
            model_name=config.model_name,
            temperature=0.3  # 提高温度以获得更好的创造性
        )
        self.task_parser = TaskParser(self.llm)
        self.tools = []
        self.max_iterations = config.max_iterations

    async def initialize(self):
        """初始化代理"""
        # 获取工具
        self.tools = await self.tool_manager.fetch_tools()

        # 创建绑定工具的LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        print(f"[OK] 代理执行器初始化完成，加载了 {len(self.tools)} 个工具")

    async def execute_direct(self, user_input: str, thread_id: str = "default") -> str:
        """直接执行用户输入，使用工具并总结结果"""
        if not self.tools:
            await self.initialize()

        # 系统提示词，强调要总结工具结果
        system_prompt = """你是一个DevOps智能助手，可以帮助用户完成各种任务。

        如果问题和金融，股票先用get_latest_trading_date获取最新交易日期，再用normalize_stock_code标准化用户提到的股票代码

        重要指令：
        1. 查数据的问题必须调用工具来获取真实数据，不能凭空编造或假设信息
        2. 当用户询问股票、文件、系统状态等信息时，必须调用相应的工具获取实际数据
        3. 当你使用工具获取数据后，必须对结果进行总结和分析，不要直接返回原始数据
        4. 对于表格数据，提取关键信息，分析趋势，给出有意义的见解
        5. 对于股票数据，分析价格变化、交易量、关键指标等
        6. 对于文件内容，总结主要内容，指出关键点
        7. 对于命令执行结果，解释输出含义

        股票数据工具使用说明：
        - 股票代码格式：sh.600095（上海），sz.000001（深圳）
        - adjust_flag参数：'1'（前复权），'2'（后复权），'3'（不复权）
        - 默认使用不复权数据（adjust_flag='3'）
        - 对于股票查询，需要先搜索公司名称对应的股票代码，然后获取历史数据
        - 当用户询问股票价格时，你必须调用股票数据工具获取实际数据，不能凭空回答

        工具调用策略（必须遵守）：
        1. 如果 search_stocks 返回股票代码，调用 normalize_stock_code 标准化代码
        2. 使用获取的数据进行分析和回答
        3. 绝对不能凭空回答股票信息，必须调用工具获取实际数据

        PowerShell命令使用说明：
        1. 在Windows上执行PowerShell命令时，必须使用正确的格式
        2. 对于复杂的PowerShell命令，应该使用 -Command 参数
        3. 正确格式：powershell -Command "Get-PSDrive -PSProvider FileSystem | Select-Object Name, Used, Free"
        4. 错误格式：powershell Get-PSDrive -PSProvider FileSystem | Select-Object Name, Used, Free
        5. 对于包含特殊字符的命令，确保正确转义

        文件操作工具：
        - 使用 read_file 工具读取文件内容
        - 使用 write_file 工具写入文件
        - 使用 list_files 工具列出目录内容
        - 使用 delete_file 工具删除文件

        命令执行工具：
        - 使用 execute_shell_command 工具执行系统命令
        - 使用 run_script 工具运行脚本

        始终用清晰、易懂的语言回复用户，提供有价值的分析而不仅仅是原始数据。

        问题解决策略：
        1. 如果发现缺少依赖库（如ModuleNotFoundError: No module named 'matplotlib'），应该主动调用工具安装
        2. 使用execute_shell_command工具执行pip安装命令
        3. 安装完成后，重新尝试执行原始任务
        4. 如果用户请求运行程序或脚本，确保先检查并安装必要的依赖

        示例：
        用户：运行这个Python程序
        代理：发现缺少matplotlib库 → 执行pip install matplotlib → 重新运行程序 → 返回结果

        用户：湘财证券的股票价格
        代理：
              1. 调用 normalize_stock_code 标准化搜索到的股票代码
              2. 调用 get_historical_k_data 获取当前时间的K线数据
              3. 分析数据并回答

        用户：读取/etc/hosts文件
        代理：1. 调用 read_file 工具读取文件内容
              2. 总结文件内容并回答

        绝对不能做的事情：
        1. 不能凭空编造股票信息
        2. 不能假设文件内容而不实际读取
        3. 不能猜测系统状态而不执行命令
        4. 必须调用工具获取真实数据

        复合任务处理指导：
        当用户任务包含多个步骤时（如"获取数据并写代码"或"写代码并运行测试"），你必须：
        1. 识别任务包含多个部分
        2. 按顺序执行所有步骤，不要只执行第一部分就说"下一步"
        3. 每个步骤都要调用相应的工具获取真实数据或执行实际操作
        4. 完成所有步骤后才返回最终总结

        常见复合任务模式：
        1. 数据获取 + 代码开发：先获取数据，然后根据数据编写代码
        2. 代码开发 + 测试执行：先创建代码文件，然后运行测试
        3. 文件操作 + 数据分析：先读取文件，然后分析内容
        4. 系统检查 + 报告生成：先执行命令检查系统，然后生成报告

        复合任务处理示例：
        用户："去/data2/calcmdd写一个计算最大回撤的代码，用工具拿一个月测试数据，需要运行测试"
        正确做法：
          1. 调用股票数据工具获取一个月测试数据
          2. 分析数据结果，总结关键信息
          3. 调用文件操作工具在/data2/calcmdd创建最大回撤计算代码
          4. 调用命令执行工具运行测试
          5. 返回完整的处理结果

        错误做法：
          1. 只获取数据就说"下一步：创建代码"
          2. 没有实际创建代码文件
          3. 没有运行测试

        重要：如果你不确定要调用哪个工具，请先思考用户需要什么数据，然后调用相应的工具。不要在没有调用工具的情况下回答问题。

        执行流程控制（走一步看一步）：
        1. 你完全控制执行流程，像人类助手一样思考
        2. 每一步都基于当前结果决定下一步做什么
        3. 不要预先计划所有步骤，而是根据实际情况调整
        4. 当你认为任务完成时，直接给出最终答案
        5. 不要等待系统提示，你自己判断何时结束

        思考过程示例：
        用户："创建一个计算最大回撤的脚本并用实际数据测试"

        第一步：获取数据
        - 思考：需要股票数据来测试 → 调用股票数据工具
        - 结果：获取到数据，分析数据质量

        第二步：创建脚本
        - 思考：有了数据，现在需要创建脚本 → 调用文件操作工具
        - 结果：脚本创建成功，检查脚本内容

        第三步：测试脚本
        - 思考：脚本已创建，需要测试 → 调用命令执行工具运行测试
        - 结果：测试通过，分析测试结果

        第四步：提供使用信息（关键步骤！）
        - 思考：用户需要知道文件在哪里、如何使用 → 检查文件位置，提供具体路径和使用方法
        - 结果：告诉用户完整的文件位置和访问方式

        第五步：总结
        - 思考：所有步骤完成，用户知道如何使用 → 给出最终答案

        关键：每一步都基于上一步的结果决定下一步，不要预先计划所有步骤。

        特别注意：当创建文件时，必须告诉用户文件的具体位置和访问方法。不要假设用户知道文件在哪里。

        文件操作后的必要步骤：
        1. 创建文件后，立即检查文件是否成功创建
        2. 获取文件的完整路径
        3. 在回复中明确告诉用户文件位置
        4. 提供具体的访问命令（如 cd、ls、cat 等）
        5. 如果可能，提供运行示例

        错误做法：只说"文件已创建"，不说在哪里
        正确做法："文件已创建在 /path/to/file.py，您可以使用 cd /path/to/ 然后 python file.py 运行"

        处理大文件/大数据时的具体操作指南：
        1. 对于日志文件（如/var/log/syslog），不要使用 read_file 工具读取全部内容
        2. 使用 execute_shell_command 工具执行以下命令：
           - 查看最后100行：`tail -n 100 /var/log/syslog`
           - 查看错误日志：`grep -i error /var/log/syslog | tail -n 50`
           - 查看今天日志：`grep "$(date '+%b %d')" /var/log/syslog | tail -n 50`
           - 查看文件大小：`ls -lh /var/log/syslog`
        3. 如果遇到"413 Request Entity Too Large"错误，立即停止当前方法，改用上述简化命令
        4. 对于大数据集，先获取样本（如前100行）或摘要

        动态调整策略：
        1. 如果工具执行失败，立即分析失败原因，尝试其他方法
        2. 如果数据太大，立即改用 head、tail、grep 等简化命令
        3. 如果用户请求不明确，主动询问澄清
        4. 始终基于当前结果决定下一步，不要固执于原计划
        5. 如果卡住超过1分钟，主动停止并报告问题

        调试和反馈：
        1. 在执行每个步骤时，简要说明你在做什么
        2. 如果遇到问题，解释问题原因和你的解决方案
        3. 不要长时间卡住而不给用户反馈"""

        # 初始化消息
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_input)
        ]

        try:
            tool_results = []
            iteration = 0
            has_required_tools = False

            # 完全由模型判断是否调用工具，不进行正则匹配
            requires_stock_tools = False
            requires_file_tools = False
            requires_command_tools = False

            while iteration < self.max_iterations:
                iteration += 1
                print(f"[调试] 第 {iteration} 次迭代，用户输入: {user_input[:100]}...")

                # 获取模型响应
                response = await self.llm_with_tools.ainvoke(messages)
                tool_calls = getattr(response, 'tool_calls', [])

                # 打印模型响应摘要
                if response.content:
                    print(f"[调试] 模型响应内容: {response.content[:200]}...")
                else:
                    print(f"[调试] 模型无内容响应")

                # 如果没有工具调用，检查是否有最终答案
                if not tool_calls:
                    print(f"[调试] 没有工具调用")

                    # 检查响应是否包含最终答案
                    if response.content and len(response.content) > 10:
                        print(f"[调试] 模型给出了最终答案，返回结果")
                        return response.content
                    else:
                        # 如果没有内容，继续处理
                        print(f"[调试] 模型无内容或内容过短，继续处理")
                        continue

                print(f"[调试] 发现 {len(tool_calls)} 个工具调用")

                # 执行所有工具调用
                for tool_call in tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']

                    print(f"[调试] 执行工具: {tool_name}, 参数: {tool_args}")

                    # 执行工具
                    result = await self._execute_tool(tool_name, tool_args)

                    # 调试：打印工具结果长度
                    print(f"[调试] 工具 {tool_name} 结果长度: {len(str(result))}")
                    if len(str(result)) < 100:
                        print(f"[调试] 工具结果预览: {str(result)[:200]}")
                    else:
                        print(f"[调试] 工具结果预览: {str(result)[:200]}...")

                    # 创建结果摘要
                    summary = self._create_tool_result_summary(tool_name, result)

                    tool_results.append({
                        "tool": tool_name,
                        "args": tool_args,
                        "result": result,
                        "summary": summary
                    })

                    # 添加工具消息到对话历史
                    messages.append(response)  # 模型的工具调用请求
                    messages.append(ToolMessage(
                        content=result,
                        name=tool_name,
                        tool_call_id=tool_call['id']
                    ))

                # 检查模型是否已经给出了最终答案（没有工具调用且有内容）
                if not tool_calls and response.content and len(response.content) > 10:
                    print(f"[调试] 模型给出了最终答案，返回结果")
                    return response.content

            # 如果达到最大迭代次数仍未返回，返回当前结果
            return f"达到最大迭代次数({self.max_iterations})，处理结果：\n{self._create_summary_request(tool_results)}"

        except Exception as e:
            return f"执行过程中出错: {str(e)}"

    async def _execute_tool(self, tool_name: str, params: Dict[str, Any]) -> str:
        """执行单个工具"""
        # 查找工具
        target_tool = None
        for tool in self.tools:
            if tool.name == tool_name:
                target_tool = tool
                break

        if not target_tool:
            return f"未找到工具: {tool_name}"

        try:
            # 执行工具
            result = await target_tool.coroutine(**params)
            result_str = str(result)

            # 检查是否有缺少依赖的错误
            if "ModuleNotFoundError" in result_str or "No module named" in result_str:
                # 提取缺少的模块名
                import re
                module_match = re.search(r"No module named ['\"]([^'\"]+)['\"]", result_str)
                if module_match:
                    missing_module = module_match.group(1)
                    # 返回特殊标记，让代理知道需要安装依赖
                    return f"[DEPENDENCY_MISSING] 缺少依赖库: {missing_module}\n原始错误: {result_str}"

            return result_str
        except Exception as e:
            return f"工具 '{tool_name}' 执行失败: {str(e)}"

    def _create_tool_result_summary(self, tool_name: str, result: str) -> str:
        """创建工具结果摘要"""
        # 根据工具类型创建不同的摘要
        if "stock" in tool_name.lower() or "k_data" in tool_name.lower():
            return self._summarize_stock_data(result)
        elif "file" in tool_name.lower():
            return self._summarize_file_content(result)
        elif "command" in tool_name.lower() or "execute" in tool_name.lower():
            return self._summarize_command_output(result)
        else:
            # 通用摘要：截取前500字符
            return result[:500] + ("..." if len(result) > 500 else "")

    def _should_summarize(self, tool_results: List[Dict[str, Any]], user_input: str = "") -> bool:
        """判断是否应该请求总结（完全由模型判断，不自动触发）"""
        # 这个方法现在只用于达到最大迭代次数时的强制总结
        # 正常流程中，应该由模型自己决定何时结束
        return False

    def _create_summary_request(self, tool_results: List[Dict[str, Any]]) -> str:
        """创建总结请求"""
        if not tool_results:
            return "请继续回答用户的问题。"

        # 构建工具结果摘要
        summaries = []
        for i, tr in enumerate(tool_results, 1):
            tool_name = tr["tool"]
            summary = tr.get("summary", "无摘要")
            summaries.append(f"工具 {i} ({tool_name}): {summary}")

        summary_text = "\n".join(summaries)

        # 检查是否有命令执行
        has_command = any("command" in tr["tool"].lower() or "execute" in tr["tool"].lower() for tr in tool_results)

        if has_command:
            return f"""我已经执行了以下命令并获得了结果：

{summary_text}

请分析这些命令执行结果，给出全面、易懂的总结：
1. 如果命令执行成功，总结输出内容，提取关键信息
2. 如果命令执行失败，解释失败原因，给出建议
3. 用清晰、友好的语言直接回答用户的原始问题
4. 对于磁盘空间查询，总结各驱动器的使用情况
5. 对于系统命令，解释输出含义

不要简单重复原始输出，而要提供有价值的分析和解释。"""
        else:
            return f"""我已经执行了以下工具并获得了结果：

{summary_text}

请分析这些结果，给出全面、易懂的总结和见解，直接回答用户的原始问题。
不要简单重复原始数据，而要提供有价值的分析和解释。"""

    def _summarize_stock_data(self, result: str) -> str:
        """总结股票数据"""
        try:
            # 提取表格数据的关键信息
            lines = result.split('\n')

            # 查找表格数据
            table_data = []
            for line in lines:
                if '|' in line and '---' not in line:
                    # 表格行
                    cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                    if len(cells) >= 6:  # 至少有日期、代码、开盘、最高、最低、收盘
                        table_data.append(cells)

            if table_data and len(table_data) > 1:
                # 提取关键信息
                headers = table_data[0]
                data_rows = table_data[1:]

                if data_rows:
                    # 获取最新数据
                    latest = data_rows[0]

                    # 尝试提取关键指标
                    summary = f"股票数据包含 {len(data_rows)} 条记录。"

                    # 查找关键列
                    date_idx = next((i for i, h in enumerate(headers) if 'date' in h.lower()), 0)
                    close_idx = next((i for i, h in enumerate(headers) if 'close' in h.lower()), 4)
                    volume_idx = next((i for i, h in enumerate(headers) if 'volume' in h.lower()), 7)

                    if date_idx < len(latest) and close_idx < len(latest):
                        summary += f" 最新记录：日期 {latest[date_idx]}，收盘价 {latest[close_idx]}"

                    # 如果有多个数据点，分析趋势
                    if len(data_rows) > 1:
                        first = data_rows[-1]  # 最旧的数据
                        if date_idx < len(first) and close_idx < len(first):
                            try:
                                latest_price = float(latest[close_idx])
                                first_price = float(first[close_idx])
                                change = ((latest_price - first_price) / first_price) * 100
                                summary += f"，期间变化：{change:.2f}%"
                            except:
                                pass

                    return summary

            # 通用摘要
            return f"股票数据：{len(result)} 字符，包含历史价格信息"

        except Exception as e:
            return f"股票数据解析摘要失败，原始数据长度: {len(result)}"

    def _summarize_file_content(self, result: str) -> str:
        """总结文件内容"""
        lines = result.split('\n')
        line_count = len(lines)
        char_count = len(result)

        if line_count <= 5:
            return f"文件内容：{line_count} 行，{char_count} 字符"
        else:
            return f"文件内容：{line_count} 行，{char_count} 字符，包含文本内容"

    def _summarize_command_output(self, result: str) -> str:
        """总结命令输出"""
        if not result:
            return "命令执行没有输出"

        lines = result.split('\n')
        line_count = len(lines)

        # 尝试解析工具执行器的标准格式
        if "工具 'execute_shell_command' 执行成功:" in result:
            # 提取命令信息
            command = ""
            exit_code = ""
            output = ""
            error = ""

            for i, line in enumerate(lines):
                if "**Command:**" in line:
                    command = line.split("**Command:**")[1].strip().strip("`").strip()
                elif "**Exit code:**" in line:
                    exit_code = line.split("**Exit code:**")[1].strip()
                elif "**Standard Output:**" in line:
                    # 提取标准输出
                    output_lines = []
                    for j in range(i+1, min(i+20, len(lines))):
                        if lines[j].strip() == "```" or "**Standard Error:**" in lines[j]:
                            break
                        output_lines.append(lines[j])
                    output = "\n".join(output_lines)
                elif "**Standard Error:**" in line:
                    # 提取标准错误
                    error_lines = []
                    for j in range(i+1, min(i+20, len(lines))):
                        if lines[j].strip() == "```":
                            break
                        error_lines.append(lines[j])
                    error = "\n".join(error_lines)

            summary = f"命令执行完成，退出码: {exit_code}"
            if command:
                summary += f"，命令: {command[:50]}..."
            if output:
                # 提取输出中的关键信息
                key_info = self._extract_key_command_info(output)
                if key_info:
                    summary += f"，输出包含: {key_info}"
                else:
                    output_lines = output.split('\n')
                    if len(output_lines) <= 5:
                        summary += f"，输出: {output[:100]}..."
                    else:
                        summary += f"，输出行数: {len(output_lines)}"
            if error:
                error_clean = self._clean_encoding_issues(error)
                summary += f"，错误: {error_clean[:100]}..."

            return summary

        # 通用摘要
        if line_count <= 5:
            return f"命令输出：{line_count} 行，内容: {result[:100]}..."
        else:
            # 提取关键信息
            key_lines = []
            for line in lines:
                if any(keyword in line.lower() for keyword in ['error', 'warning', 'failed', 'success', 'total', 'result', 'usage', 'free', 'used', 'disk', 'memory', 'cpu']):
                    key_lines.append(line[:100])

            if key_lines:
                return f"命令输出：{line_count} 行，关键信息: {'; '.join(key_lines[:3])}..."
            else:
                return f"命令输出：{line_count} 行，内容: {result[:100]}..."

    def _extract_key_command_info(self, output: str) -> str:
        """从命令输出中提取关键信息"""
        if not output:
            return ""

        lines = output.split('\n')

        # 如果是表格格式，提取表头和数据
        if any('|' in line and '---' in line for line in lines):
            # 表格格式
            table_lines = [line for line in lines if '|' in line and '---' not in line]
            if table_lines:
                return f"表格数据，{len(table_lines)} 行"

        # 如果是PowerShell Get-PSDrive输出
        if any('UsedGB' in line or 'FreeGB' in line for line in lines):
            # 提取磁盘信息
            disk_info = []
            for line in lines:
                if line.strip() and not line.startswith('-') and not line.startswith('Name'):
                    parts = line.split()
                    if len(parts) >= 3:
                        disk_info.append(f"{parts[0]}: {parts[1]}GB已用, {parts[2]}GB可用")
            if disk_info:
                return f"磁盘空间: {'; '.join(disk_info[:3])}"

        # 如果是df -h输出
        if any('Filesystem' in line or 'Size' in line and 'Used' in line and 'Avail' in line for line in lines):
            return "磁盘使用情况"

        return ""

    def _clean_encoding_issues(self, text: str) -> str:
        """清理编码问题"""
        if not text:
            return text

        # 常见乱码修复
        # '�����ڲ����ⲿ���Ҳ���ǿ����еĳ���' -> '不是内部或外部命令，也不是可运行的程序'
        # 这些是GBK编码的字符被当作UTF-8解码

        try:
            # 尝试用GBK编码再解码
            encoded = text.encode('utf-8', errors='ignore')
            # 尝试用不同编码解码
            for encoding in ['gbk', 'cp936', 'utf-8', 'latin-1']:
                try:
                    decoded = encoded.decode(encoding, errors='strict')
                    # 检查是否包含合理的中文或英文
                    if any('\u4e00' <= char <= '\u9fff' for char in decoded) or any(c.isalpha() for c in decoded):
                        return decoded
                except:
                    continue
        except:
            pass

        # 如果无法修复，尝试简单替换
        replacements = {
            '�����ڲ����ⲿ���Ҳ���ǿ����еĳ���': '不是内部或外部命令，也不是可运行的程序',
            '���������ļ���': '或批处理文件',
            '����': '错误'
        }

        for bad, good in replacements.items():
            if bad in text:
                text = text.replace(bad, good)

        return text[:200]

    async def execute_with_skill(self, user_input: str, skill_name: str) -> str:
        """使用特定技能执行任务"""
        skill = self.skill_manager.get_skill(skill_name)
        if not skill:
            return f"未找到技能: {skill_name}"

        # 创建工具执行器
        async def tool_executor(tool_name: str, params: Dict[str, Any]) -> str:
            tools = await self.tool_manager.fetch_tools()
            for tool in tools:
                if tool.name == tool_name:
                    try:
                        result = await tool.coroutine(**params)
                        return result
                    except Exception as e:
                        return f"工具执行失败: {str(e)}"
            return f"未找到工具: {tool_name}"

        # 执行技能
        return await skill.execute(user_input, tool_executor)

    async def parallel_execute(self, subtasks: List[Dict[str, Any]]) -> List[str]:
        """并行执行多个子任务"""

        async def execute_subtask(subtask: Dict[str, Any]) -> str:
            """执行单个子任务"""
            tool_name = subtask.get("tool")
            params = subtask.get("parameters", {})

            if not tool_name:
                return "子任务未指定工具"

            # 获取并执行工具
            tools = await self.tool_manager.fetch_tools()
            target_tool = None
            for tool in tools:
                if tool.name == tool_name:
                    target_tool = tool
                    break

            if not target_tool:
                return f"未找到工具: {tool_name}"

            try:
                result = await target_tool.coroutine(**params)
                return f"子任务 '{subtask['description']}' 完成: {result}"
            except Exception as e:
                return f"子任务 '{subtask['description']}' 失败: {str(e)}"

        # 并行执行
        tasks = [execute_subtask(subtask) for subtask in subtasks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(f"子任务{i+1}异常: {str(result)}")
            else:
                processed_results.append(result)

        return processed_results