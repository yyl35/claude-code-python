#!/usr/bin/env python3
"""
智能记忆压缩器
使用LLM进行对话压缩和摘要生成（仿照oh-my-claudecode的智能压缩机制）
"""

import re
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import asyncio

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from .types import (
    ConversationSummary, Entity, SessionMemory,
    SUMMARY_INTERVAL, MAX_RAW_MESSAGES
)
from .entity_tracker import EntityTracker


class SmartMemoryCompressor:
    """智能记忆压缩器（使用LLM）"""

    def __init__(self, llm: ChatOpenAI = None):
        self.llm = llm
        self.entity_tracker = EntityTracker()
        self._setup_prompts()

    def _setup_prompts(self):
        """设置提示词模板"""

        # 主题提取提示词
        self.topic_extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个对话分析助手。请分析以下对话内容，提取主要主题和关键信息。

对话内容：
{messages}

请提取以下信息：
1. 主要讨论的主题（最多3个）
2. 用户的主要需求或问题
3. 助手的主要回应或解决方案
4. 对话中提到的关键实体（如股票、文件、命令等）

请以JSON格式返回结果，包含以下字段：
- main_topics: 主要主题列表
- user_needs: 用户需求列表
- assistant_responses: 助手回应列表
- key_entities: 关键实体列表（每个实体包含type和name）
- overall_summary: 对话整体摘要（50-100字）"""),
            ("human", "请分析以上对话内容")
        ])

        # 摘要生成提示词
        self.summary_generation_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个对话摘要生成助手。请根据对话内容和提取的信息生成简洁、信息丰富的摘要。

对话信息：
- 主题: {topics}
- 用户需求: {user_needs}
- 助手回应: {assistant_responses}
- 关键实体: {key_entities}

请生成一个50-100字的对话摘要，要求：
1. 包含对话的主要内容和目的
2. 提及关键实体和操作
3. 语言简洁明了
4. 使用中文

请以JSON格式返回结果，包含：
- summary: 对话摘要文本
- key_points: 关键点列表（最多5个）"""),
            ("human", "请生成对话摘要")
        ])

        # 上下文增强提示词
        self.context_enhancement_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个上下文理解助手。请根据对话历史和当前消息，生成包含上下文的增强消息。

对话历史摘要：
{history_summary}

最近对话：
{recent_messages}

当前用户消息：
{current_message}

请生成一个包含以下内容的增强消息：
1. 对话历史摘要（简要回顾）
2. 当前消息的上下文理解
3. 指代词解析（如果有）
4. 对助手的明确指令

