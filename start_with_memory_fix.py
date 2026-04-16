#!/usr/bin/env python3
"""
启动修复后的聊天服务器测试
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("启动修复后的聊天服务器测试")
print("=" * 70)
print()
print("修复总结:")
print("1. ✅ 会话恢复功能 - 用户重新连接时能恢复最近会话")
print("2. ✅ 对话历史增强 - AI现在能访问完整的对话历史")
print("3. ✅ 指代解析 - 能理解'刚才'、'之前'、'上面说的'等指代词")
print("4. ✅ 会话合并 - 多个相关会话可以合并")
print("5. ✅ 智能sessionId管理 - 前后端协同管理sessionId")
print()
print("测试步骤:")
print("1. 启动聊天服务器")
print("2. 访问 http://localhost:8004")
print("3. 测试对话:")
print("   - 问: 'windows查看硬盘空间的命令是什么'")
print("   - 问: '我刚才问你什么问题'")
print("   - AI应该能记住之前的对话")
print()
print("按Enter键启动服务器...")
input()

async def main():
    """启动聊天服务器"""
    try:
        from src.chat_server import ChatServer

        print("\n启动聊天服务器...")
        server = ChatServer()

        # 初始化
        print("初始化服务器...")
        success = await server.initialize()
        if not success:
            print("[ERROR] 服务器初始化失败")
            return

        print("[OK] 服务器初始化成功")
        print("\n访问地址:")
        print("  Web界面: http://localhost:8004")
        print("  健康检查: http://localhost:8004/api/health")
        print("  状态信息: http://localhost:8004/api/status")
        print("\n按 Ctrl+C 停止服务器")

        # 运行服务器
        await server.run_async(host="0.0.0.0", port=8004)

    except ImportError as e:
        print(f"[ERROR] 导入模块失败: {e}")
        print("\n请安装依赖:")
        print("  pip install -r requirements.txt")
    except Exception as e:
        print(f"[ERROR] 启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[再见] 服务器已停止")
    except UnicodeEncodeError:
        print("\n\n注意: 控制台编码问题，建议使用支持UTF-8的终端")
        print("或者直接访问: http://localhost:8004")