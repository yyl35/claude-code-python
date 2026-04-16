#!/usr/bin/env python3
"""
指令检测器
检测和提取用户指令（仿照 oh-my-claudecode 的 directive-detector）
"""

import re
from typing import List, Dict, Optional
from datetime import datetime
from .types import UserDirective, MemorySource, Priority


class DirectiveDetector:
    """指令检测器"""

    # 指令模式（仿照 oh-my-claudecode 的 DIRECTIVE_PATTERNS）
    DIRECTIVE_PATTERNS = [
        # 显式指令
        (r'只(?:看|关注|处理|使用)\s+(.+)', "explicit"),          # 只看、只关注
        (r'总是(?:使用|检查|包含|记住)\s+(.+)', "explicit"),      # 总是使用
        (r'从不(?:使用|修改|碰|改变)\s+(.+)', "explicit"),        # 从不使用
        (r'忽略(?:所有|任何)?\s+(.+)', "explicit"),              # 忽略
        (r'专注于\s+(.+)', "explicit"),                          # 专注于
        (r'坚持\s+(.+)', "explicit"),                            # 坚持
        (r'不要(?:使用|修改|碰|改变)\s+(.+)', "explicit"),        # 不要

        # 约束指令
        (r'必须(?:使用|包含|有)\s+(.+)', "constraint"),          # 必须
        (r'要求[:：]\s*(.+)', "constraint"),                     # 要求：
        (r'约束[:：]\s*(.+)', "constraint"),                     # 约束：
        (r'规则[:：]\s*(.+)', "constraint"),                     # 规则：

        # 范围指令
        (r'范围[:：]\s*(.+)', "scope"),                          # 范围：
        (r'在范围内[:：]\s*(.+)', "scope"),                      # 在范围内：
        (r'超出范围[:：]\s*(.+)', "scope"),                      # 超出范围：

        # 优先级指令
        (r'优先(?:处理|考虑)\s+(.+)', "priority"),               # 优先处理
        (r'重要[:：]\s*(.+)', "priority"),                       # 重要：
        (r'关键[:：]\s*(.+)', "priority"),                       # 关键：

        # 条件指令
        (r'(?:当|如果)\s+(.+?)\s*(?:时|的时候)?\s*(?:总是|从不|应该)\s+(.+)', "conditional"),  # 当...时，总是...
    ]

    # 高优先级关键词
    HIGH_PRIORITY_KEYWORDS = {
        '必须', '关键', '重要', '总是', '从不', '要求', '约束', '规则'
    }

    def detect_directives(self, message: str) -> List[UserDirective]:
        """从消息中检测指令"""
        directives = []
        lines = message.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            for pattern, pattern_type in self.DIRECTIVE_PATTERNS:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    # 提取指令内容
                    if pattern_type == "conditional" and len(match.groups()) >= 2:
                        # 条件指令：当X时，总是Y
                        condition = match.group(1).strip()
                        action = match.group(2).strip()
                        directive_text = f"当 {condition} 时，{action}"
                    else:
                        # 普通指令
                        directive_text = match.group(1).strip() if match.groups() else line

                    if directive_text and len(directive_text) > 3:
                        # 确定优先级
                        priority = self._determine_priority(line)

                        # 创建指令
                        directive = UserDirective(
                            timestamp=int(datetime.now().timestamp() * 1000),
                            directive=directive_text,
                            context=line,
                            source=MemorySource.EXPLICIT,
                            priority=priority,
                            entities=[]  # 将在后续处理中填充
                        )
                        directives.append(directive)

        return directives

    def infer_directive_from_pattern(self, command_history: List[str], threshold: int = 3) -> Optional[UserDirective]:
        """从重复模式中推断指令"""
        if len(command_history) < threshold:
            return None

        # 统计命令频率
        command_counts: Dict[str, int] = {}
        for cmd in command_history:
            normalized = self._normalize_command(cmd)
            command_counts[normalized] = command_counts.get(normalized, 0) + 1

        # 找到最频繁的命令
        most_common = max(command_counts.items(), key=lambda x: x[1], default=(None, 0))
        if most_common[1] >= threshold:
            command, count = most_common
            return UserDirective(
                timestamp=int(datetime.now().timestamp() * 1000),
                directive=f"经常执行: {command}",
                context=f"观察到用户重复执行此命令 {count} 次",
                source=MemorySource.INFERRED,
                priority=Priority.NORMAL,
                entities=[]
            )

        return None

    def extract_constraints(self, message: str) -> List[str]:
        """提取约束条件"""
        constraints = []

        # 约束模式
        constraint_patterns = [
            r'不能\s+(.+)',
            r'不允许\s+(.+)',
            r'禁止\s+(.+)',
            r'限制\s+(.+)',
            r'避免\s+(.+)',
        ]

        for pattern in constraint_patterns:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                if match.groups():
                    constraint = match.group(1).strip()
                    if constraint:
                        constraints.append(constraint)

        return constraints

    def is_directive_message(self, message: str) -> bool:
        """判断消息是否包含指令"""
        for pattern, _ in self.DIRECTIVE_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        return False

    def _determine_priority(self, text: str) -> Priority:
        """确定指令优先级"""
        text_lower = text.lower()

        # 检查高优先级关键词
        for keyword in self.HIGH_PRIORITY_KEYWORDS:
            if keyword in text_lower:
                return Priority.HIGH

        # 检查中等优先级关键词
        medium_keywords = {'应该', '建议', '推荐', '最好', '优先'}
        for keyword in medium_keywords:
            if keyword in text_lower:
                return Priority.NORMAL

        return Priority.LOW

    def _normalize_command(self, command: str) -> str:
        """标准化命令"""
        # 移除参数和选项，只保留基本命令
        command = command.strip()

        # 提取第一个单词（通常是命令本身）
        parts = command.split()
        if not parts:
            return command

        # 移除常见的前缀
        base_command = parts[0]
        if base_command in ['sudo', 'doas', 'run'] and len(parts) > 1:
            base_command = parts[1]

        # 移除路径前缀
        if '/' in base_command:
            base_command = base_command.split('/')[-1]

        return base_command

    def merge_directives(self, directives: List[UserDirective]) -> List[UserDirective]:
        """合并相似的指令"""
        if not directives:
            return []

        # 按指令内容分组
        groups: Dict[str, List[UserDirective]] = {}
        for directive in directives:
            key = directive.directive.lower()
            if key not in groups:
                groups[key] = []
            groups[key].append(directive)

        # 合并每组指令
        merged = []
        for key, group in groups.items():
            if len(group) == 1:
                merged.append(group[0])
            else:
                # 合并多个相同指令
                latest = max(group, key=lambda d: d.timestamp)
                # 更新上下文以反映合并
                latest.context = f"多次提及: {latest.directive} (共{len(group)}次)"
                merged.append(latest)

        # 按优先级和时间排序
        merged.sort(key=lambda d: (
            0 if d.priority == Priority.HIGH else
            1 if d.priority == Priority.NORMAL else 2,
            -d.timestamp  # 降序，最新的在前
        ))

        return merged

    def format_directives_for_context(self, directives: List[UserDirective], limit: int = 3) -> str:
        """格式化指令用于上下文"""
        if not directives:
            return ""

        # 按优先级排序
        sorted_directives = sorted(
            directives,
            key=lambda d: (0 if d.priority == Priority.HIGH else 1, -d.timestamp)
        )[:limit]

        lines = ["[用户指令]"]
        for i, directive in enumerate(sorted_directives, 1):
            priority_marker = "⚠️" if directive.priority == Priority.HIGH else "•"
            lines.append(f"{priority_marker} {directive.directive}")

        return "\n".join(lines)