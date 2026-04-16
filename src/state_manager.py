import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

class StateManager:
    """状态管理器"""

    def __init__(self, memory_path: str):
        self.memory_path = Path(memory_path)
        self.state = {
            "tasks": [],
            "session_start": datetime.now().isoformat(),
            "statistics": {
                "total_tasks": 0,
                "successful_tasks": 0,
                "failed_tasks": 0
            }
        }

    async def load_state(self):
        """加载状态"""
        if self.memory_path.exists():
            try:
                with open(self.memory_path, 'r', encoding='utf-8') as f:
                    self.state = json.load(f)
                print(f"已加载 {len(self.state['tasks'])} 条历史记录")
            except Exception as e:
                print(f"加载状态失败: {e}")

    async def save_state(self):
        """保存状态"""
        try:
            self.memory_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.memory_path, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存状态失败: {e}")

    async def record_task(self, user_input: str):
        """记录新任务"""
        task = {
            "timestamp": datetime.now().isoformat(),
            "input": user_input,
            "result": None,
            "status": "pending"
        }
        self.state["tasks"].append(task)
        self.state["statistics"]["total_tasks"] += 1
        await self.save_state()

    async def record_result(self, user_input: str, result: str):
        """记录任务结果"""
        for task in reversed(self.state["tasks"]):
            if task["input"] == user_input and task["status"] == "pending":
                task["result"] = result
                task["status"] = "success" if "失败" not in result else "failed"
                task["completed_at"] = datetime.now().isoformat()

                if task["status"] == "success":
                    self.state["statistics"]["successful_tasks"] += 1
                else:
                    self.state["statistics"]["failed_tasks"] += 1

                await self.save_state()
                break

    async def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取历史记录"""
        return self.state["tasks"][-limit:]

    async def clear_history(self):
        """清除历史记录"""
        self.state["tasks"] = []
        self.state["statistics"] = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0
        }
        await self.save_state()