#!/usr/bin/env python3
"""
智能记忆系统
仿照 oh-my-claudecode 的多层记忆架构
"""

from .types import (
    Entity, UserDirective, HotPath, CustomNote,
    ConversationSummary, SessionMemory, ProjectMemory,
    MemoryContext, MemorySource, Priority,
    SUMMARY_CHAR_BUDGET, MAX_HOT_PATH_ITEMS,
    MAX_DIRECTIVE_ITEMS, MAX_LEARNING_ITEMS,
    MAX_RAW_MESSAGES, SUMMARY_INTERVAL,
    CACHE_EXPIRY_MS
)

from .entity_tracker import EntityTracker
from .directive_detector import DirectiveDetector
from .formatter import MemoryFormatter
from .learner import MemoryLearner
from .compressor import MemoryCompressor

__all__ = [
    # 类型
    'Entity', 'UserDirective', 'HotPath', 'CustomNote',
    'ConversationSummary', 'SessionMemory', 'ProjectMemory',
    'MemoryContext', 'MemorySource', 'Priority',

    # 常量
    'SUMMARY_CHAR_BUDGET', 'MAX_HOT_PATH_ITEMS',
    'MAX_DIRECTIVE_ITEMS', 'MAX_LEARNING_ITEMS',
    'MAX_RAW_MESSAGES', 'SUMMARY_INTERVAL',
    'CACHE_EXPIRY_MS',

    # 组件
    'EntityTracker', 'DirectiveDetector',
    'MemoryFormatter', 'MemoryLearner', 'MemoryCompressor',
]