#!/usr/bin/env python3
"""
记忆系统类型定义
仿照 oh-my-claudecode 的多层记忆架构
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path


class MemorySource(str, Enum):
    """记忆来源"""
    EXPLICIT = "explicit"      # 显式用户指令
    INFERRED = "inferred"      # 推断的模式
    LEARNED = "learned"        # 从工具使用中学习
    MANUAL = "manual"          # 手动添加


class Priority(str, Enum):
    """优先级"""
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class Entity:
    """实体（股票、文件、命令等）"""
    id: str                    # 实体ID
    type: str                  # 类型：stock, file, command, user, etc.
    name: str                  # 名称
    aliases: List[str] = field(default_factory=list)  # 别名/指代词
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    last_referenced: datetime = field(default_factory=datetime.now)
    reference_count: int = 0   # 引用次数


@dataclass
class UserDirective:
    """用户指令（必须存活压缩）"""
    timestamp: int                    # 时间戳
    directive: str                    # 指令内容
    context: str                     # 上下文
    source: MemorySource             # 来源
    priority: Priority               # 优先级
    entities: List[str] = field(default_factory=list)  # 相关实体ID


@dataclass
class HotPath:
    """热路径（频繁访问的文件/目录）"""
    path: str                        # 相对路径
    access_count: int                # 访问次数
    last_accessed: int               # 最后访问时间戳
    type: str                        # 类型：file, directory


@dataclass
class CustomNote:
    """自定义笔记（从错误/学习中获取）"""
    timestamp: int                    # 时间戳
    source: MemorySource             # 来源
    category: str                    # 类别：env, dependency, runtime, etc.
    content: str                     # 内容
    entities: List[str] = field(default_factory=list)  # 相关实体ID


@dataclass
class ConversationSummary:
    """对话摘要（替代原始历史）"""
    timestamp: int                    # 时间戳
    summary: str                     # 摘要内容
    key_entities: List[str] = field(default_factory=list)  # 关键实体ID
    message_count: int = 0           # 涵盖的消息数量
    start_message_id: int = 0        # 起始消息ID
    end_message_id: int = 0          # 结束消息ID


@dataclass
class SessionMemory:
    """会话记忆"""
    session_id: str                  # 会话ID
    created_at: datetime             # 创建时间
    last_activity: datetime          # 最后活动时间
    message_count: int = 0           # 消息总数
    entities: Dict[str, Entity] = field(default_factory=dict)  # 会话内实体
    summaries: List[ConversationSummary] = field(default_factory=list)  # 对话摘要
    raw_messages: List[Dict] = field(default_factory=list)  # 原始消息（有限）
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据


@dataclass
class ProjectMemory:
    """项目记忆（跨会话）"""
    version: str = "1.0.0"
    last_scanned: int = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    project_root: str = ""           # 项目根目录
    user_directives: List[UserDirective] = field(default_factory=list)  # 用户指令
    hot_paths: List[HotPath] = field(default_factory=list)  # 热路径
    custom_notes: List[CustomNote] = field(default_factory=list)  # 自定义笔记
    user_preferences: Dict[str, Any] = field(default_factory=dict)  # 用户偏好
    entities: Dict[str, Entity] = field(default_factory=dict)  # 全局实体


@dataclass
class MemoryContext:
    """记忆上下文（用于格式化）"""
    working_directory: Optional[str] = None
    scope_key: Optional[str] = None
    now: Optional[int] = None        # 当前时间戳


# 常量定义
SUMMARY_CHAR_BUDGET = 650            # 摘要字符预算
MAX_HOT_PATH_ITEMS = 3               # 最大热路径显示数量
MAX_DIRECTIVE_ITEMS = 3              # 最大指令显示数量
MAX_LEARNING_ITEMS = 3               # 最大学习项显示数量
MAX_RAW_MESSAGES = 20                # 保留的原始消息数量
SUMMARY_INTERVAL = 10                # 每N条消息生成摘要
CACHE_EXPIRY_MS = 24 * 60 * 60 * 1000  # 缓存过期时间（24小时）