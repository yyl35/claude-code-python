"""配置测试"""

import os
from unittest.mock import patch
from src.config import AgentConfig

def test_config_loading():
    """测试配置加载"""

    # 设置测试环境变量
    test_env = {
        "OPENAI_API_KEY": "test-api-key",
        "OPENAI_BASE_URL": "https://test-api.example.com/v1",
        "MCP_SERVER_URL": "http://test-server:1234/sse",
        "BASE_WORKSPACE": "/test/workspace",
        "MEMORY_PATH": "test_memory.json"
    }

    with patch.dict(os.environ, test_env):
        config = AgentConfig()

        assert config.openai_api_key == "test-api-key"
        assert config.openai_base_url == "https://test-api.example.com/v1"
        assert config.mcp_server_url == "http://test-server:1234/sse"
        assert config.workspace_path == "/test/workspace"
        assert config.memory_path == "test_memory.json"

        # 检查默认值
        assert config.model_name == "deepseek-chat"
        assert config.model_temperature == 0.1
        assert config.max_iterations == 10
        assert config.enable_parallel == True

def test_config_defaults():
    """测试配置默认值"""

    # 只设置必需的环境变量
    test_env = {
        "OPENAI_API_KEY": "test-api-key"
    }

    with patch.dict(os.environ, test_env):
        config = AgentConfig()

        assert config.openai_api_key == "test-api-key"
        assert config.openai_base_url == "https://api.deepseek.com/v1"  # 默认值
        assert config.mcp_server_url == "http://114.67.103.249:7864/sse"  # 默认值
        assert config.workspace_path == "/data2/RD-Agent/qlib/workspace"  # 默认值
        assert config.memory_path == "agent_memory.json"  # 默认值

if __name__ == "__main__":
    test_config_loading()
    test_config_defaults()
    print("所有测试通过！")