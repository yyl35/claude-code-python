#!/usr/bin/env python3
"""
测试PowerShell命令编码问题
"""

import asyncio
import sys
import os
import subprocess

# 在Windows上设置UTF-8编码
if sys.platform == "win32":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

# 添加项目根目录到Python路径
sys.path.insert(0, '.')

def test_powershell_commands():
    '''测试不同的PowerShell命令格式'''
    print('测试PowerShell命令编码问题...')
    print('=' * 60)

    # 测试几种不同的命令格式
    test_commands = [
        # 原命令格式
        "powershell Get-PSDrive -PSProvider FileSystem | Select-Object Name, Used, Free, @{Name='UsedGB';Expression={[math]::Round($_.Used/1GB,2)}}, @{Name='FreeGB';Expression={[math]::Round($_.Free/1GB,2)}}",

        # 使用-Command参数
        "powershell -Command \"Get-PSDrive -PSProvider FileSystem | Select-Object Name, Used, Free, @{Name='UsedGB';Expression={[math]::Round($_.Used/1GB,2)}}, @{Name='FreeGB';Expression={[math]::Round($_.Free/1GB,2)}}\"",

        # 简化命令
        "powershell -Command \"Get-PSDrive -PSProvider FileSystem | Format-Table Name, @{Name='Used(GB)';Expression={[math]::Round($_.Used/1GB,2)}}, @{Name='Free(GB)';Expression={[math]::Round($_.Free/1GB,2)}} -AutoSize\"",

        # 更简单的命令
        "powershell -Command \"Get-PSDrive -PSProvider FileSystem | Select Name, @{Name='UsedGB';Expression={[math]::Round($_.Used/1GB,2)}}, @{Name='FreeGB';Expression={[math]::Round($_.Free/1GB,2)}}\"",

        # 最简单的命令
        "powershell Get-WmiObject Win32_LogicalDisk | Select DeviceID, Size, FreeSpace",

        # 使用cmd /c执行
        "cmd /c \"powershell Get-PSDrive -PSProvider FileSystem | Select-Object Name, Used, Free\""
    ]

    for i, cmd in enumerate(test_commands, 1):
        print(f'\n测试命令 {i}:')
        print(f'命令: {cmd[:80]}...' if len(cmd) > 80 else f'命令: {cmd}')

        try:
            # 执行命令
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            print(f'退出码: {result.returncode}')

            if result.stdout:
                print(f'标准输出 (前200字符):')
                print(result.stdout[:200])
            else:
                print('标准输出: 空')

            if result.stderr:
                print(f'标准错误:')
                print(result.stderr[:200])
            else:
                print('标准错误: 空')

        except Exception as e:
            print(f'执行失败: {e}')

    print('\n' + '=' * 60)
    print('测试系统默认编码...')

    # 测试系统编码
    import locale
    print(f'系统默认编码: {locale.getpreferredencoding()}')

    # 测试chcp命令
    try:
        result = subprocess.run('chcp', shell=True, capture_output=True, text=True)
        print(f'代码页: {result.stdout.strip()}')
    except:
        pass

async def test_agent_powershell():
    '''测试代理执行PowerShell命令'''
    print('\n' + '=' * 60)
    print('测试代理执行PowerShell命令')
    print('=' * 60)

    try:
        from src.config import config
        from src.tool_manager import MCPToolManager

        # 创建工具管理器
        tool_manager = MCPToolManager(config.mcp_server_url)
        tools = await tool_manager.fetch_tools()

        # 查找execute_shell_command工具
        execute_tool = None
        for tool in tools:
            if tool.name == 'execute_shell_command':
                execute_tool = tool
                break

        if execute_tool:
            print('测试execute_shell_command工具...')

            # 测试简单的PowerShell命令
            test_cmd = "powershell Get-WmiObject Win32_LogicalDisk | Select DeviceID, Size, FreeSpace"
            print(f'执行命令: {test_cmd}')

            result = await execute_tool.coroutine(command=test_cmd)
            print(f'工具执行结果 (前500字符):')
            print(result[:500] if result else '空结果')
        else:
            print('未找到execute_shell_command工具')

    except Exception as e:
        print(f'测试失败: {e}')
        import traceback
        traceback.print_exc()

async def test_agent_command():
    '''测试代理执行命令功能'''
    print('\n' + '=' * 60)
    print('测试代理执行命令功能')
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

        # 测试命令
        query = '用powershell命令帮我查一下电脑剩余硬盘空间'
        print(f'查询: {query}')

        result = await agent.execute_direct(query)
        print(f'结果 (前500字符):')
        print(result[:500] if len(result) > 500 else result)

    except Exception as e:
        print(f'测试失败: {e}')
        import traceback
        traceback.print_exc()

async def main():
    '''主函数'''
    print('PowerShell命令编码问题测试')
    print('=' * 60)

    # 测试直接命令执行
    test_powershell_commands()

    # 测试代理执行
    await test_agent_powershell()

    # 测试代理命令功能
    await test_agent_command()

    print('\n' + '=' * 60)
    print('测试完成')

    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)