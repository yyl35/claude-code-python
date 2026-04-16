from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os

class AgentConfig(BaseSettings):
    """代理系统配置"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",  # 无前缀
        case_sensitive=False,  # 不区分大小写
        extra="ignore"  # 忽略额外字段
    )

    openai_api_key: str = Field(default="sk-dummy-key", description="OpenAI API密钥")
    openai_base_url: str = Field("https://api.deepseek.com/v1", description="OpenAI API基础URL")
    mcp_server_url: str = Field("http://127.0.0.1:8000/sse", description="MCP服务器URL")
    workspace_path: str = Field("/data2/RD-Agent/qlib/workspace", description="工作空间路径")
    memory_path: str = Field("agent_memory.json", description="内存文件路径")

    # 模型配置
    model_name: str = "deepseek-chat"
    model_temperature: float = 0.1

    # 代理配置
    max_iterations: int = 30  # 增加迭代次数以支持复杂任务
    enable_parallel: bool = True

# 创建配置实例，允许环境变量缺失
try:
    config = AgentConfig()
except Exception as e:
    print(f"Warning: Failed to load config from .env: {e}")
    print("Using default configuration...")
    # 创建默认配置
    config = AgentConfig(
        openai_api_key=os.getenv("OPENAI_API_KEY", "sk-dummy-key"),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1"),
        mcp_server_url=os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000/sse"),
        workspace_path=os.getenv("WORKSPACE_PATH", "/data2/RD-Agent/qlib/workspace"),
        memory_path=os.getenv("MEMORY_PATH", "agent_memory.json"),
    )