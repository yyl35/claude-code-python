#!/usr/bin/env python3
"""
记忆管理器
整合所有记忆组件，提供统一接口
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import hashlib

from .types import (
    SessionMemory, ProjectMemory, Entity,
    ConversationSummary, MemoryContext,
    MAX_RAW_MESSAGES, SUMMARY_INTERVAL
)
from .smart_entity_tracker import SmartEntityTracker
from .directive_detector import DirectiveDetector
from .formatter import MemoryFormatter
from .learner import MemoryLearner
from .compressor import MemoryCompressor
from .smart_compressor import SmartMemoryCompressor


logger = logging.getLogger(__name__)


class MemoryManager:
    """记忆管理器（主类）"""

    def __init__(self, memory_dir: str = "chat_memory", project_root: Optional[str] = None, llm=None):
        self.memory_dir = Path(memory_dir)
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.llm = llm

        # 初始化组件
        self.entity_tracker = SmartEntityTracker(llm) if llm else None
        self.directive_detector = DirectiveDetector()
        self.formatter = MemoryFormatter()
        # 如果有LLM，使用智能压缩器，否则使用简单压缩器
        if llm:
            self.compressor = SmartMemoryCompressor(llm)
        else:
            self.compressor = MemoryCompressor()

        # 记忆存储
        self.sessions: Dict[str, SessionMemory] = {}
        self.project_memory: Optional[ProjectMemory] = None
        self.memory_learner: Optional[MemoryLearner] = None

        # 初始化项目记忆学习器
        self._init_memory_learner()

    def _init_memory_learner(self):
        """初始化记忆学习器（禁用）"""
        # 禁用记忆学习器，避免扫描工作区文件
        self.memory_learner = None
        logger.info("记忆学习器已禁用，避免扫描工作区文件")

    async def initialize(self) -> bool:
        """初始化记忆管理器"""
        try:
            # 创建记忆目录
            self.memory_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"记忆目录: {self.memory_dir.absolute()}")

            # 加载现有会话
            await self._load_sessions()

            # 加载项目记忆
            await self._load_project_memory()

            logger.info(f"记忆管理器初始化完成，已加载 {len(self.sessions)} 个会话")

            # 打印加载的会话ID
            for session_id in self.sessions:
                session = self.sessions[session_id]
                logger.info(f"  会话: {session_id}, 消息数: {session.message_count}, 最后活动: {session.last_activity}")

            return True

        except Exception as e:
            logger.error(f"记忆管理器初始化失败: {e}")
            return False

    async def _load_sessions(self):
        """加载现有会话"""
        if not self.memory_dir.exists():
            logger.warning(f"记忆目录不存在: {self.memory_dir}")
            return

        session_files = list(self.memory_dir.glob("session_*.json"))
        logger.info(f"找到 {len(session_files)} 个会话文件")

        for session_file in session_files:
            try:
                logger.info(f"加载会话文件: {session_file}")
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                session_id = data.get("session_id")
                if not session_id:
                    logger.warning(f"会话文件缺少session_id: {session_file}")
                    continue

                logger.info(f"加载会话: {session_id}")

                # 恢复会话记忆
                session_memory = SessionMemory(
                    session_id=session_id,
                    created_at=datetime.fromisoformat(data["created_at"]),
                    last_activity=datetime.fromisoformat(data["last_activity"]),
                    message_count=data.get("message_count", 0),
                    metadata=data.get("metadata", {})
                )

                # 加载实体
                if "entities" in data:
                    for eid, entity_data in data["entities"].items():
                        entity = Entity(
                            id=entity_data["id"],
                            type=entity_data["type"],
                            name=entity_data["name"],
                            aliases=entity_data["aliases"],
                            metadata=entity_data["metadata"],
                            created_at=datetime.fromisoformat(entity_data["created_at"]),
                            last_referenced=datetime.fromisoformat(entity_data["last_referenced"]),
                            reference_count=entity_data["reference_count"]
                        )
                        session_memory.entities[eid] = entity
                    logger.info(f"  加载了 {len(data['entities'])} 个实体")

                # 加载摘要
                if "summaries" in data:
                    for summary_data in data["summaries"]:
                        summary = ConversationSummary(
                            timestamp=summary_data["timestamp"],
                            summary=summary_data["summary"],
                            key_entities=summary_data["key_entities"],
                            message_count=summary_data["message_count"],
                            start_message_id=summary_data["start_message_id"],
                            end_message_id=summary_data["end_message_id"]
                        )
                        session_memory.summaries.append(summary)
                    logger.info(f"  加载了 {len(data['summaries'])} 个摘要")

                # 加载原始消息
                conv_file = self.memory_dir / f"conversation_{session_id}.json"
                if conv_file.exists():
                    with open(conv_file, 'r', encoding='utf-8') as f:
                        session_memory.raw_messages = json.load(f)
                    logger.info(f"  加载了 {len(session_memory.raw_messages)} 条原始消息")
                else:
                    logger.warning(f"对话文件不存在: {conv_file}")

                self.sessions[session_id] = session_memory
                logger.info(f"会话 {session_id} 加载成功")

            except Exception as e:
                logger.error(f"加载会话失败 {session_file}: {e}", exc_info=True)

    async def _load_project_memory(self):
        """加载项目记忆"""
        if self.memory_learner:
            self.project_memory = await self.memory_learner._load_project_memory()

    async def _save_session(self, session_id: str):
        """保存会话数据"""
        session_memory = self.sessions.get(session_id)
        if not session_memory:
            logger.warning(f"尝试保存不存在的会话: {session_id}")
            return

        try:
            logger.info(f"开始保存会话: {session_id}, 消息数: {session_memory.message_count}")

            # 准备会话数据
            session_data = {
                "session_id": session_memory.session_id,
                "created_at": session_memory.created_at.isoformat(),
                "last_activity": session_memory.last_activity.isoformat(),
                "message_count": session_memory.message_count,
                "metadata": session_memory.metadata,
                "entities": {
                    eid: {
                        "id": entity.id,
                        "type": entity.type,
                        "name": entity.name,
                        "aliases": entity.aliases,
                        "metadata": entity.metadata,
                        "created_at": entity.created_at.isoformat(),
                        "last_referenced": entity.last_referenced.isoformat(),
                        "reference_count": entity.reference_count
                    }
                    for eid, entity in session_memory.entities.items()
                },
                "summaries": [
                    {
                        "timestamp": summary.timestamp,
                        "summary": summary.summary,
                        "key_entities": summary.key_entities,
                        "message_count": summary.message_count,
                        "start_message_id": summary.start_message_id,
                        "end_message_id": summary.end_message_id
                    }
                    for summary in session_memory.summaries
                ]
            }

            # 保存会话文件
            session_file = self.memory_dir / f"session_{session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            logger.info(f"会话文件已保存: {session_file}")

            # 保存对话记录
            if session_memory.raw_messages:
                conv_file = self.memory_dir / f"conversation_{session_id}.json"
                with open(conv_file, 'w', encoding='utf-8') as f:
                    json.dump(session_memory.raw_messages, f, ensure_ascii=False, indent=2)
                logger.info(f"对话文件已保存: {conv_file}, 消息数: {len(session_memory.raw_messages)}")
            else:
                logger.warning(f"会话 {session_id} 没有原始消息可保存")

        except Exception as e:
            logger.error(f"保存会话失败 {session_id}: {e}", exc_info=True)

    def create_session(self, session_id: Optional[str] = None) -> str:
        """创建新会话"""
        if not session_id:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            random_hash = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:8]
            session_id = f"session_{timestamp}_{random_hash}"

        # 检查是否已存在该会话
        if session_id in self.sessions:
            logger.info(f"会话已存在: {session_id}")
            return session_id

        session_memory = SessionMemory(
            session_id=session_id,
            created_at=datetime.now(),
            last_activity=datetime.now(),
            message_count=0,
            metadata={}
        )

        self.sessions[session_id] = session_memory
        logger.info(f"创建新会话: {session_id}")

        return session_id

    def get_or_create_session(self, preferred_session_id: Optional[str] = None,
                             restore_recent: bool = True) -> str:
        """获取或创建会话（支持恢复最近会话）"""
        # 如果提供了首选会话ID，尝试使用它
        if preferred_session_id and preferred_session_id in self.sessions:
            logger.info(f"使用现有会话: {preferred_session_id}")
            return preferred_session_id

        # 如果启用了恢复功能，尝试查找最近的会话
        if restore_recent and not preferred_session_id:
            recent_session = self.find_recent_session(hours=6)  # 6小时内的会话
            if recent_session:
                logger.info(f"恢复最近会话: {recent_session}")
                return recent_session

        # 创建新会话
        if preferred_session_id:
            session_id = self.create_session(preferred_session_id)
        else:
            session_id = self.create_session()

        logger.info(f"创建新会话: {session_id}")
        return session_id

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """添加消息到会话"""
        if session_id not in self.sessions:
            self.create_session(session_id)

        session_memory = self.sessions[session_id]

        # 创建消息对象
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "message_id": session_memory.message_count,
            "metadata": metadata or {}
        }

        # 添加到原始消息
        session_memory.raw_messages.append(message)
        session_memory.message_count += 1
        session_memory.last_activity = datetime.now()

        # 禁用实体提取 - 只保留消息，不提取实体
        # 注释掉实体提取代码，避免抽取无关实体
        # if role == "user" and self.entity_tracker:
        #     try:
        #         # 使用智能实体跟踪器（异步）
        #         entities = await self.entity_tracker.extract_entities(content, role)
        #         for entity in entities:
        #             session_memory.entities[entity.id] = entity
        #     except Exception as e:
        #         logger.error(f"实体提取失败: {e}")
        #         # 失败时使用简单提取
        #         import re
        #         # 简单的股票代码提取（备用）
        #         stock_matches = re.findall(r'(\d{6})\.(?:sh|sz|ss)', content)
        #         for stock_code in stock_matches:
        #             entity_id = f"stock_{stock_code}"
        #             if entity_id not in session_memory.entities:
        #                 entity = Entity(
        #                     id=entity_id,
        #                     type="stock",
        #                     name=stock_code,
        #                     aliases=[f"{stock_code}.sh"],
        #                     metadata={"source": "regex_fallback"},
        #                     created_at=datetime.now(),
        #                     last_referenced=datetime.now(),
        #                     reference_count=1
        #                 )
        #                 session_memory.entities[entity_id] = entity

        # 检查是否需要压缩
        if self.compressor.should_compress(session_memory):
            # 检查是否是异步方法
            import inspect
            if inspect.iscoroutinefunction(self.compressor.compress_conversation):
                summary = await self.compressor.compress_conversation(session_memory)
            else:
                summary = self.compressor.compress_conversation(session_memory)

            if summary:
                session_memory.summaries.append(summary)

        # 异步保存
        asyncio.create_task(self._save_session(session_id))

        logger.info(f"添加消息到会话 {session_id}: {role} - {content[:50]}...")
        logger.info(f"  当前会话消息数: {session_memory.message_count}, 原始消息数: {len(session_memory.raw_messages)}")

    async def learn_from_tool(
        self,
        tool_name: str,
        tool_input: Dict,
        tool_output: str,
        user_message: Optional[str] = None
    ) -> bool:
        """从工具使用中学习"""
        if not self.memory_learner:
            return False

        try:
            result = await self.memory_learner.learn_from_tool_output(
                tool_name, tool_input, tool_output, user_message
            )

            if result.get("updated"):
                # 更新内存中的项目记忆
                self.project_memory = result.get("memory")
                return True

            return False

        except Exception as e:
            logger.error(f"从工具学习失败: {e}")
            return False

    async def get_enhanced_message(
        self,
        session_id: str,
        user_message: str
    ) -> str:
        """获取增强后的消息（包含上下文）"""
        session_memory = self.sessions.get(session_id)
        if not session_memory:
            return user_message

        # 使用压缩器增强消息
        project_memory_dict = None
        if self.project_memory:
            # 转换为字典格式
            project_memory_dict = {
                'user_directives': [
                    {
                        'directive': d.directive,
                        'priority': d.priority.value
                    }
                    for d in self.project_memory.user_directives
                ]
            }

        # 检查压缩器是否有异步方法
        if hasattr(self.compressor, 'enhance_message_with_context') and callable(self.compressor.enhance_message_with_context):
            # 检查是否是异步方法
            import inspect
            if inspect.iscoroutinefunction(self.compressor.enhance_message_with_context):
                enhanced = await self.compressor.enhance_message_with_context(
                    user_message, session_memory, project_memory_dict
                )
            else:
                enhanced = self.compressor.enhance_message_with_context(
                    user_message, session_memory, project_memory_dict
                )
        else:
            # 回退到简单增强
            enhanced = user_message

        return enhanced

    def get_context_summary(
        self,
        session_id: str,
        char_budget: int = 500
    ) -> str:
        """获取上下文摘要"""
        session_memory = self.sessions.get(session_id)
        if not session_memory:
            return ""

        # 创建记忆上下文
        context = MemoryContext(
            now=int(datetime.now().timestamp() * 1000)
        )

        # 使用格式化器生成摘要
        summary = self.formatter.format_context_summary(
            self.project_memory, session_memory, context
        )

        # 如果摘要太长，使用压缩器生成更简洁的版本
        if len(summary) > char_budget:
            summary = self.compressor.format_compressed_context(
                session_memory, char_budget
            )

        return summary

    def get_session_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """获取会话历史（前端格式）"""
        session_memory = self.sessions.get(session_id)
        if not session_memory:
            logger.warning(f"会话不存在: {session_id}")
            return []

        logger.info(f"获取会话历史: {session_id}, 原始消息数: {len(session_memory.raw_messages)}, 摘要数: {len(session_memory.summaries)}")

        # 只返回原始消息（前端期望用户和机器人消息）
        history = []

        # 添加原始消息
        for msg in session_memory.raw_messages[-limit:]:
            try:
                # 确保消息格式正确
                timestamp = datetime.fromisoformat(msg["timestamp"])
                history.append({
                    "text": msg["content"],
                    "sender": msg["role"],
                    "timestamp": timestamp.strftime("%H:%M:%S"),
                    "date": timestamp.strftime("%Y-%m-%d")
                })
            except Exception as e:
                logger.error(f"格式化消息失败: {e}, 消息: {msg}")

        logger.info(f"返回历史消息数量: {len(history)}")
        return history

    def clear_session_history(self, session_id: str):
        """清空会话历史"""
        if session_id in self.sessions:
            session_memory = self.sessions[session_id]
            session_memory.raw_messages = []
            session_memory.summaries = []
            session_memory.entities = {}
            session_memory.message_count = 0
            session_memory.last_activity = datetime.now()

            # 异步保存
            asyncio.create_task(self._save_session(session_id))

            logger.info(f"清空会话历史: {session_id}")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_sessions = len(self.sessions)
        active_sessions = sum(
            1 for s in self.sessions.values()
            if (datetime.now() - s.last_activity).total_seconds() < 3600
        )

        total_messages = sum(s.message_count for s in self.sessions.values())

        stats = {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "total_messages": total_messages,
            "memory_dir": str(self.memory_dir.absolute())
        }

        if self.project_memory:
            stats.update({
                "user_directives_count": len(self.project_memory.user_directives),
                "hot_paths_count": len(self.project_memory.hot_paths),
                "custom_notes_count": len(self.project_memory.custom_notes),
                "user_preferences_count": len(self.project_memory.user_preferences),
            })

        return stats

    def cleanup_old_sessions(self, days: int = 7):
        """清理旧会话"""
        cutoff_date = datetime.now() - datetime.timedelta(days=days)
        sessions_to_remove = []

        for session_id, session_memory in self.sessions.items():
            if session_memory.last_activity < cutoff_date:
                sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            # 删除会话文件
            session_file = self.memory_dir / f"session_{session_id}.json"
            conv_file = self.memory_dir / f"conversation_{session_id}.json"

            for file_path in [session_file, conv_file]:
                if file_path.exists():
                    try:
                        file_path.unlink()
                    except Exception as e:
                        logger.error(f"删除文件失败 {file_path}: {e}")

            # 从内存中移除
            del self.sessions[session_id]

        if sessions_to_remove:
            logger.info(f"清理了 {len(sessions_to_remove)} 个旧会话")

    def search_conversations(self, query: str, limit: int = 10) -> List[Dict]:
        """搜索对话"""
        results = []

        for session_id, session_memory in self.sessions.items():
            # 搜索原始消息
            for msg in session_memory.raw_messages:
                if query.lower() in msg["content"].lower():
                    results.append({
                        "session_id": session_id,
                        "role": msg["role"],
                        "content": msg["content"],
                        "timestamp": msg["timestamp"],
                        "message_id": msg.get("message_id", 0)
                    })

                    if len(results) >= limit:
                        break

            if len(results) >= limit:
                break

        return results[:limit]

    def find_recent_session(self, hours: int = 24) -> Optional[str]:
        """查找最近的活动会话"""
        recent_sessions = []

        for session_id, session_memory in self.sessions.items():
            time_diff = (datetime.now() - session_memory.last_activity).total_seconds()
            if time_diff < hours * 3600:  # 在指定小时内
                recent_sessions.append((session_id, session_memory.last_activity))

        if not recent_sessions:
            return None

        # 返回最新的会话
        recent_sessions.sort(key=lambda x: x[1], reverse=True)
        return recent_sessions[0][0]

    def merge_sessions(self, source_session_id: str, target_session_id: str) -> bool:
        """合并两个会话"""
        if source_session_id not in self.sessions or target_session_id not in self.sessions:
            logger.error(f"无法合并会话: 源会话 {source_session_id} 或目标会话 {target_session_id} 不存在")
            return False

        source_session = self.sessions[source_session_id]
        target_session = self.sessions[target_session_id]

        try:
            # 合并原始消息（按时间排序）
            all_messages = source_session.raw_messages + target_session.raw_messages
            all_messages.sort(key=lambda x: x.get("timestamp", ""))

            # 限制消息数量
            if len(all_messages) > MAX_RAW_MESSAGES * 2:
                all_messages = all_messages[-(MAX_RAW_MESSAGES * 2):]

            target_session.raw_messages = all_messages

            # 合并实体
            for entity_id, entity in source_session.entities.items():
                if entity_id not in target_session.entities:
                    target_session.entities[entity_id] = entity
                else:
                    # 更新引用计数
                    target_entity = target_session.entities[entity_id]
                    target_entity.reference_count += entity.reference_count
                    target_entity.last_referenced = max(
                        target_entity.last_referenced, entity.last_referenced
                    )

            # 合并摘要
            target_session.summaries.extend(source_session.summaries)

            # 更新消息计数
            target_session.message_count = len(target_session.raw_messages)
            target_session.last_activity = max(
                source_session.last_activity, target_session.last_activity
            )

            # 删除源会话
            del self.sessions[source_session_id]

            # 异步保存目标会话
            asyncio.create_task(self._save_session(target_session_id))

            # 删除源会话文件
            session_file = self.memory_dir / f"session_{source_session_id}.json"
            conv_file = self.memory_dir / f"conversation_{source_session_id}.json"

            for file_path in [session_file, conv_file]:
                if file_path.exists():
                    try:
                        file_path.unlink()
                    except Exception as e:
                        logger.error(f"删除文件失败 {file_path}: {e}")

            logger.info(f"成功合并会话: {source_session_id} -> {target_session_id}")
            return True

        except Exception as e:
            logger.error(f"合并会话失败: {e}", exc_info=True)
            return False

    # 用户偏好方法（向后兼容）
    def get_user_preference(self, key: str, default: Any = None) -> Any:
        """获取用户偏好"""
        if self.project_memory:
            return self.project_memory.user_preferences.get(key, default)
        return default

    def set_user_preference(self, key: str, value: Any):
        """设置用户偏好"""
        if not self.project_memory:
            self.project_memory = ProjectMemory(project_root=str(self.project_root))

        self.project_memory.user_preferences[key] = value

        # 异步保存
        if self.memory_learner:
            asyncio.create_task(self._save_project_memory_async())

    async def _save_project_memory_async(self):
        """异步保存项目记忆"""
        if self.memory_learner and self.project_memory:
            await self.memory_learner._save_project_memory(self.project_memory)


# 单例实例
memory_manager: Optional[MemoryManager] = None


async def initialize_memory_manager(
    memory_dir: str = "chat_memory",
    project_root: Optional[str] = None
) -> bool:
    """初始化记忆管理器（全局）"""
    global memory_manager

    memory_manager = MemoryManager(memory_dir, project_root)
    return await memory_manager.initialize()


def get_memory_manager() -> MemoryManager:
    """获取记忆管理器实例"""
    global memory_manager
    if memory_manager is None:
        raise RuntimeError("记忆管理器未初始化，请先调用 initialize_memory_manager")
    return memory_manager