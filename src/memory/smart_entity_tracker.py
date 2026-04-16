#!/usr/bin/env python3
"""
智能实体跟踪器
使用DeepSeek模型进行实体提取和指代解析，替代正则表达式
"""
import asyncio
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from .types import Entity, MemorySource
from .model_entity_extractor import ModelEntityExtractor


class SmartEntityTracker:
    """智能实体跟踪器（基于模型）"""

    def __init__(self, llm):
        self.extractor = ModelEntityExtractor(llm)
        self.entities: Dict[str, Entity] = {}
        self.entity_references: Dict[str, List[Tuple[str, datetime]]] = {}
        self.last_referenced: Dict[str, str] = {}  # 按类型最后引用的实体ID
        self.conversation_context: List[Dict] = []  # 对话上下文

    async def extract_entities(self, text: str, role: str = "user") -> List[Entity]:
        """提取实体（使用模型）"""
        # 更新对话上下文
        self.conversation_context.append({"role": role, "content": text})
        if len(self.conversation_context) > 10:  # 保留最近10条
            self.conversation_context = self.conversation_context[-10:]

        # 使用模型提取实体
        entities = await self.extractor.extract_entities(text)

        # 更新实体库
        for entity in entities:
            entity_id = entity.id

            if entity_id in self.entities:
                # 更新现有实体
                existing = self.entities[entity_id]
                existing.last_referenced = datetime.now()
                existing.reference_count += 1

                # 记录引用
                if entity_id not in self.entity_references:
                    self.entity_references[entity_id] = []
                self.entity_references[entity_id].append((text[:100], datetime.now()))

                # 更新最后引用
                self.last_referenced[entity.type] = entity_id
            else:
                # 添加新实体
                self.entities[entity_id] = entity
                self.entity_references[entity_id] = [(text[:100], datetime.now())]
                self.last_referenced[entity.type] = entity_id

        return entities

    async def resolve_reference(self, text: str, entity_type: Optional[str] = None) -> Optional[Entity]:
        """解析指代词（使用模型）"""
        # 使用模型解析指代
        resolved = await self.extractor.resolve_reference(text, self.conversation_context)

        if resolved:
            # 检查是否在现有实体中
            entity_id = resolved.id
            if entity_id in self.entities:
                # 更新引用计数
                entity = self.entities[entity_id]
                entity.last_referenced = datetime.now()
                entity.reference_count += 1
                self.last_referenced[entity.type] = entity_id
                return entity
            else:
                # 添加新解析的实体
                self.entities[entity_id] = resolved
                self.entity_references[entity_id] = [(text[:100], datetime.now())]
                self.last_referenced[resolved.type] = entity_id
                return resolved

        # 如果模型无法解析，尝试基于上下文的简单逻辑
        return self._simple_reference_resolution(text, entity_type)

    def _simple_reference_resolution(self, text: str, entity_type: Optional[str] = None) -> Optional[Entity]:
        """简单的指代解析（备用方案）"""
        import re

        # 检查指代模式
        reference_patterns = [
            (r'这个\s*(股票|文件|命令|目录)', "this"),
            (r'那个\s*(股票|文件|命令|目录)', "that"),
            (r'刚才\s*(说的|提到的|查询的)', "previous"),
            (r'之前\s*(说的|提到的|查询的)', "previous"),
        ]

        for pattern, ref_type in reference_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # 获取指代的实体类型
                if match.groups():
                    ref_entity_type = match.group(1)
                    type_map = {
                        "股票": "stock",
                        "文件": "file",
                        "命令": "command",
                        "目录": "directory"
                    }
                    target_type = type_map.get(ref_entity_type, entity_type)
                else:
                    target_type = entity_type

                # 查找实体
                if ref_type == "this" or ref_type == "that":
                    # "这个股票" -> 最后提到的该类型实体
                    if target_type and target_type in self.last_referenced:
                        entity_id = self.last_referenced[target_type]
                        return self.entities.get(entity_id)
                    elif self.entities:
                        # 返回最后引用的任何实体
                        return max(self.entities.values(), key=lambda e: e.last_referenced)

                elif ref_type == "previous":
                    # "刚才说的" -> 最近提到的实体
                    if self.entities:
                        return max(self.entities.values(), key=lambda e: e.last_referenced)

        return None

    def add_alias(self, entity_id: str, alias: str):
        """为实体添加别名"""
        if entity_id in self.entities:
            entity = self.entities[entity_id]
            if alias not in entity.aliases:
                entity.aliases.append(alias)

    def get_entity_by_name(self, name: str, entity_type: Optional[str] = None) -> Optional[Entity]:
        """通过名称获取实体"""
        for entity in self.entities.values():
            if entity_type and entity.type != entity_type:
                continue

            # 检查实体名称或别名
            if (entity.name == name or
                any(alias == name for alias in entity.aliases)):
                return entity

        return None

    def get_entities_by_type(self, entity_type: str) -> List[Entity]:
        """获取指定类型的所有实体"""
        return [e for e in self.entities.values() if e.type == entity_type]

    def get_recent_entities(self, limit: int = 5) -> List[Entity]:
        """获取最近引用的实体"""
        return sorted(
            self.entities.values(),
            key=lambda e: e.last_referenced,
            reverse=True
        )[:limit]

    def clear_context(self):
        """清空对话上下文（保留实体）"""
        self.conversation_context = []

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "entities": {eid: {
                "id": entity.id,
                "type": entity.type,
                "name": entity.name,
                "aliases": entity.aliases,
                "metadata": entity.metadata,
                "created_at": entity.created_at.isoformat(),
                "last_referenced": entity.last_referenced.isoformat(),
                "reference_count": entity.reference_count
            } for eid, entity in self.entities.items()},
            "last_referenced": self.last_referenced
        }

    @classmethod
    def from_dict(cls, data: Dict, llm) -> 'SmartEntityTracker':
        """从字典恢复"""
        tracker = cls(llm)

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
                tracker.entities[eid] = entity

        if "last_referenced" in data:
            tracker.last_referenced = data["last_referenced"]

        return tracker