#!/usr/bin/env python3
"""
记忆格式化器
仿照 oh-my-claudecode 的 formatter.ts，生成智能压缩的上下文
"""

from typing import List, Dict, Optional
from datetime import datetime
from .types import (
    ProjectMemory, SessionMemory, MemoryContext,
    UserDirective, HotPath, CustomNote, Entity,
    ConversationSummary, Priority,
    SUMMARY_CHAR_BUDGET, MAX_HOT_PATH_ITEMS,
    MAX_DIRECTIVE_ITEMS, MAX_LEARNING_ITEMS
)


class MemoryFormatter:
    """记忆格式化器"""

    def format_context_summary(
        self,
        project_memory: Optional[ProjectMemory],
        session_memory: Optional[SessionMemory],
        context: Optional[MemoryContext] = None
    ) -> str:
        """格式化上下文摘要（仿照 oh-my-claudecode 的 formatContextSummary）"""
        if context is None:
            context = MemoryContext()

        lines: List[str] = []
        push_tier = self._create_bounded_tier_writer(lines)

        # 第1层：项目环境
        if project_memory:
            push_tier(self._format_environment_tier(project_memory))

        # 第2层：热路径
        if project_memory:
            push_tier(self._format_hot_paths_tier(project_memory, context))

        # 第3层：用户指令
        if project_memory:
            push_tier(self._format_directives_tier(project_memory))

        # 第4层：学习笔记
        if project_memory:
            push_tier(self._format_learnings_tier(project_memory, context))

        # 第5层：会话实体
        if session_memory:
            push_tier(self._format_session_entities_tier(session_memory))

        # 第6层：对话摘要
        if session_memory:
            push_tier(self._format_conversation_summary_tier(session_memory))

        summary = "\n".join(lines)
        return self._trim_to_budget(summary, SUMMARY_CHAR_BUDGET)

    def format_full_context(
        self,
        project_memory: Optional[ProjectMemory],
        session_memory: Optional[SessionMemory]
    ) -> str:
        """格式化完整上下文（用于调试）"""
        lines: List[str] = ["<记忆上下文>"]

        if project_memory:
            lines.extend(self._format_project_memory_details(project_memory))

        if session_memory:
            lines.extend(self._format_session_memory_details(session_memory))

        lines.append("</记忆上下文>")
        return "\n".join(lines)

    def _format_environment_tier(self, memory: ProjectMemory) -> List[str]:
        """格式化环境层"""
        lines: List[str] = []

        # 提取关键信息
        key_info = []

        # 用户偏好
        if memory.user_preferences:
            prefs = list(memory.user_preferences.keys())[:3]
            if prefs:
                key_info.append(f"偏好: {', '.join(prefs)}")

        # 如果有任何信息，添加标题
        if key_info:
            lines.append("[环境]")
            lines.extend(f"- {info}" for info in key_info)

        return lines

    def _format_hot_paths_tier(
        self,
        memory: ProjectMemory,
        context: MemoryContext
    ) -> List[str]:
        """格式化热路径层"""
        if not memory.hot_paths:
            return []

        # 获取热门路径
        top_paths = self._get_top_hot_paths(
            memory.hot_paths,
            MAX_HOT_PATH_ITEMS,
            context
        )

        if not top_paths:
            return []

        lines = ["[常用路径]"]
        for hot_path in top_paths:
            lines.append(f"- {hot_path.path} ({hot_path.access_count}次)")

        return lines

    def _format_directives_tier(self, memory: ProjectMemory) -> List[str]:
        """格式化指令层"""
        if not memory.user_directives:
            return []

        # 按优先级和时间排序
        directives = sorted(
            memory.user_directives,
            key=lambda d: self._score_directive(d),
            reverse=True
        )[:MAX_DIRECTIVE_ITEMS]

        lines = ["[用户指令]"]
        for directive in directives:
            priority_marker = "⚠️" if directive.priority == Priority.HIGH else "•"
            lines.append(f"{priority_marker} {directive.directive}")

        return lines

    def _format_learnings_tier(
        self,
        memory: ProjectMemory,
        context: MemoryContext
    ) -> List[str]:
        """格式化学习层"""
        if not memory.custom_notes:
            return []

        # 按相关性排序
        notes = sorted(
            memory.custom_notes,
            key=lambda n: self._score_learning(n, context),
            reverse=True
        )[:MAX_LEARNING_ITEMS]

        lines = ["[学习笔记]"]
        for note in notes:
            lines.append(f"- [{note.category}] {note.content}")

        return lines

    def _format_session_entities_tier(self, memory: SessionMemory) -> List[str]:
        """格式化会话实体层"""
        if not memory.entities:
            return []

        # 获取最近引用的实体
        recent_entities = sorted(
            memory.entities.values(),
            key=lambda e: e.last_referenced,
            reverse=True
        )[:5]

        lines = ["[对话实体]"]
        for entity in recent_entities:
            ref_text = f"({entity.reference_count}次引用)"
            lines.append(f"- {entity.type}: {entity.name} {ref_text}")

        return lines

    def _format_conversation_summary_tier(self, memory: SessionMemory) -> List[str]:
        """格式化对话摘要层"""
        if not memory.summaries:
            return []

        # 获取最新摘要
        latest_summary = max(memory.summaries, key=lambda s: s.timestamp)

        lines = ["[对话摘要]"]
        lines.append(f"- {latest_summary.summary}")

        # 如果有关键实体
        if latest_summary.key_entities:
            entity_names = []
            for entity_id in latest_summary.key_entities[:3]:
                entity = memory.entities.get(entity_id)
                if entity:
                    entity_names.append(entity.name)
            if entity_names:
                lines.append(f"- 涉及: {', '.join(entity_names)}")

        return lines

    def _format_project_memory_details(self, memory: ProjectMemory) -> List[str]:
        """格式化项目记忆详情"""
        lines: List[str] = []

        lines.append("## 项目记忆")

        # 用户指令
        if memory.user_directives:
            lines.append("### 用户指令")
            for directive in memory.user_directives:
                priority = "高" if directive.priority == Priority.HIGH else "普通"
                lines.append(f"- [{priority}] {directive.directive}")
                if directive.context:
                    lines.append(f"  上下文: {directive.context}")
            lines.append("")

        # 热路径
        if memory.hot_paths:
            lines.append("### 常用路径")
            for hot_path in sorted(memory.hot_paths, key=lambda h: -h.access_count)[:10]:
                lines.append(f"- {hot_path.path}: {hot_path.access_count}次访问")
            lines.append("")

        # 自定义笔记
        if memory.custom_notes:
            lines.append("### 学习笔记")
            for note in memory.custom_notes:
                lines.append(f"- [{note.category}] {note.content}")
            lines.append("")

        # 用户偏好
        if memory.user_preferences:
            lines.append("### 用户偏好")
            for key, value in list(memory.user_preferences.items())[:10]:
                lines.append(f"- {key}: {value}")
            lines.append("")

        return lines

    def _format_session_memory_details(self, memory: SessionMemory) -> List[str]:
        """格式化会话记忆详情"""
        lines: List[str] = []

        lines.append("## 会话记忆")

        # 实体
        if memory.entities:
            lines.append("### 实体")
            for entity in memory.entities.values():
                lines.append(f"- {entity.type}: {entity.name}")
                if entity.aliases:
                    lines.append(f"  别名: {', '.join(entity.aliases)}")
                lines.append(f"  引用次数: {entity.reference_count}")
            lines.append("")

        # 对话摘要
        if memory.summaries:
            lines.append("### 对话摘要")
            for summary in sorted(memory.summaries, key=lambda s: s.timestamp, reverse=True)[:3]:
                time_str = datetime.fromtimestamp(summary.timestamp / 1000).strftime("%H:%M:%S")
                lines.append(f"- [{time_str}] {summary.summary}")
            lines.append("")

        # 原始消息统计
        lines.append(f"### 消息统计")
        lines.append(f"- 总消息数: {memory.message_count}")
        lines.append(f"- 保留原始消息: {len(memory.raw_messages)}")
        lines.append("")

        return lines

    def _create_bounded_tier_writer(self, lines: List[str]):
        """创建有界的层写入器"""
        def push_tier(tier_lines: List[str]):
            if not tier_lines:
                return

            if lines:
                lines.append("")

            lines.extend(tier_lines)

        return push_tier

    def _trim_to_budget(self, summary: str, budget: int) -> str:
        """修剪到预算内"""
        if len(summary) <= budget:
            return summary

        # 保留完整行，直到超出预算
        lines = summary.split('\n')
        result_lines = []
        current_length = 0

        for line in lines:
            line_with_newline = line + '\n'
            if current_length + len(line_with_newline) > budget - 1:
                break
            result_lines.append(line)
            current_length += len(line_with_newline)

        if result_lines:
            return '\n'.join(result_lines).rstrip() + '…'
        else:
            return summary[:budget - 1] + '…'

    def _score_directive(self, directive: UserDirective) -> int:
        """评分指令"""
        priority_score = {
            Priority.HIGH: 1_000_000_000_000,
            Priority.NORMAL: 100_000_000,
            Priority.LOW: 0
        }.get(directive.priority, 0)

        return priority_score + directive.timestamp

    def _score_learning(self, note: CustomNote, context: MemoryContext) -> int:
        """评分学习笔记"""
        # 类别权重
        category_weights = {
            'env': 60,
            'runtime': 50,
            'dependency': 40,
            'deploy': 30,
            'test': 20,
            'build': 15,
            'config': 10,
        }

        now = context.now or int(datetime.now().timestamp() * 1000)
        age_hours = max(0, now - note.timestamp) // (60 * 60 * 1000)
        recency_weight = max(0, 100 - age_hours)

        category_weight = category_weights.get(note.category, 10)

        return recency_weight + category_weight

    def _get_top_hot_paths(
        self,
        hot_paths: List[HotPath],
        limit: int,
        context: MemoryContext
    ) -> List[HotPath]:
        """获取热门路径"""
        if not hot_paths:
            return []

        # 按访问次数和时间排序
        sorted_paths = sorted(
            hot_paths,
            key=lambda h: (h.access_count, h.last_accessed),
            reverse=True
        )

        return sorted_paths[:limit]

    def _normalize_scope_path(self, working_directory: Optional[str]) -> Optional[str]:
        """标准化作用域路径"""
        if not working_directory:
            return None

        # 简化路径处理
        import os
        normalized = os.path.normpath(working_directory)
        if normalized in ['.', '']:
            return None

        return normalized