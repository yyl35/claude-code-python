#!/usr/bin/env python3
"""
安装脚本
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """检查Python版本"""
    print("Checking Python version...")
    if sys.version_info < (3, 8):
        print(f"ERROR: Python 3.8+ required, found {sys.version}")
        return False
    print(f"OK: Python {sys.version}")
    return True

def install_dependencies():
    """安装依赖"""
    print("\nInstalling dependencies...")

    requirements_file = "requirements.txt"
    if not os.path.exists(requirements_file):
        print(f"ERROR: {requirements_file} not found")
        return False

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_file])
        print("OK: Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e}")
        return False

def create_env_file():
    """创建环境变量文件"""
    print("\nSetting up environment...")

    env_example = ".env.example"
    env_file = ".env"

    if os.path.exists(env_file):
        print(f"INFO: {env_file} already exists")
        return True

    if os.path.exists(env_example):
        try:
            with open(env_example, 'r') as src, open(env_file, 'w') as dst:
                dst.write(src.read())
            print(f"OK: Created {env_file} from {env_example}")
            print("   Please edit .env to add your API keys")
            return True
        except Exception as e:
            print(f"ERROR: Failed to create {env_file}: {e}")
            return False
    else:
        print(f"WARNING: {env_example} not found")
        return True

def run_tests():
    """运行测试"""
    print("\nRunning tests...")

    test_file = "final_test.py"
    if not os.path.exists(test_file):
        print(f"WARNING: {test_file} not found")
        return True

    try:
        result = subprocess.run([sys.executable, test_file],
                              capture_output=True, text=True)

        if result.returncode == 0:
            print("OK: All tests passed")
            # 显示测试摘要
            for line in result.stdout.split('\n'):
                if "TEST SUMMARY" in line or "SUCCESS:" in line or "FAILURE:" in line:
                    print(f"   {line}")
            return True
        else:
            print(f"ERROR: Tests failed (exit code: {result.returncode})")
            print(f"Output:\n{result.stdout}")
            if result.stderr:
                print(f"Errors:\n{result.stderr}")
            return False
    except Exception as e:
        print(f"ERROR: Failed to run tests: {e}")
        return False

def show_next_steps():
    """显示下一步操作"""
    print("\n" + "="*60)
    print("SETUP COMPLETE")
    print("="*60)

    print("\nNext steps:")
    print("1. Edit .env file to add your API keys:")
    print("   - OPENAI_API_KEY (DeepSeek API key)")
    print("   - Other settings as needed")

    print("\n2. Start the MCP server (if not already running):")
    print("   Your MCP server should be at: http://127.0.0.1:8000/sse")

    print("\n3. Run the agent:")
    print("   Interactive mode: python -m src.main --interactive")
    print("   Single task: python -m src.main --task \"your task here\"")

    print("\n4. Use in your code:")
    print("   ```python")
    print("   import asyncio")
    print("   from devops_agent import DevOpsAgent")
    print("   ")
    print("   async def main():")
    print("       agent = DevOpsAgent()")
    print("       await agent.initialize()")
    print("       result = await agent.process_task(\"your task\")")
    print("       print(result)")
    print("   ")
    print("   asyncio.run(main())")
    print("   ```")

    print("\n5. Available skills:")
    print("   - file_operations: File creation, reading, writing, deletion")
    print("   - command_execution: System command execution")
    print("   - code_development: Code file creation, modification, testing")

    print("\n" + "="*60)

def main():
    """主安装函数"""
    print("="*60)
    print("DevOps-Agent Setup")
    print("="*60)

    # 检查当前目录
    if not os.path.exists("src") or not os.path.exists("requirements.txt"):
        print("ERROR: Please run this script from the project root directory")
        return 1

    steps = [
        ("Python version check", check_python_version),
        ("Install dependencies", install_dependencies),
        ("Create environment file", create_env_file),
        ("Run tests", run_tests),
    ]

    results = []
    for name, func in steps:
        print(f"\n[{name}]")
        result = func()
        results.append(result)

        if not result and name != "Run tests":  # 测试失败可以继续
            print(f"\nERROR: Setup failed at step: {name}")
            return 1

    if all(results):
        show_next_steps()
        return 0
    else:
        print("\nWARNING: Some setup steps had issues")
        print("You may need to manually fix some problems")
        show_next_steps()
        return 1

if __name__ == "__main__":
    sys.exit(main())