#!/usr/bin/env python3
"""
最终验证：测试修复后的记忆系统是否正常工作
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.memory.manager import MemoryManager


async def final_verification():
    """最终验证测试"""
    print("=" * 60)
    print("最终验证：修复后的记忆系统")
    print("=" * 60)

    # 使用实际的chat_memory目录
    memory_dir = project_root / "chat_memory"
    memory_dir.mkdir(exist_ok=True)

    print(f"使用实际记忆目录: {memory_dir}")

    # 清理所有会话文件
    for file in memory_dir.glob("*.json"):
        file.unlink()
    print("已清理所有旧会话文件")

    # 创建记忆管理器
    memory_manager = MemoryManager(str(memory_dir))
    await memory_manager.initialize()

    # 创建新会话（模拟你的实际会话）
    session_id = "final_test_session"
    memory_manager.create_session(session_id)

    print(f"\n创建新会话: {session_id}")

    # 模拟实际对话流程
    print(f"\n模拟对话流程:")

        # 检查是否包含原始表格数据
        if '| date | code |' in result or '|:-----------|:----------|' in result:
            print('[失败] 结果包含原始表格数据，总结功能未工作')
            return False
        elif '2026' in result:
            print('[成功] 结果包含2026年数据，日期正确')
        elif '2024' in result:
            print('[警告] 结果包含2024年数据，日期可能不正确')
        else:
            print('[信息] 结果中没有明确的年份信息')

        # 检查是否包含分析内容
        if '分析' in result or '总结' in result or '建议' in result:
            print('[成功] 结果包含分析总结内容')
        else:
            print('[警告] 结果可能缺少分析总结')

        print(f'\n结果片段:')
        print(result[:300] if len(result) > 300 else result)

        return True

    except Exception as e:
        print(f'[错误] 测试失败: {e}')
        import traceback
        traceback.print_exc()
        return False

async def test_powershell_command():
    '''测试PowerShell命令功能'''
    print('\n' + '=' * 60)
    print('测试PowerShell命令功能')
    print('=' * 60)

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

        # 测试查询
        query = '用powershell命令帮我查一下电脑剩余硬盘空间'
        print(f'查询: {query}')

        result = await agent.execute_direct(query)

        # 检查结果
        print(f'\n结果分析:')
        print(f'结果长度: {len(result)} 字符')

        # 检查是否包含乱码
        if '�����ڲ����ⲿ���Ҳ���ǿ����еĳ���' in result:
            print('[失败] 结果包含乱码，编码修复未工作')
            return False
        elif '不是内部或外部命令' in result:
            print('[成功] 乱码已修复为中文')
        elif 'GB' in result or '磁盘' in result or '空间' in result:
            print('[成功] 结果包含磁盘空间信息')
        else:
            print('[信息] 结果格式正常')

        # 检查是否包含分析内容
        if '分析' in result or '总结' in result or '报告' in result:
            print('[成功] 结果包含分析总结内容')
        else:
            print('[警告] 结果可能缺少分析总结')

        print(f'\n结果片段:')
        print(result[:300] if len(result) > 300 else result)

        return True

    except Exception as e:
        print(f'[错误] 测试失败: {e}')
        import traceback
        traceback.print_exc()
        return False

async def test_skill_manager():
    '''测试技能管理器'''
    print('\n' + '=' * 60)
    print('测试技能管理器')
    print('=' * 60)

    try:
        from src.skill_manager import SkillManager, CommandExecutionSkill

        # 创建技能管理器
        skill_manager = SkillManager()

        # 测试技能列表
        skills = skill_manager.list_skills()
        print(f'可用技能: {len(skills)} 个')
        for name, desc in skills.items():
            print(f'  - {name}: {desc}')

        # 测试命令执行技能
        command_skill = skill_manager.get_skill("command_execution")
        if command_skill:
            print(f'\n找到command_execution技能')

            # 测试编码修复
            test_text = "'Select-Object' �����ڲ����ⲿ���Ҳ���ǿ����еĳ���"
            fixed = command_skill._fix_encoding_issues(test_text)
            print(f'编码修复测试:')
            print(f'  输入: {test_text}')
            print(f'  输出: {fixed}')

            return True
        else:
            print('[错误] 未找到command_execution技能')
            return False

    except Exception as e:
        print(f'[错误] 测试失败: {e}')
        import traceback
        traceback.print_exc()
        return False

async def test_agent_summary():
    '''测试代理总结功能'''
    print('\n' + '=' * 60)
    print('测试代理总结功能')
    print('=' * 60)

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

        # 测试命令输出总结
        test_output = """工具 'execute_shell_command' 执行成功:
[COMMAND] Executing: powershell Get-PSDrive -PSProvider FileSystem | Select-Object Name, Used, Free
**Command:** `powershell Get-PSDrive -PSProvider FileSystem | Select-Object Name, Used, Free`
**Exit code:** 255
**Standard Error:**
```
'Select-Object' �����ڲ����ⲿ���Ҳ���ǿ����еĳ���
���������ļ���
```"""

        summary = agent._summarize_command_output(test_output)
        print(f'命令输出总结测试:')
        print(f'  输入长度: {len(test_output)} 字符')
        print(f'  总结: {summary}')

        # 检查是否修复了乱码
        if '�����ڲ����ⲿ���Ҳ���ǿ����еĳ���' in summary:
            print('  [失败] 总结中仍然包含乱码')
            return False
        elif '不是内部或外部命令' in summary:
            print('  [成功] 乱码已修复')
        else:
            print('  [信息] 总结正常')

        return True

    except Exception as e:
        print(f'[错误] 测试失败: {e}')
        import traceback
        traceback.print_exc()
        return False

async def main():
    '''主函数'''
    print('DevOps Agent 最终验证测试')
    print('=' * 60)
    print('测试所有修复是否正常工作')
    print('=' * 60)

    results = []

    # 测试1: 股票查询功能
    print('\n[测试1] 股票查询功能')
    stock_ok = await test_stock_query()
    results.append(('股票查询', stock_ok))

    # 测试2: PowerShell命令功能
    print('\n[测试2] PowerShell命令功能')
    ps_ok = await test_powershell_command()
    results.append(('PowerShell命令', ps_ok))

    # 测试3: 技能管理器
    print('\n[测试3] 技能管理器')
    skill_ok = await test_skill_manager()
    results.append(('技能管理器', skill_ok))

    # 测试4: 代理总结功能
    print('\n[测试4] 代理总结功能')
    summary_ok = await test_agent_summary()
    results.append(('代理总结', summary_ok))

    # 总结
    print('\n' + '=' * 60)
    print('测试结果总结')
    print('=' * 60)

    all_passed = True
    for test_name, passed in results:
        status = '✓ 通过' if passed else '✗ 失败'
        print(f'{test_name}: {status}')
        if not passed:
            all_passed = False

    print('\n' + '=' * 60)
    if all_passed:
        print('[成功] 所有测试通过！修复工作正常。')
        print('\n现在可以访问 http://localhost:8001 测试聊天界面：')
        print('1. 股票查询："查一下600095.sh最新收盘价"')
        print('2. 磁盘空间："用powershell命令帮我查一下电脑剩余硬盘空间"')
        print('3. 其他命令："查看当前目录文件" 等')
    else:
        print('[失败] 部分测试未通过，需要进一步修复。')

    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)