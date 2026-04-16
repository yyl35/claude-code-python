#!/usr/bin/env python3
"""
记忆压缩器
智能压缩对话历史，生成摘要（仿照 oh-my-claudecode 的压缩机制）
"""

import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from .types import (
    ConversationSummary, Entity, SessionMemory,
    SUMMARY_INTERVAL, MAX_RAW_MESSAGES
)
from .entity_tracker import EntityTracker


class MemoryCompressor:
    """记忆压缩器"""

    def __init__(self):
        self.entity_tracker = EntityTracker()

    def should_compress(self, session_memory: SessionMemory) -> bool:
        """检查是否应该压缩"""
        # 每 N 条消息压缩一次
        if len(session_memory.raw_messages) >= SUMMARY_INTERVAL:
            return True

        # 或者原始消息数量超过限制
        if len(session_memory.raw_messages) > MAX_RAW_MESSAGES * 2:
            return True

        return False

    def compress_conversation(self, session_memory: SessionMemory) -> Optional[ConversationSummary]:
        """压缩对话，生成摘要"""
        if not session_memory.raw_messages or len(session_memory.raw_messages) < 3:
            return None

        try:
            # 提取关键信息（禁用实体提取）
            key_entities = []  # 清空实体列表，避免无关实体影响摘要
            topics = self._extract_topics(session_memory.raw_messages)
            actions = self._extract_actions(session_memory.raw_messages)

            # 生成摘要（不包含实体信息）
            summary_text = self._generate_summary(topics, actions, [])

            # 创建摘要对象
            summary = ConversationSummary(
                timestamp=int(datetime.now().timestamp() * 1000),
                summary=summary_text,
                key_entities=[],  # 清空关键实体
                message_count=len(session_memory.raw_messages),
                start_message_id=session_memory.raw_messages[0].get('message_id', 0),
                end_message_id=session_memory.raw_messages[-1].get('message_id', 0)
            )

            # 清理原始消息（保留最近的一些）
            self._cleanup_raw_messages(session_memory)

            return summary

        except Exception as e:
            print(f"压缩对话失败: {e}")
            return None

    def _extract_key_entities(self, session_memory: SessionMemory) -> List[str]:
        """提取关键实体"""
        # 按引用次数排序
        entities_by_ref = sorted(
            session_memory.entities.values(),
            key=lambda e: e.reference_count,
            reverse=True
        )

        # 取引用次数最多的实体
        key_entities = []
        for entity in entities_by_ref[:5]:  # 最多5个关键实体
            if entity.reference_count >= 2:  # 至少被引用2次
                key_entities.append(entity.id)

        return key_entities

    def _extract_topics(self, messages: List[Dict]) -> List[str]:
        """提取对话主题（简化版，避免提取无关信息）"""
        topics = []
        all_text = ' '.join(msg.get('content', '') for msg in messages)

        # 简化的主题模式 - 只基于对话内容，不扫描工作区
        topic_patterns = [
            # 科学知识
            (r'黑洞|引力透镜|宇宙|天体|物理|爱因斯坦|相对论', '科学知识'),

            # 技术操作
            (r'Linux|硬盘|磁盘|占用|命令|df|du', '系统操作'),
            (r'查看|命令是什么|怎么用', '技术指导'),

            # 记忆测试
            (r'记忆|刚才|之前|问过|测试', '记忆测试'),

            # 问题质疑
            (r'为什么|有什么关系|无关|质疑', '问题澄清'),
        ]

        for pattern, topic_name in topic_patterns:
            if re.search(pattern, all_text, re.IGNORECASE):
                topics.append(topic_name)

        # 去重
        unique_topics = list(dict.fromkeys(topics))

        # 限制主题数量
        if len(unique_topics) > 3:
            unique_topics = unique_topics[:3]

        return unique_topics

    def _extract_actions(self, messages: List[Dict]) -> List[str]:
        """提取执行的动作"""
        actions = []

        for msg in messages:
            content = msg.get('content', '').lower()
            role = msg.get('role', '')

            if role == 'bot':
                # 从助手回复中提取动作
                action_patterns = [
                    (r'已执行\s+(.+)', '执行'),
                    (r'已读取\s+(.+)', '读取'),
                    (r'已创建\s+(.+)', '创建'),
                    (r'已修改\s+(.+)', '修改'),
                    (r'已获取\s+(.+)', '获取'),
                    (r'已分析\s+(.+)', '分析'),
                    (r'结果如下', '返回结果'),
                    (r'错误[:：]', '报错'),
                ]

                for pattern, action_name in action_patterns:
                    if re.search(pattern, content):
                        actions.append(action_name)
                        break

        # 去重并限制数量
        unique_actions = list(dict.fromkeys(actions))
        return unique_actions[:5]  # 最多5个动作

    def _generate_summary(self, topics: List[str], actions: List[str], key_entities: List[str]) -> str:
        """生成摘要文本（简化版）"""
        # 如果主题明确，基于主题生成摘要
        if topics:
            if "科学知识" in topics:
                return "讨论了科学概念如黑洞、引力透镜等。"
            elif "系统操作" in topics:
                return "讨论了Linux系统操作和命令使用。"
            elif "记忆测试" in topics:
                return "测试了AI助手的记忆和对话回顾能力。"
            elif "问题澄清" in topics:
                return "用户对之前的回答提出质疑和澄清。"

        # 如果有动作，生成相应摘要
        if actions:
            if len(actions) == 1:
                return f"执行了{actions[0]}操作。"
            else:
                return f"执行了多个操作。"

        # 默认摘要
        return "进行了一段对话。"

    def _cleanup_raw_messages(self, session_memory: SessionMemory):
        """清理原始消息"""
        # 保留最近的消息
        keep_count = min(MAX_RAW_MESSAGES, len(session_memory.raw_messages) // 2)
        if keep_count > 0:
            session_memory.raw_messages = session_memory.raw_messages[-keep_count:]
        else:
            session_memory.raw_messages = []

    def enhance_message_with_context(
        self,
        message: str,
        session_memory: SessionMemory,
        project_memory: Optional[Dict] = None
    ) -> str:
        """使用上下文增强消息"""
        enhanced_parts = []

        # 添加最近的对话历史（最重要的部分！）
        recent_history = self._get_recent_conversation_history(session_memory)
        if recent_history:
            enhanced_parts.append(f"最近的对话历史:\n{recent_history}")

        # 禁用实体解析 - 避免抽取无关实体
        # resolved_entities = self._resolve_entities_in_message(message, session_memory)
        # if resolved_entities:
        #     enhanced_parts.append(f"实体解析: {resolved_entities}")

        # 添加上下文摘要
        if session_memory.summaries:
            latest_summary = max(session_memory.summaries, key=lambda s: s.timestamp)
            enhanced_parts.append(f"对话摘要: {latest_summary.summary}")

        # 添加用户指令（如果有）
        if project_memory and 'user_directives' in project_memory:
            directives = project_memory['user_directives']
            if directives:
                # 取最近的高优先级指令
                high_priority = [d for d in directives if d.get('priority') == 'high']
                if high_priority:
                    directive = high_priority[0]
                    enhanced_parts.append(f"用户指令: {directive.get('directive', '')}")

        # 组合增强内容
        if enhanced_parts:
            context = "\n".join(enhanced_parts)
            enhanced_message = f"""【系统提示：以下是当前对话的上下文信息，请仔细阅读并参考】

{context}

【用户当前消息】
{message}

【指令】
请根据上述对话历史理解用户的意图和指代。
当用户提到"刚才"、"之前"、"上面说的"、"我问过"等指代词时，请参考对话历史。
你有完整的对话历史可以访问，请基于这些信息回答问题。"""
            return enhanced_message

        # 即使没有其他上下文，也至少添加一个简单的系统提示
        return f"""【系统提示：请参考对话历史回答用户问题】

【用户当前消息】
{message}

【指令】
请基于对话历史理解用户的意图，特别是当用户提到过去的问题时。"""

    def _resolve_entities_in_message(self, message: str, session_memory: SessionMemory) -> str:
        """解析消息中的实体指代"""
        # 首先检查是否有指代词（如"这个股票"）
        referenced_entity = self._resolve_reference_from_session(message, session_memory)
        if referenced_entity:
            return f"'{message}' 指代 {referenced_entity.type}: {referenced_entity.name}"

        # 检查消息中是否有新的实体
        extracted = self.entity_tracker.extract_entities(message)
        if extracted:
            entity_names = [e.name for e in extracted[:3]]  # 最多3个
            return f"识别到实体: {', '.join(entity_names)}"

        return ""

    def _resolve_reference_from_session(self, message: str, session_memory: SessionMemory) -> Optional[Entity]:
        """从会话记忆中解析指代词"""
        import re

        # 指代模式
        reference_patterns = [
            (r'这个\s*(股票|文件|命令|目录)', "this"),
            (r'那个\s*(股票|文件|命令|目录)', "that"),
            (r'刚才\s*(说的|提到的|查询的)', "previous"),
            (r'之前\s*(说的|提到的|查询的)', "previous"),
            (r'上面\s*(说的|提到的)', "above"),
        ]

        for pattern, ref_type in reference_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                # 获取指代的实体类型
                if match.groups():
                    ref_entity_type = match.group(1)
                    # 中文类型映射到英文类型
                    type_map = {
                        "股票": "stock",
                        "文件": "file",
                        "命令": "command",
                        "目录": "directory"
                    }
                    entity_type = type_map.get(ref_entity_type)
                else:
                    entity_type = None

                # 从会话记忆中查找实体
                entities = list(session_memory.entities.values())
                if not entities:
                    return None

                if ref_type == "this" or ref_type == "that":
                    # "这个股票" -> 最后提到的该类型实体
                    if entity_type:
                        # 按最后引用时间排序
                        typed_entities = [e for e in entities if e.type == entity_type]
                        if typed_entities:
                            return max(typed_entities, key=lambda e: e.last_referenced)
                    else:
                        # 没有指定类型，返回最后引用的任何实体
                        return max(entities, key=lambda e: e.last_referenced)

                elif ref_type == "previous":
                    # "刚才说的" -> 最近提到的实体
                    return max(entities, key=lambda e: e.last_referenced)

                elif ref_type == "above":
                    # "上面说的" -> 较早提到的实体（按时间正序）
                    if entity_type:
                        typed_entities = [e for e in entities if e.type == entity_type]
                        if typed_entities:
                            return min(typed_entities, key=lambda e: e.last_referenced)
                    else:
                        return min(entities, key=lambda e: e.last_referenced)

        return None

    def format_compressed_context(
        self,
        session_memory: SessionMemory,
        char_budget: int = 500
    ) -> str:
        """格式化压缩后的上下文"""
        lines = []

        # 添加最新摘要
        if session_memory.summaries:
            latest_summary = max(session_memory.summaries, key=lambda s: s.timestamp)
            lines.append(f"[对话摘要] {latest_summary.summary}")

            # 添加关键实体
            if latest_summary.key_entities:
                entity_names = []
                for entity_id in latest_summary.key_entities[:3]:
                    entity = session_memory.entities.get(entity_id)
                    if entity:
                        entity_names.append(f"{entity.type}:{entity.name}")
                if entity_names:
                    lines.append(f"[关键实体] {', '.join(entity_names)}")

        # 添加最近的消息（如果有空间）
        remaining_budget = char_budget - sum(len(line) + 1 for line in lines)
        if remaining_budget > 50 and session_memory.raw_messages:
            recent_messages = self._get_recent_messages_for_context(
                session_memory.raw_messages,
                remaining_budget
            )
            if recent_messages:
                lines.append("[最近消息]")
                lines.extend(recent_messages)

        return "\n".join(lines)

    def _get_recent_conversation_history(self, session_memory: SessionMemory, max_messages: int = 5) -> str:
        """获取最近的对话历史"""
        if not session_memory.raw_messages:
            return ""

        # 获取最近的消息
        recent_messages = session_memory.raw_messages[-max_messages:]

        history_lines = []
        for msg in recent_messages:
            role = "用户" if msg.get('role') == 'user' else "助手"
            content = msg.get('content', '')

            # 截断过长的内容
            if len(content) > 200:
                content = content[:197] + "..."

            history_lines.append(f"{role}: {content}")

        return "\n".join(history_lines)

    def _get_recent_messages_for_context(
        self,
        messages: List[Dict],
        budget: int
    ) -> List[str]:
        """获取适合上下文的最近消息"""
        context_messages = []
        current_length = 0

        # 从最新消息开始
        for msg in reversed(messages):
            role = "用户" if msg.get('role') == 'user' else "助手"
            content = msg.get('content', '')
            preview = content[:50] + ('...' if len(content) > 50 else '')

            line = f"{role}: {preview}"
            line_length = len(line) + 1  # +1 for newline

            if current_length + line_length > budget:
                break

            context_messages.insert(0, line)  # 保持时间顺序
            current_length += line_length

            if len(context_messages) >= 3:  # 最多3条消息
                break

        return context_messages

    def merge_summaries(self, summaries: List[ConversationSummary]) -> List[ConversationSummary]:
        """合并相似的摘要"""
        if len(summaries) <= 1:
            return summaries

        merged = []
        current_summary = summaries[0]

        for next_summary in summaries[1:]:
            # 检查是否可以合并（时间接近且主题相似）
            time_gap = next_summary.timestamp - current_summary.end_message_id
            can_merge = (
                time_gap < 5 * 60 * 1000 and  # 5分钟内
                self._summaries_are_similar(current_summary, next_summary)
            )

            if can_merge:
                # 合并摘要
                current_summary = self._merge_two_summaries(current_summary, next_summary)
            else:
                merged.append(current_summary)
                current_summary = next_summary

        merged.append(current_summary)
        return merged

    def _summaries_are_similar(self, s1: ConversationSummary, s2: ConversationSummary) -> bool:
        """检查两个摘要是否相似"""
        # 检查是否有重叠的实体
        s1_entities = set(s1.key_entities)
        s2_entities = set(s2.key_entities)
        entity_overlap = len(s1_entities & s2_entities) > 0

        # 检查摘要文本的相似性（简单关键词匹配）
        s1_words = set(s1.summary.lower().split())
        s2_words = set(s2.summary.lower().split())
        word_overlap = len(s1_words & s2_words) / max(len(s1_words), 1) > 0.3

        return entity_overlap or word_overlap

    def _merge_two_summaries(self, s1: ConversationSummary, s2: ConversationSummary) -> ConversationSummary:
        """合并两个摘要"""
        # 合并实体
        merged_entities = list(set(s1.key_entities + s2.key_entities))

        # 生成新的摘要文本
        if s1.summary.endswith('。'):
            s1_summary = s1.summary[:-1]
        else:
            s1_summary = s1.summary

        merged_summary = f"{s1_summary}，然后{s2.summary}"

        return ConversationSummary(
            timestamp=max(s1.timestamp, s2.timestamp),
            summary=merged_summary[:150],  # 限制长度
            key_entities=merged_entities[:10],  # 最多10个实体
            message_count=s1.message_count + s2.message_count,
            start_message_id=s1.start_message_id,
            end_message_id=s2.end_message_id
        )