请以JSON格式返回结果，包含：
- enhanced_message: 增强后的消息内容
- context_understanding: 对当前消息的上下文理解
- resolved_references: 解析出的指代实体列表
- instructions: 给助手的明确指令"""),
            ("human", "请生成增强消息")
        ])

        # 输出解析器
        self.json_parser = JsonOutputParser()

    def should_compress(self, session_memory: SessionMemory) -> bool:
        """检查是否应该压缩"""
        # 每 N 条消息压缩一次
        if len(session_memory.raw_messages) >= SUMMARY_INTERVAL:
            return True

        # 或者原始消息数量超过限制
        if len(session_memory.raw_messages) > MAX_RAW_MESSAGES * 2:
            return True

        return False

    async def compress_conversation(self, session_memory: SessionMemory) -> Optional[ConversationSummary]:
        """压缩对话，生成摘要（使用LLM）"""
        if not session_memory.raw_messages or len(session_memory.raw_messages) < 3:
            return None

        try:
            # 如果没有LLM，使用简单压缩器
            if not self.llm:
                from .compressor import MemoryCompressor
                simple_compressor = MemoryCompressor()
                return simple_compressor.compress_conversation(session_memory)

            # 准备对话内容
            messages_text = self._format_messages_for_analysis(session_memory.raw_messages)

            # 提取主题和信息
            analysis_result = await self._analyze_conversation(messages_text)

            # 生成摘要
            summary_result = await self._generate_summary(analysis_result)

            # 提取关键实体
            key_entities = self._extract_key_entities_from_analysis(analysis_result, session_memory)

            # 创建摘要对象
            summary = ConversationSummary(
                timestamp=int(datetime.now().timestamp() * 1000),
                summary=summary_result.get("summary", "进行了一段对话。"),
                key_entities=key_entities,
                message_count=len(session_memory.raw_messages),
                start_message_id=session_memory.raw_messages[0].get('message_id', 0),
                end_message_id=session_memory.raw_messages[-1].get('message_id', 0)
            )

            # 清理原始消息（保留最近的一些）
            self._cleanup_raw_messages(session_memory)

            return summary

        except Exception as e:
            print(f"智能压缩对话失败: {e}")
            # 失败时使用简单压缩器
            from .compressor import MemoryCompressor
            simple_compressor = MemoryCompressor()
            return simple_compressor.compress_conversation(session_memory)

    def _format_messages_for_analysis(self, messages: List[Dict]) -> str:
        """格式化消息供分析"""
        formatted = []
        for msg in messages:
            role = "用户" if msg.get('role') == 'user' else "助手"
            content = msg.get('content', '')
            # 截断过长的内容
            if len(content) > 500:
                content = content[:497] + "..."
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted)

    async def _analyze_conversation(self, messages_text: str) -> Dict:
        """分析对话内容"""
        try:
            chain = self.topic_extraction_prompt | self.llm | self.json_parser
            result = await chain.ainvoke({"messages": messages_text})
            return result
        except Exception as e:
            print(f"对话分析失败: {e}")
            return {
                "main_topics": [],
                "user_needs": [],
                "assistant_responses": [],
                "key_entities": [],
                "overall_summary": "对话分析失败"
            }

    async def _generate_summary(self, analysis_result: Dict) -> Dict:
        """生成对话摘要"""
        try:
            chain = self.summary_generation_prompt | self.llm | self.json_parser
            result = await chain.ainvoke({
                "topics": ", ".join(analysis_result.get("main_topics", [])),
                "user_needs": ", ".join(analysis_result.get("user_needs", [])),
                "assistant_responses": ", ".join(analysis_result.get("assistant_responses", [])),
                "key_entities": json.dumps(analysis_result.get("key_entities", []), ensure_ascii=False)
            })
            return result
        except Exception as e:
            print(f"摘要生成失败: {e}")
            return {
                "summary": "进行了一段对话。",
                "key_points": []
            }

    def _extract_key_entities_from_analysis(self, analysis_result: Dict, session_memory: SessionMemory) -> List[str]:
        """从分析结果中提取关键实体"""
        key_entities = []

        # 从分析结果中提取实体
        analysis_entities = analysis_result.get("key_entities", [])
        for entity_data in analysis_entities:
            entity_type = entity_data.get("type", "")
            entity_name = entity_data.get("name", "")
            if entity_type and entity_name:
                # 查找或创建实体ID
                entity_id = self._find_or_create_entity_id(entity_type, entity_name, session_memory)
                if entity_id:
                    key_entities.append(entity_id)

        # 如果分析结果中没有实体，使用引用次数最多的实体
        if not key_entities:
            entities_by_ref = sorted(
                session_memory.entities.values(),
                key=lambda e: e.reference_count,
                reverse=True
            )
            for entity in entities_by_ref[:3]:  # 最多3个关键实体
                if entity.reference_count >= 2:  # 至少被引用2次
                    key_entities.append(entity.id)

        return key_entities

    def _find_or_create_entity_id(self, entity_type: str, entity_name: str, session_memory: SessionMemory) -> Optional[str]:
        """查找或创建实体ID"""
        # 首先尝试查找现有实体
        for entity_id, entity in session_memory.entities.items():
            if entity.type == entity_type and entity.name == entity_name:
                return entity_id

        # 如果没有找到，创建新实体
        from datetime import datetime
        entity_id = f"{entity_type}_{hash(entity_name) % 1000000:06x}"

        entity = Entity(
            id=entity_id,
            type=entity_type,
            name=entity_name,
            aliases=[entity_name],
            metadata={
                "first_seen": datetime.now().isoformat(),
                "source": "analysis_extracted",
                "confidence": 0.7
            },
            created_at=datetime.now(),
            last_referenced=datetime.now(),
            reference_count=1
        )

        session_memory.entities[entity_id] = entity
        return entity_id

    def _cleanup_raw_messages(self, session_memory: SessionMemory):
        """清理原始消息"""
        # 保留最近的消息
        keep_count = min(MAX_RAW_MESSAGES, len(session_memory.raw_messages) // 2)
        if keep_count > 0:
            session_memory.raw_messages = session_memory.raw_messages[-keep_count:]
        else:
            session_memory.raw_messages = []

    async def enhance_message_with_context(
        self,
        message: str,
        session_memory: SessionMemory,
        project_memory: Optional[Dict] = None
    ) -> str:
        """使用上下文增强消息（使用LLM）"""
        # 如果没有LLM，使用简单增强
        if not self.llm:
            from .compressor import MemoryCompressor
            simple_compressor = MemoryCompressor()
            return simple_compressor.enhance_message_with_context(message, session_memory, project_memory)

        try:
            # 准备上下文信息
            history_summary = self._get_history_summary(session_memory)
            recent_messages = self._get_recent_messages(session_memory)

            # 生成增强消息
            chain = self.context_enhancement_prompt | self.llm | self.json_parser
            result = await chain.ainvoke({
                "history_summary": history_summary,
                "recent_messages": recent_messages,
                "current_message": message
            })

            enhanced_message = result.get("enhanced_message", "")
            if enhanced_message:
                return enhanced_message

        except Exception as e:
            print(f"智能上下文增强失败: {e}")

        # 失败时使用简单增强
        from .compressor import MemoryCompressor
        simple_compressor = MemoryCompressor()
        return simple_compressor.enhance_message_with_context(message, session_memory, project_memory)

    def _get_history_summary(self, session_memory: SessionMemory) -> str:
        """获取历史摘要"""
        if session_memory.summaries:
            latest_summary = max(session_memory.summaries, key=lambda s: s.timestamp)
            return latest_summary.summary
        return "暂无历史摘要"

    def _get_recent_messages(self, session_memory: SessionMemory, max_messages: int = 5) -> str:
        """获取最近消息"""
        if not session_memory.raw_messages:
            return "暂无最近消息"

        recent_messages = session_memory.raw_messages[-max_messages:]
        formatted = []
        for msg in recent_messages:
            role = "用户" if msg.get('role') == 'user' else "助手"
            content = msg.get('content', '')
            if len(content) > 200:
                content = content[:197] + "..."
            formatted.append(f"{role}: {content}")

        return "\n".join(formatted)

    def format_compressed_context(
        self,
        session_memory: SessionMemory,
        char_budget: int = 500
    ) -> str:
        """格式化压缩后的上下文"""
        # 使用简单压缩器的格式化方法
        from .compressor import MemoryCompressor
        simple_compressor = MemoryCompressor()
        return simple_compressor.format_compressed_context(session_memory, char_budget)

    def merge_summaries(self, summaries: List[ConversationSummary]) -> List[ConversationSummary]:
        """合并相似的摘要"""
        # 使用简单压缩器的合并方法
        from .compressor import MemoryCompressor
        simple_compressor = MemoryCompressor()
        return simple_compressor.merge_summaries(summaries)