# DevOps智能代理系统 (DevOps-Agent)

基于Python的智能代理系统，通过自然语言理解用户需求，动态调用MCP服务器工具完成代码开发和运维任务。

**项目状态**: ✅ 测试通过，可运行

## 特性

- **自然语言接口**：用户用日常语言描述任务
- **动态工具集成**：自动发现和加载MCP服务器工具
- **智能任务分解**：将复杂任务拆解为工具调用序列
- **状态持久化**：支持会话恢复和上下文记忆
- **技能系统**：预定义和自定义的工作流模板
- **多代理协作**：支持并行执行和代理分工

## 系统架构

```
用户输入 → 任务解析与分类器 → 代理编排引擎 → MCP工具管理层 → MCP服务器
```

## 安装

1. 克隆仓库：
```bash
git clone <repository-url>
cd devops-agent
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，设置您的API密钥和其他配置
```

## 使用

### 1. 直接执行任务

```bash
# 读取文件
python -m src.main --task "修改nginx配置，删掉缓存相关配置"

# 执行命令
python -m src.main --task "检查docker镜像，并找出占用硬盘空间大的镜像"

# 获取股票数据
python -m src.main --task "获取贵州茅台(600519)的股票数据"

# 使用特定技能
python -m src.main --task "创建一个计算最大回撤的python脚本，并用真实数据验证" --skill skill_name

# MCP服务器地址已配置为: http://127.0.0.1:8000/sse
```

### 2. 交互模式

```bash
python -m src.main --interactive
```

### 3. Web聊天界面（新增）

```bash
# 启动聊天服务器
python start_chat.py

# 然后在浏览器访问
# http://localhost:8004
```

### 4. 编程方式使用

```python
import asyncio
from devops_agent import DevOpsAgent

async def main():
    # 创建代理
    agent = DevOpsAgent()
    await agent.initialize()
    
    # 执行任务
    result = await agent.process_task("读取 /var/log/syslog 文件")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

## 项目结构

```
devops-agent/
├── src/
│   ├── __init__.py
│   ├── main.py                      # 主入口点
│   ├── config.py                    # 配置管理
│   ├── tool_manager.py              # MCP工具管理
│   ├── agent_executor.py            # 代理执行引擎
│   ├── task_parser.py               # 任务解析器
│   ├── skill_manager.py             # 技能管理系统
│   ├── state_manager.py             # 状态持久化
│   ├── chat_server.py               # 聊天服务器（新增）
│   ├── chat_memory.py               # 聊天记忆管理（新增）
│   ├── skills/                      # 预定义技能
│   │   ├── __init__.py
│   │   ├── file_operations.py       # 文件操作技能
│   │   ├── command_execution.py     # 命令执行技能
│   │   ├── code_development.py      # 代码开发技能
│   │   └── devops_tasks.py          # 运维任务技能
│   └── utils/
│       ├── __init__.py
│       ├── logger.py                # 日志配置
│       └── validation.py            # 输入验证
├── tests/                           # 测试目录
├── examples/                        # 使用示例
├── requirements.txt                 # 依赖列表
├── .env.example                     # 环境变量示例
├── start_chat.py                    # 聊天界面启动脚本（新增）
├── README.md                        # 项目说明
└── README_CHAT.md                   # 聊天界面文档（新增）
```

## 核心组件

### 1. MCP工具管理器 (`tool_manager.py`)
动态从MCP服务器加载工具，包括：
- 文件操作 (`read_file`, `write_file`, `list_files`, `delete_file`)
- 命令执行 (`execute_command`, `run_script`)
- 数据获取 (`get_stock_data`, `get_market_data`)
- 代码开发 (`create_file`, `modify_code`, `run_tests`)

**MCP服务器地址**: `http://127.0.0.1:8000/sse`

### 2. 任务解析器 (`task_parser.py`)
将自然语言任务解析为结构化任务计划：
- 意图识别
- 任务分解
- 技能匹配
- 执行顺序确定

### 3. 技能管理器 (`skill_manager.py`)
预定义和可扩展的工作流模板：
- **文件操作技能**：文件创建、读取、写入、删除
- **命令执行技能**：系统命令和脚本执行
- **代码开发技能**：代码文件创建、修改、测试
- **运维任务技能**：部署、监控、日志检查

### 4. 代理执行引擎 (`agent_executor.py`)
协调任务执行的智能引擎：
- React代理（动态工具调用）
- 技能执行器（预定义工作流）
- 并行执行协调器

### 5. 状态管理器 (`state_manager.py`)
持久化会话状态：
- 任务历史记录
- 执行统计
- 会话恢复

## 扩展指南

### 添加新工具
MCP服务器添加新工具后，系统会自动发现并加载。

### 创建新技能

```python
from skill_manager import BaseSkill

class CustomSkill(BaseSkill):
    """自定义技能"""
    
    def __init__(self):
        super().__init__(
            name="custom_skill",
            description="自定义技能描述",
            required_tools=["tool1", "tool2"]
        )
    
    async def execute(self, task_description: str, tool_executor):
        # 实现技能逻辑
        result1 = await tool_executor("tool1", {"param": "value"})
        result2 = await tool_executor("tool2", {"param": "value"})
        return f"组合结果: {result1}, {result2}"

# 注册技能
skill_manager.register_skill(CustomSkill())
```

### 配置自定义
编辑 `.env` 文件：
```env
OPENAI_API_KEY=sk-your-api-key
OPENAI_BASE_URL=https://api.deepseek.com/v1
MCP_SERVER_URL=http://your-mcp-server:port/sse
BASE_WORKSPACE=/your/workspace
MEMORY_PATH=agent_memory.json
```

## 安全考虑

1. **工具权限控制**：MCP服务器应限制危险命令的执行
2. **输入验证**：所有工具参数都经过Pydantic验证
3. **沙箱环境**：建议在容器中运行敏感操作
4. **访问控制**：MCP服务器应实现身份验证

## 性能优化

1. **工具缓存**：缓存MCP工具列表，减少连接开销
2. **并行执行**：对独立任务使用异步并行执行
3. **结果缓存**：缓存常用操作结果
4. **连接池**：维护MCP连接池

## 聊天界面（新增）

项目现已支持Web聊天界面，提供更友好的用户交互体验。

### 主要特性
- **现代化Web界面**：响应式设计，实时聊天
- **增强记忆功能**：对话历史、会话管理、上下文记忆
- **完整API支持**：WebSocket实时通信，REST API

### 快速使用
```bash
# 启动聊天服务器
python start_chat.py

# 访问Web界面
# http://localhost:8004
```

### 详细文档
- [README_CHAT.md](README_CHAT.md) - 聊天界面完整文档
- [USAGE.md](USAGE.md) - 使用指南和故障排除

## 许可证

MIT