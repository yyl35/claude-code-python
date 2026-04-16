#!/usr/bin/env python3
"""
测试最终优化效果
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_final_optimization():
    """测试最终优化"""
    print("测试代理执行器最终优化效果...")
    print("=" * 60)

    try:
        # 读取系统提示词
        with open("src/agent_executor.py", "r", encoding="utf-8") as f:
            content = f.read()

        # 查找系统提示词部分
        import re
        system_prompt_match = re.search(r'system_prompt = """(.*?)"""', content, re.DOTALL)

        if not system_prompt_match:
            print("[ERROR] 未找到系统提示词")
            return False

        system_prompt = system_prompt_match.group(1)

        print("1. 检查核心优化点:")

        # 检查所有关键优化
        optimizations = [
            ("走一步看一步", "核心思维模式"),
            ("每一步都基于当前结果决定下一步", "动态决策"),
            ("提供使用信息（关键步骤！）", "用户视角"),
            ("文件操作后的必要步骤", "文件位置指导"),
            ("处理大文件/大数据时的注意事项", "大数据处理"),
            ("动态调整策略", "灵活应对"),
            ("413 Request Entity Too Large", "错误处理指导"),
            ("如果工具执行失败，分析失败原因", "故障处理")
        ]

        all_passed = True
        for concept, description in optimizations:
            if concept in system_prompt:
                print(f"   [OK] 包含: {description}")
            else:
                print(f"   [ERROR] 缺少: {description}")
                all_passed = False

        if not all_passed:
            return False

        # 检查代码逻辑
        print("\n2. 检查代码逻辑优化:")

        code_checks = [
            ("_should_summarize", "返回False", "return False" in content and "_should_summarize" in content),
            ("模型控制结束", "if not tool_calls", "if not tool_calls and response.content" in content),
            ("移除自动总结", "无自动触发", "if iteration >= self.max_iterations or self._should_summarize" not in content)
        ]

        for check_name, description, condition in code_checks:
            if condition:
                print(f"   [OK] {check_name}: {description}")
            else:
                print(f"   [ERROR] {check_name}: {description} 未正确实现")
                all_passed = False

        # 检查思考过程完整性
        print("\n3. 检查思考过程完整性:")

        thinking_steps = [
            "第一步：获取数据",
            "第二步：创建脚本",
            "第三步：测试脚本",
            "第四步：提供使用信息",
            "第五步：总结"
        ]

        for step in thinking_steps:
            if step in system_prompt:
                print(f"   [OK] 包含: {step}")
            else:
                print(f"   [ERROR] 缺少: {step}")
                all_passed = False

        return all_passed

    except Exception as e:
        print(f"[错误] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("代理执行器最终优化测试")
    print("=" * 60)

    success = await test_final_optimization()

    print("\n" + "=" * 60)
    if success:
        print("[成功] 所有优化验证通过")
        print("\n优化总结:")
        print("1. [OK] 核心思维: '走一步看一步'的动态决策")
        print("2. [OK] 用户视角: 提供文件位置和使用信息")
        print("3. [OK] 代码逻辑: 模型完全控制流程")
        print("4. [OK] 错误处理: 指导处理大文件和413错误")
        print("5. [OK] 灵活应对: 基于结果动态调整策略")
        print("\n预期效果:")
        print("- 代理能完成复合任务而不中断")
        print("- 创建文件后会明确告知位置")
        print("- 能处理大文件和错误情况")
        print("- 像人类助手一样逐步思考")
    else:
        print("[失败] 优化验证失败")

    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)