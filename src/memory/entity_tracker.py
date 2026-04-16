#!/usr/bin/env python3
"""
实体跟踪器
识别和跟踪对话中的实体（股票、文件、命令等）
"""

import re
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime
from .types import Entity, MemorySource


class EntityTracker:
    """实体跟踪器"""

    # 实体类型和对应的正则模式
    ENTITY_PATTERNS = {
        "stock": [
            r'(\d{6})\.(?:sh|sz|ss)',      # 600095.sh
            r'(?<![a-zA-Z0-9])([A-Z]{2,5})(?![a-zA-Z0-9])',  # AAPL, TSLA (大写字母，不紧邻其他字母数字)
            r'股票\s*[:：]\s*(\d{6}|[A-Z]{2,5})',
        ],
        "file": [
            r'\b([\w\-_/\\.]+\.(?:py|js|ts|java|cpp|h|go|rs|md|txt|json|yaml|yml|xml|html|css|sh|bat))\b',
            r'文件\s*[:：]\s*([\w\-_/\\.]+\.\w+)',
            r'读取\s+([\w\-_/\\.]+\.\w+)',
            r'创建\s+([\w\-_/\\.]+\.\w+)',
            r'修改\s+([\w\-_/\\.]+\.\w+)',
            r'删除\s+([\w\-_/\\.]+\.\w+)',
        ],
        "command": [
            r'`([^`]+)`',                  # 反引号内的命令
            r'执行\s+(?:命令)?[:：]\s*(.+)',
            r'运行\s+(.+)',
            r'命令\s*[:：]\s*(.+)',
            r'输入\s+命令\s*[:：]\s*(.+)',
        ],
        "directory": [
            r'目录\s*[:：]\s*([\w\-_/]+)',
            r'文件夹\s*[:：]\s*([\w\-_/]+)',
            r'进入\s+([\w\-_/]+)',
        ],
        "user": [
            r'用户\s*[:：]\s*([\w\-_]+)',
            r'我\b',
            r'你\b',
        ],
    }

    # 指代模式
    REFERENCE_PATTERNS = [
        (r'这个\s*(股票|文件|命令|目录)', "this"),      # 这个股票
        (r'那个\s*(股票|文件|命令|目录)', "that"),      # 那个文件
        (r'刚才\s*(说的|提到的|查询的)', "previous"),   # 刚才说的
        (r'之前\s*(说的|提到的|查询的)', "previous"),   # 之前提到的
        (r'上面\s*(说的|提到的)', "above"),            # 上面说的
        (r'下面\s*(说的|提到的)', "below"),            # 下面说的
    ]

    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.entity_references: Dict[str, List[Tuple[str, datetime]]] = {}  # 实体ID -> [(引用文本, 时间)]
        self.last_referenced: Dict[str, str] = {}  # 最后引用的实体ID（按类型）

    def extract_entities(self, text: str) -> List[Entity]:
        """从文本中提取实体"""
        entities = []
        extracted_positions = set()  # 记录已提取的位置，避免重复提取

        for entity_type, patterns in self.ENTITY_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    # 检查是否已经提取过这个位置
                    start, end = match.span()
                    if any(start <= pos <= end for pos in extracted_positions):
                        continue

                    entity_name = match.group(1) if match.groups() else match.group(0)

                    # 跳过太短的实体（除非是股票代码）
                    if entity_type != "stock" and len(entity_name.strip()) < 3:
                        continue

                    # 跳过明显不是实体的单词
                    if self._should_skip_entity(entity_name, entity_type):
                        continue

                    # 标准化实体名称
                    normalized_name = self._normalize_entity_name(entity_name, entity_type)

                    # 创建或更新实体
                    entity_id = self._get_entity_id(normalized_name, entity_type)

                    if entity_id in self.entities:
                        # 更新现有实体
                        entity = self.entities[entity_id]
                        entity.last_referenced = datetime.now()
                        entity.reference_count += 1

                        # 记录引用
                        if entity_id not in self.entity_references:
                            self.entity_references[entity_id] = []
                        self.entity_references[entity_id].append((text[:100], datetime.now()))

                        # 更新最后引用
                        self.last_referenced[entity_type] = entity_id
                    else:
                        # 创建新实体
                        entity = Entity(
                            id=entity_id,
                            type=entity_type,
                            name=normalized_name,
                            aliases=[entity_name],
                            metadata={
                                "first_seen": datetime.now().isoformat(),
                                "source": "extracted",
                            },
                            created_at=datetime.now(),
                            last_referenced=datetime.now(),
                            reference_count=1
                        )
                        self.entities[entity_id] = entity

                        # 记录引用
                        self.entity_references[entity_id] = [(text[:100], datetime.now())]
                        self.last_referenced[entity_type] = entity_id

                    entities.append(entity)
                    # 记录这个位置已经被提取
                    extracted_positions.update(range(start, end))

        return entities

        return entities

    def resolve_reference(self, text: str, entity_type: Optional[str] = None) -> Optional[Entity]:
        """解析指代词（这个、那个、刚才等）"""
        for pattern, ref_type in self.REFERENCE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # 获取指代的实体类型
                ref_entity_type = match.group(1) if match.groups() else entity_type
                if not ref_entity_type:
                    continue

                # 根据指代类型获取对应的实体
                if ref_type == "this" or ref_type == "that":
                    # "这个股票" -> 最后提到的股票
                    if ref_entity_type in self.last_referenced:
                        entity_id = self.last_referenced[ref_entity_type]
                        return self.entities.get(entity_id)

                elif ref_type == "previous":
                    # "刚才说的" -> 最近提到的任何实体
                    # 按时间倒序查找
                    recent_entities = sorted(
                        self.entities.values(),
                        key=lambda e: e.last_referenced,
                        reverse=True
                    )
                    for entity in recent_entities:
                        if not entity_type or entity.type == entity_type:
                            return entity

                elif ref_type == "above":
                    # "上面说的" -> 对话中较早提到的
                    # 这里简化处理，返回第一个该类型的实体
                    for entity in self.entities.values():
                        if not entity_type or entity.type == entity_type:
                            return entity

        return None

    def add_alias(self, entity_id: str, alias: str):
        """为实体添加别名"""
        if entity_id in self.entities:
            entity = self.entities[entity_id]
            if alias not in entity.aliases:
                entity.aliases.append(alias)

    def get_entity_by_name(self, name: str, entity_type: Optional[str] = None) -> Optional[Entity]:
        """通过名称获取实体（支持别名）"""
        normalized_name = self._normalize_entity_name(name, entity_type)

        for entity in self.entities.values():
            if entity_type and entity.type != entity_type:
                continue

            # 检查实体名称或别名
            if (self._normalize_entity_name(entity.name, entity.type) == normalized_name or
                any(self._normalize_entity_name(alias, entity.type) == normalized_name
                    for alias in entity.aliases)):
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

    def clear_old_entities(self, days: int = 7):
        """清理旧的实体"""
        cutoff_date = datetime.now() - datetime.timedelta(days=days)
        entities_to_remove = []

        for entity_id, entity in self.entities.items():
            if entity.last_referenced < cutoff_date and entity.reference_count < 3:
                entities_to_remove.append(entity_id)

        for entity_id in entities_to_remove:
            del self.entities[entity_id]
            if entity_id in self.entity_references:
                del self.entity_references[entity_id]

    def _get_entity_id(self, name: str, entity_type: str) -> str:
        """生成实体ID"""
        # 使用类型和名称的哈希作为ID
        import hashlib
        key = f"{entity_type}:{name}".lower()
        return hashlib.md5(key.encode()).hexdigest()[:12]

    def _normalize_entity_name(self, name: str, entity_type: Optional[str] = None) -> str:
        """标准化实体名称"""
        name = name.strip()

        if entity_type == "stock":
            # 股票代码标准化：移除.sh/.sz后缀，转为大写
            name = re.sub(r'\.(?:sh|sz|ss)$', '', name, flags=re.IGNORECASE)
            name = name.upper()

        elif entity_type == "file":
            # 文件名标准化：转为小写
            name = name.lower()

        elif entity_type == "command":
            # 命令标准化：移除多余空格
            name = ' '.join(name.split())

        return name

    def to_dict(self) -> Dict:
        """转换为字典（用于序列化）"""
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
    def from_dict(cls, data: Dict) -> 'EntityTracker':
        """从字典恢复"""
        tracker = cls()

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

    def _should_skip_entity(self, entity_name: str, entity_type: str) -> bool:
        """检查是否应该跳过这个实体"""
        # 常见非实体单词
        common_words = {
            "src", "main", "test", "build", "run", "ls", "la", "py", "yaml", "json",
            "xml", "html", "css", "sh", "bat", "npm", "git", "python", "java"
        }

        # 对于股票类型，只检查大写字母股票代码
        if entity_type == "stock":
            # 如果是大写字母，检查是否是常见缩写
            if entity_name.isupper() and len(entity_name) >= 2:
                # 常见文件扩展名等不应该被识别为股票
                file_extensions = {"PY", "YAML", "JSON", "XML", "HTML", "CSS", "SH", "BAT", "GRADLE"}
                if entity_name in file_extensions:
                    return True
                # 常见命令/工具缩写
                command_words = {"LS", "LA", "NPM", "GIT", "CD", "RM", "CP", "MV", "CAT"}
                if entity_name in command_words:
                    return True
                # 常见目录/文件名
                dir_file_words = {"SRC", "MAIN", "TEST", "BUILD", "CONFIG"}
                if entity_name in dir_file_words:
                    return True
            return False

        # 对于其他类型，检查是否是常见单词
        normalized = entity_name.lower().strip()
        if normalized in common_words:
            return True

        # 检查是否是文件扩展名
        if entity_type == "file" and '.' in entity_name:
            # 提取扩展名部分
            ext = entity_name.split('.')[-1].lower()
            if ext in common_words:
                return True

        return False