#!/usr/bin/env python3
"""
测试命令输出格式化修复
"""

import sys
import os

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

def test_encoding_fix():
    '''测试编码修复'''
    print('测试编码修复功能...')
    print('=' * 60)

    from src.skill_manager import CommandExecutionSkill

    # 创建技能实例
    skill = CommandExecutionSkill()

    # 测试乱码修复
    test_cases = [
        # 乱码示例
        ("'Select-Object' �����ڲ����ⲿ���Ҳ���ǿ����еĳ���\n���������ļ���",
         "'Select-Object' 不是内部或外部命令，也不是可运行的程序\n或批处理文件"),

        # 工具执行器输出示例
        ("""工具 'execute_shell_command' 执行成功:
[COMMAND] Executing: powershell Get-PSDrive -PSProvider FileSystem | Select-Object Name, Used, Free
**Command:** `powershell Get-PSDrive -PSProvider FileSystem | Select-Object Name, Used, Free`
**Exit code:** 255
**Standard Error:**
```
'Select-Object' �����ڲ����ⲿ���Ҳ���ǿ����еĳ���
���������ļ���
```""",
         "命令执行完成")
    ]

    for i, (input_text, expected_contains) in enumerate(test_cases, 1):
        print(f'\n测试用例 {i}:')
        print(f'输入: {input_text[:100]}...')

        # 测试编码修复
        fixed = skill._fix_encoding_issues(input_text)
        print(f'修复后: {fixed[:100]}...')

        # 测试格式化
        formatted = skill._format_command_result(input_text, "test command", "execute_shell_command")
        print(f'格式化后 (前200字符):')
        print(formatted[:200] if len(formatted) > 200 else formatted)

def test_agent_command():
    '''测试代理命令执行'''
    print('\n' + '=' * 60)
    print('测试代理命令执行')
    print('=' * 60)

    import asyncio

    async def test():
        try:
            from src.config import config
            from src.tool_manager import MCPToolManager
            from src.skill_manager import SkillManager

            # 创建技能管理器
            skill_manager = SkillManager()

            # 获取命令执行技能
            command_skill = skill_manager.get_skill("command_execution")

            if command_skill:
                print('测试CommandExecutionSkill...')

                # 模拟工具执行器
                async def mock_tool_executor(tool_name, params):
                    command = params.get('command', '')
                    print(f'模拟执行命令: {command}')

                    # 返回模拟结果
                    if 'powershell' in command:
                        return f"""工具 'execute_shell_command' 执行成功:
[COMMAND] Executing: {command}
**Command:** `{command}`
**Exit code:** 0
**Standard Output:**
```
Name UsedGB FreeGB
---- ------ ------
C    268.69 917.49
D    533.52 1028.77
E      1.03 975.53
```"""
                    else:
                        return f"""工具 'execute_shell_command' 执行成功:
[COMMAND] Executing: {command}
**Command:** `{command}`
**Exit code:** 0
**Standard Output:**
```
模拟命令输出
```"""

                # 测试技能执行
                result = await command_skill.execute(
                    "用powershell命令帮我查一下电脑剩余硬盘空间",
                    mock_tool_executor
                )

                print(f'技能执行结果:')
                print(result[:500] if len(result) > 500 else result)
            else:
                print('未找到command_execution技能')

        except Exception as e:
            print(f'测试失败: {e}')
            import traceback
            traceback.print_exc()

    asyncio.run(test())

if __name__ == "__main__":
    test_encoding_fix()
    test_agent_command()
    print('\n' + '=' * 60)
    print('测试完成')