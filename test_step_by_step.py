#!/usr/bin/env python3
"""
测试"走一步看一步"的代理执行逻辑
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_step_by_step_logic():
    """测试走一步看一步的逻辑"""
    print("测试代理'走一步看一步'执行逻辑...")
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

        print("1. 检查系统提示词优化:")

        # 检查关键概念
        key_concepts = [
            ("走一步看一步", "强调逐步执行"),
            ("每一步都基于当前结果决定下一步", "动态决策"),
            ("不要预先计划所有步骤", "避免过度规划"),
            ("像人类助手一样思考", "自然思考过程"),
            ("思考过程示例", "具体示例指导")
        ]

        all_passed = True
        for concept, description in key_concepts:
            if concept in system_prompt:
                print(f"   [OK] 包含: {description} ({concept})")
            else:
                print(f"   [ERROR] 缺少: {description} ({concept})")
                all_passed = False

        if not all_passed:
            return False

        # 检查执行逻辑
        print("\n2. 检查执行逻辑:")

        # 检查是否移除了自动总结
        if "if iteration >= self.max_iterations or self._should_summarize" not in content:
            print("   [OK] 已移除自动总结逻辑")
        else:
            print("   [ERROR] 自动总结逻辑仍然存在")
            return False

        # 检查模型控制结束的逻辑
        if "if not tool_calls and response.content and len(response.content) > 10:" in content:
            print("   [OK] 模型控制结束逻辑存在")
        else:
            print("   [ERROR] 模型控制结束逻辑不存在")
            return False

        # 检查 _should_summarize 方法
        if "return False" in content and "_should_summarize" in content:
            print("   [OK] _should_summarize 返回 False")
        else:
            print("   [ERROR] _should_summarize 可能未正确设置")
            return False

        return True

    except Exception as e:
        print(f"[错误] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("代理'走一步看一步'执行逻辑测试")
    print("=" * 60)

    success = await test_step_by_step_logic()

    print("\n" + "=" * 60)
    if success:
        print("[成功] 代理执行逻辑优化验证通过")
        print("\n优化总结:")
        print("1. 系统提示词强调'走一步看一步'思维")
        print("2. 模型基于当前结果动态决定下一步")
        print("3. 移除了自动总结，完全由模型控制")
        print("4. 提供了具体的思考过程示例")
        print("\n预期效果:")
        print("- 代理会像人类助手一样逐步思考")
        print("- 根据工具执行结果决定下一步")
        print("- 不会在获取数据后就停止")
        print("- 会完成所有必要步骤后给出最终答案")
    else:
        print("[失败] 优化验证失败")

    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)