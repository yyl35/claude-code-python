#!/usr/bin/env python3
"""
测试代理是否会在创建文件后提供文件位置信息
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_file_location_guidance():
    """测试文件位置指导"""
    print("测试代理文件位置信息提供功能...")
    print("=" * 60)

    try:
        # 读取系统提示词，检查是否包含关键内容
        with open("src/agent_executor.py", "r", encoding="utf-8") as f:
            content = f.read()

        # 查找系统提示词部分
        import re
        system_prompt_match = re.search(r'system_prompt = """(.*?)"""', content, re.DOTALL)

        if not system_prompt_match:
            print("[ERROR] 未找到系统提示词")
            return False

        system_prompt = system_prompt_match.group(1)

        print("1. 检查文件位置指导:")

        # 检查关键概念
        key_concepts = [
            ("提供使用信息", "强调提供使用信息"),
            ("用户需要知道文件在哪里", "用户视角"),
            ("检查文件位置，提供具体路径", "具体路径指导"),
            ("文件操作后的必要步骤", "操作步骤"),
            ("获取文件的完整路径", "完整路径"),
            ("在回复中明确告诉用户文件位置", "明确告知"),
            ("错误做法", "错误示例"),
            ("正确做法", "正确示例")
        ]

        all_passed = True
        for concept, description in key_concepts:
            if concept in system_prompt:
                print(f"   [OK] 包含: {description}")
            else:
                print(f"   [ERROR] 缺少: {description}")
                all_passed = False

        if not all_passed:
            return False

        # 检查思考过程示例是否完整
        print("\n2. 检查思考过程完整性:")

        # 检查是否包含完整的5步思考
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

        # 检查具体的文件操作指导
        print("\n3. 检查具体操作指导:")

        file_operations = [
            "创建文件后，立即检查文件是否成功创建",
            "获取文件的完整路径",
            "提供具体的访问命令",
            "如果可能，提供运行示例"
        ]

        for operation in file_operations:
            if operation in system_prompt:
                print(f"   [OK] 包含: {operation}")
            else:
                print(f"   [ERROR] 缺少: {operation}")
                all_passed = False

        return all_passed

    except Exception as e:
        print(f"[错误] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("代理文件位置信息提供功能测试")
    print("=" * 60)

    success = await test_file_location_guidance()

    print("\n" + "=" * 60)
    if success:
        print("[成功] 文件位置指导优化验证通过")
        print("\n优化总结:")
        print("1. 添加了'提供使用信息'作为关键步骤")
        print("2. 强调用户需要知道文件具体位置")
        print("3. 提供了文件操作后的必要步骤")
        print("4. 给出了正确和错误的做法示例")
        print("5. 完整的5步思考过程")
        print("\n预期效果:")
        print("- 代理创建文件后会告诉用户具体路径")
        print("- 会提供具体的访问和使用命令")
        print("- 用户不需要主动询问'文件在哪里'")
        print("- 回复中包含完整的文件位置信息")
    else:
        print("[失败] 优化验证失败")

    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)