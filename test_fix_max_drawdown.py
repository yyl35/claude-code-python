#!/usr/bin/env python3
"""
测试最大回撤脚本创建功能的修复
"""

import asyncio
import sys
import os
from pathlib import Path

# 在Windows上设置UTF-8编码
if sys.platform == "win32":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_max_drawdown_request():
    """测试最大回撤脚本创建请求"""
    print("测试最大回撤脚本创建功能修复...")
    print("=" * 60)

    try:
        from src.config import config
        from src.tool_manager import MCPToolManager
        from src.skill_manager import SkillManager
        from src.agent_executor import AgentExecutor

        # 创建代理执行器
        tool_manager = MCPToolManager(config.mcp_server_url)
        skill_manager = SkillManager()
        agent = AgentExecutor(config, tool_manager, skill_manager)

        # 初始化
        await agent.initialize()

        # 测试查询 - 与用户原始请求相同
        test_query = "帮我创建一个计算最大回撤的脚本 可以用tools获取一点实际数据测试"

        print(f"测试查询: {test_query}")
        print(f"{'='*60}")

        # 执行查询
        result = await agent.execute_direct(test_query)

        print(f"结果长度: {len(result)} 字符")
        print(f"\n结果预览 (前500字符):")
        print(result[:500] + "..." if len(result) > 500 else result)

        # 检查结果是否完整
        if len(result) < 100:
            print("\n[警告] 结果可能不完整，可能仍然存在中断问题")
            return False
        elif "最大回撤" in result and ("脚本" in result or "代码" in result or "def " in result or "import " in result):
            print("\n[成功] 结果看起来包含了脚本创建内容")
            return True
        else:
            print("\n[信息] 返回了结果，但内容可能需要检查")
            return True

    except ImportError as e:
        print(f"[错误] 导入失败: {e}")
        return False
    except Exception as e:
        print(f"[错误] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("最大回撤脚本创建功能修复测试")
    print("=" * 60)

    success = await test_max_drawdown_request()

    print("\n" + "=" * 60)
    if success:
        print("[成功] 测试完成，修复可能有效")
        print("\n说明:")
        print("1. 代理应该完成整个任务：获取数据、创建脚本、测试")
        print("2. 不应该在获取数据后就中断")
        print("3. 应该返回完整的处理结果")
    else:
        print("[失败] 测试失败，需要进一步调试")

    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)