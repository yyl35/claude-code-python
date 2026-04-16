"""DevOps智能代理系统"""

# 基础配置总是可导入的
from .config import config

# 其他模块可能依赖外部包，使用延迟导入或try-except
__all__ = [
    "config",
    "MCPToolManager",
    "TaskParser",
    "SkillManager",
    "BaseSkill",
    "AgentExecutor",
    "StateManager",
    "DevOpsAgent"
]

# 延迟导入函数
def __getattr__(name):
    if name == "MCPToolManager":
        from .tool_manager import MCPToolManager
        return MCPToolManager
    elif name == "TaskParser":
        from .task_parser import TaskParser
        return TaskParser
    elif name == "SkillManager":
        from .skill_manager import SkillManager
        return SkillManager
    elif name == "BaseSkill":
        from .skill_manager import BaseSkill
        return BaseSkill
    elif name == "AgentExecutor":
        from .agent_executor import AgentExecutor
        return AgentExecutor
    elif name == "StateManager":
        from .state_manager import StateManager
        return StateManager
    elif name == "DevOpsAgent":
        from .main import DevOpsAgent
        return DevOpsAgent
    else:
        raise AttributeError(f"module 'src' has no attribute '{name}'")

__version__ = "0.1.0"