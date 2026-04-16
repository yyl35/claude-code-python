#!/usr/bin/env python3
"""
DevOps Agent聊天界面启动脚本
启动聊天服务器和Web界面
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_environment():
    """设置环境变量"""
    # 检查环境变量文件
    env_file = project_root / ".env"
    if env_file.exists():
        print(f"使用环境变量文件: {env_file}")

        # 读取环境变量
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
                    print(f"  设置: {key.strip()}=****" if "KEY" in key or "SECRET" in key else f"  设置: {key.strip()}={value.strip()}")
    else:
        print("未找到.env文件，使用默认配置")

        # 设置默认值
        defaults = {
            "OPENAI_API_KEY": "sk-dummy-key",
            "OPENAI_BASE_URL": "https://api.deepseek.com/v1",
            "MCP_SERVER_URL": "http://127.0.0.1:8000/sse",
            "WORKSPACE_PATH": "./workspace",
            "MEMORY_PATH": "agent_memory.json"
        }

        for key, value in defaults.items():
            if key not in os.environ:
                os.environ[key] = value
                print(f"  设置默认: {key}={value}")

async def main():
    """主函数"""
    print("=" * 60)
    print("DevOps Agent 聊天界面")
    print("=" * 60)

    # 设置环境
    setup_environment()

    print("\n启动聊天服务器...")

    try:
        # 导入聊天服务器
        from src.chat_server import ChatServer

        # 创建服务器实例
        server = ChatServer()

        # 初始化
        print("初始化服务器...")
        if not await server.initialize():
            print("[错误] 服务器初始化失败")
            return 1

        print("[成功] 服务器初始化成功")
        print("\n" + "=" * 60)
        print("聊天服务器已启动！")
        print("=" * 60)
        print("\n访问地址:")
        print("  [Web] Web界面: http://localhost:8001")
        print("  [健康] 健康检查: http://localhost:8001/api/health")
        print("  [状态] 状态信息: http://localhost:8001/api/status")
        print("\n使用说明:")
        print("  1. 打开浏览器访问 http://localhost:8001")
        print("  2. 在聊天框中输入任务")
        print("  3. 按回车或点击发送按钮")
        print("  4. 等待代理处理并返回结果")
        print("\n示例任务:")
        print("  - 读取 /etc/hosts 文件")
        print("  - 在当前目录执行 ls -la 命令")
        print("  - 获取贵州茅台(600519)的股票数据")
        print("  - 创建Python脚本文件 test.py")
        print("\n按 Ctrl+C 停止服务器")
        print("=" * 60)

        # 异步运行服务器
        await server.run_async(host="0.0.0.0", port=8001)

    except ImportError as e:
        print(f"[错误] 导入模块失败: {e}")
        print("\n请安装依赖:")
        print("  pip install -r requirements.txt")
        return 1

    except Exception as e:
        print(f"[错误] 启动失败: {e}")
        return 1

    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[再见] 服务器已停止")
        sys.exit(0)