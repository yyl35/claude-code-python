#!/usr/bin/env python3
"""
聊天记忆管理器
增强的记忆功能，支持对话历史、上下文记忆和会话管理
"""

import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)

class ChatMemoryManager:
    """聊天记忆管理器"""

    def __init__(self, memory_dir: str = "chat_memory"):
        self.memory_dir = Path(memory_dir)
        self.sessions: Dict[str, Dict] = {}
        self.conversations: Dict[str, List[Dict]] = defaultdict(list)
        self.summaries: Dict[str, str] = {}
        self.contexts: Dict[str, List[str]] = defaultdict(list)
        self.user_preferences: Dict[str, Any] = {}

    async def initialize(self):
        """初始化记忆管理器"""
        try:
            # 创建记忆目录
            self.memory_dir.mkdir(parents=True, exist_ok=True)

            # 加载现有会话
            await self._load_sessions()

            # 加载用户偏好
            await self._load_user_preferences()

            logger.info(f"记忆管理器初始化完成，已加载 {len(self.sessions)} 个会话")
            return True

        except Exception as e:
            logger.error(f"记忆管理器初始化失败: {e}")
            return False

    async def _load_sessions(self):
        """加载现有会话"""
        session_files = list(self.memory_dir.glob("session_*.json"))

        for session_file in session_files:
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)

                session_id = session_data.get("session_id")
                if session_id:
                    self.sessions[session_id] = session_data

                    # 加载对话记录
                    conv_file = self.memory_dir / f"conversation_{session_id}.json"
                    if conv_file.exists():
                        with open(conv_file, 'r', encoding='utf-8') as f:
                            self.conversations[session_id] = json.load(f)

                    # 加载摘要
                    summary_file = self.memory_dir / f"summary_{session_id}.json"
                    if summary_file.exists():
                        with open(summary_file, 'r', encoding='utf-8') as f:
                            self.summaries[session_id] = json.load(f).get("summary", "")

            except Exception as e:
                logger.error(f"加载会话失败 {session_file}: {e}")

    async def _load_user_preferences(self):
        """加载用户偏好"""
        try:
            pref_file = self.memory_dir / "user_preferences.json"
            if pref_file.exists():
                with open(pref_file, 'r', encoding='utf-8') as f:
                    self.user_preferences = json.load(f)
                logger.info(f"已加载用户偏好，共 {len(self.user_preferences)} 个条目")
        except Exception as e:
            logger.error(f"加载用户偏好失败: {e}")
            self.user_preferences = {}

    async def _save_user_preferences(self):
        """保存用户偏好"""
        try:
            pref_file = self.memory_dir / "user_preferences.json"
            with open(pref_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_preferences, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存用户偏好失败: {e}")

    def get_user_preference(self, key: str, default: Any = None) -> Any:
        """获取用户偏好"""
        return self.user_preferences.get(key, default)

    def set_user_preference(self, key: str, value: Any):
        """设置用户偏好"""
        self.user_preferences[key] = value
        # 异步保存
        asyncio.create_task(self._save_user_preferences())

    def get_all_user_preferences(self) -> Dict[str, Any]:
        """获取所有用户偏好"""
        return dict(self.user_preferences)

    def clear_user_preference(self, key: str):
        """清除用户偏好"""
        if key in self.user_preferences:
            del self.user_preferences[key]
            asyncio.create_task(self._save_user_preferences())

    async def _save_session(self, session_id: str):
        """保存会话数据"""
        try:
            session_data = self.sessions.get(session_id)
            if session_data:
                session_file = self.memory_dir / f"session_{session_id}.json"
                with open(session_file, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, ensure_ascii=False, indent=2)

            # 保存对话记录
            conversation = self.conversations.get(session_id, [])
            if conversation:
                conv_file = self.memory_dir / f"conversation_{session_id}.json"
                with open(conv_file, 'w', encoding='utf-8') as f:
                    json.dump(conversation, f, ensure_ascii=False, indent=2)

            # 保存摘要
            summary = self.summaries.get(session_id)
            if summary:
                summary_file = self.memory_dir / f"summary_{session_id}.json"
                with open(summary_file, 'w', encoding='utf-8') as f:
                    json.dump({"summary": summary}, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"保存会话失败 {session_id}: {e}")

    def create_session(self, session_id: Optional[str] = None) -> str:
        """创建新会话"""
        if not session_id:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:8]}"

        self.sessions[session_id] = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "message_count": 0,
            "status": "active",
            "metadata": {}
        }

        self.conversations[session_id] = []
        self.summaries[session_id] = ""
        self.contexts[session_id] = []

        logger.info(f"创建新会话: {session_id}")
        return session_id

    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """添加消息到会话"""
        if session_id not in self.sessions:
            self.create_session(session_id)

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "message_id": len(self.conversations[session_id]),
            "metadata": metadata or {}
        }

        self.conversations[session_id].append(message)
        self.sessions[session_id]["message_count"] += 1
        self.sessions[session_id]["last_activity"] = datetime.now().isoformat()

        # 更新上下文
        self._update_context(session_id, message)

        # 异步保存
        asyncio.create_task(self._save_session(session_id))

        logger.debug(f"添加消息到会话 {session_id}: {role} - {content[:50]}...")

    def _update_context(self, session_id: str, message: Dict):
        """更新上下文"""
        # 提取关键词
        keywords = self._extract_keywords(message["content"])
        self.contexts[session_id].extend(keywords)

        # 保持上下文长度
        if len(self.contexts[session_id]) > 50:
            self.contexts[session_id] = self.contexts[session_id][-50:]

        # 定期生成摘要
        if len(self.conversations[session_id]) % 10 == 0:
            asyncio.create_task(self._generate_summary(session_id))

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词（简化版本）"""
        # 这里可以集成更复杂的关键词提取算法
        words = text.lower().split()
        keywords = []

        # 简单的关键词提取：长度大于3的非常见词
        common_words = {"the", "and", "for", "with", "this", "that", "have", "from", "what", "how", "why", "when", "where"}
        for word in words:
            if len(word) > 3 and word not in common_words and word.isalpha():
                keywords.append(word)

        return keywords[:5]  # 最多返回5个关键词

    async def _generate_summary(self, session_id: str):
        """生成对话摘要"""
        try:
            conversation = self.conversations.get(session_id, [])
            if len(conversation) < 5:
                return

            # 提取重要消息
            important_messages = []
            for msg in conversation[-20:]:  # 最近20条消息
                if msg["role"] == "user" or len(msg["content"]) > 100:
                    important_messages.append(f"{msg['role']}: {msg['content'][:200]}")

            if important_messages:
                summary = " | ".join(important_messages[-5:])  # 最近5条重要消息
                self.summaries[session_id] = summary[:500]  # 限制长度

                logger.debug(f"为会话 {session_id} 生成摘要")

        except Exception as e:
            logger.error(f"生成摘要失败 {session_id}: {e}")

    def get_session_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """获取会话历史"""
        if session_id not in self.conversations:
            return []

        history = self.conversations[session_id][-limit:]

        # 转换为前端格式
        formatted_history = []
        for msg in history:
            formatted_history.append({
                "text": msg["content"],
                "sender": msg["role"],
                "timestamp": datetime.fromisoformat(msg["timestamp"]).strftime("%H:%M:%S"),
                "date": datetime.fromisoformat(msg["timestamp"]).strftime("%Y-%m-%d")
            })

        return formatted_history

    def get_conversation_context(self, session_id: str, limit: int = 10) -> str:
        """获取对话上下文"""
        if session_id not in self.conversations:
            return ""

        # 获取最近的对话
        recent_messages = self.conversations[session_id][-limit:]

        # 构建上下文
        context_parts = []
        for msg in recent_messages:
            role = "用户" if msg["role"] == "user" else "助手"
            context_parts.append(f"{role}: {msg['content'][:200]}")

        # 添加上下文关键词
        if self.contexts[session_id]:
            context_parts.append(f"\n对话关键词: {', '.join(set(self.contexts[session_id][-10:]))}")

        # 添加摘要
        if self.summaries.get(session_id):
            context_parts.append(f"\n对话摘要: {self.summaries[session_id]}")

        return "\n".join(context_parts)

    def clear_session_history(self, session_id: str):
        """清空会话历史"""
        if session_id in self.conversations:
            self.conversations[session_id] = []
            self.contexts[session_id] = []
            self.summaries[session_id] = ""

            # 更新会话
            self.sessions[session_id]["message_count"] = 0
            self.sessions[session_id]["last_activity"] = datetime.now().isoformat()

            # 异步保存
            asyncio.create_task(self._save_session(session_id))

            logger.info(f"清空会话历史: {session_id}")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_sessions = len(self.sessions)
        active_sessions = sum(1 for s in self.sessions.values()
                             if datetime.fromisoformat(s["last_activity"]) > datetime.now() - timedelta(hours=1))

        total_messages = sum(s["message_count"] for s in self.sessions.values())

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "total_messages": total_messages,
            "user_preferences_count": len(self.user_preferences),
            "memory_dir": str(self.memory_dir.absolute())
        }

    def cleanup_old_sessions(self, days: int = 7):
        """清理旧会话"""
        cutoff_date = datetime.now() - timedelta(days=days)
        sessions_to_remove = []

        for session_id, session_data in self.sessions.items():
            last_activity = datetime.fromisoformat(session_data["last_activity"])
            if last_activity < cutoff_date:
                sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            # 删除会话文件
            session_file = self.memory_dir / f"session_{session_id}.json"
            conv_file = self.memory_dir / f"conversation_{session_id}.json"
            summary_file = self.memory_dir / f"summary_{session_id}.json"

            for file_path in [session_file, conv_file, summary_file]:
                if file_path.exists():
                    try:
                        file_path.unlink()
                    except Exception as e:
                        logger.error(f"删除文件失败 {file_path}: {e}")

            # 从内存中移除
            self.sessions.pop(session_id, None)
            self.conversations.pop(session_id, None)
            self.summaries.pop(session_id, None)
            self.contexts.pop(session_id, None)

        if sessions_to_remove:
            logger.info(f"清理了 {len(sessions_to_remove)} 个旧会话")

    def search_conversations(self, query: str, limit: int = 10) -> List[Dict]:
        """搜索对话"""
        results = []

        for session_id, conversation in self.conversations.items():
            for msg in conversation:
                if query.lower() in msg["content"].lower():
                    results.append({
                        "session_id": session_id,
                        "role": msg["role"],
                        "content": msg["content"],
                        "timestamp": msg["timestamp"],
                        "message_id": msg["message_id"]
                    })

                    if len(results) >= limit:
                        break

            if len(results) >= limit:
                break

        return results[:limit]

# 单例实例
memory_manager = ChatMemoryManager()

async def initialize_memory_manager():
    """初始化记忆管理器（全局）"""
    return await memory_manager.initialize()