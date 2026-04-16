#!/usr/bin/env python3
"""
基于DeepSeek模型的智能实体提取器
使用LLM进行实体识别和指代解析，替代正则表达式
"""
import json
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import asyncio

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from .types import Entity, MemorySource


class ModelEntityExtractor:
    """基于模型的实体提取器"""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self._setup_prompts()

    def _setup_prompts(self):
        """设置提示词模板"""

        # 实体提取提示词
        self.entity_extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的实体提取助手。请从用户消息中提取所有相关实体。

实体类型说明：
1. stock（股票）：股票代码如600519、AAPL、TSLA等
2. file（文件）：文件路径如main.py、src/config.yaml、/etc/hosts等
3. command（命令）：系统命令如ls -la、git status、npm install等
4. directory（目录）：目录路径如src/、/home/user/、./test等
5. user（用户）：用户相关如"我"、"你"、"用户"等

提取规则：
- 股票代码：6位数字或2-5个大写字母
- 文件：包含扩展名的路径
- 命令：可执行的指令
- 目录：文件夹路径
- 用户：人称代词或用户标识

请以JSON格式返回结果，包含entities数组，每个实体有type和name字段。"""),
            ("human", "用户消息：{message}")
        ])

        # 指代解析提示词
        self.reference_resolution_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个指代解析助手。请根据对话上下文解析用户消息中的指代词。

指代类型：
1. "这个/那个" + 实体类型：如"这个股票"、"那个文件"
2. "刚才/之前" + 提到的：如"刚才说的"、"之前提到的"
3. "上面/下面" + 提到的：如"上面说的"、"下面说的"

对话上下文：
{context}

请分析用户消息中的指代词，并解析出具体指代的实体。
如果没有指代词或无法解析，返回null。

请以JSON格式返回结果，包含：
- has_reference: 是否有指代词
- reference_type: 指代类型
- resolved_entity: 解析出的实体（type和name）
- confidence: 置信度（0-1）"""),
            ("human", "用户消息：{message}")
        ])

        # 输出解析器
        self.json_parser = JsonOutputParser()

    async def extract_entities(self, message: str) -> List[Entity]:
        """使用模型提取实体"""
        try:
            # 构建提示词链
            chain = self.entity_extraction_prompt | self.llm | self.json_parser

            # 调用模型
            result = await chain.ainvoke({"message": message})

            # 转换为Entity对象
            entities = []
            for entity_data in result.get("entities", []):
                entity_type = entity_data.get("type", "").lower()
                entity_name = entity_data.get("name", "")

                if entity_type and entity_name:
                    entity = Entity(
                        id=self._get_entity_id(entity_name, entity_type),
                        type=entity_type,
                        name=entity_name,
                        aliases=[entity_name],
                        metadata={
                            "first_seen": datetime.now().isoformat(),
                            "source": "model_extracted",
                            "confidence": entity_data.get("confidence", 0.8)
                        },
                        created_at=datetime.now(),
                        last_referenced=datetime.now(),
                        reference_count=1
                    )
                    entities.append(entity)

            return entities

        except Exception as e:
            print(f"模型实体提取失败: {e}")
            # 失败时返回空列表
            return []

    async def resolve_reference(self, message: str, context: List[Dict]) -> Optional[Entity]:
        """使用模型解析指代词"""
        try:
            # 准备上下文
            context_text = self._format_context(context)

            # 构建提示词链
            chain = self.reference_resolution_prompt | self.llm | self.json_parser

            # 调用模型
            result = await chain.ainvoke({
                "message": message,
                "context": context_text
            })

            # 检查是否有解析结果
            if result.get("has_reference") and result.get("resolved_entity"):
                entity_data = result["resolved_entity"]
                entity_type = entity_data.get("type", "").lower()
                entity_name = entity_data.get("name", "")

                if entity_type and entity_name:
                    return Entity(
                        id=self._get_entity_id(entity_name, entity_type),
                        type=entity_type,
                        name=entity_name,
                        aliases=[entity_name],
                        metadata={
                            "source": "model_resolved",
                            "confidence": result.get("confidence", 0.7),
                            "reference_type": result.get("reference_type", "unknown")
                        },
                        created_at=datetime.now(),
                        last_referenced=datetime.now(),
                        reference_count=1
                    )

            return None

        except Exception as e:
            print(f"模型指代解析失败: {e}")
            return None

    def _format_context(self, context: List[Dict]) -> str:
        """格式化对话上下文"""
        if not context:
            return "无对话上下文"

        lines = []
        for i, msg in enumerate(context[-5:]):  # 最近5条消息
            role = "用户" if msg.get("role") == "user" else "助手"
            content = msg.get("content", "")[:100]  # 截断
            lines.append(f"{role}: {content}")

        return "\n".join(lines)

    def _get_entity_id(self, name: str, entity_type: str) -> str:
        """生成实体ID"""
        import hashlib
        key = f"{entity_type}:{name}".lower()
        return hashlib.md5(key.encode()).hexdigest()[:12]

    async def extract_and_resolve(self, message: str, context: List[Dict] = None) -> Tuple[List[Entity], Optional[Entity]]:
        """同时提取实体和解析指代"""
        # 并行执行两个任务
        extract_task = self.extract_entities(message)
        resolve_task = self.resolve_reference(message, context or [])

        entities, resolved_entity = await asyncio.gather(extract_task, resolve_task)

        return entities, resolved_entity


# 测试函数
async def test_model_extractor():
    """测试模型提取器"""
    print("测试基于模型的实体提取器...")

    # 创建LLM实例（使用项目配置）
    from src.config import config
    llm = ChatOpenAI(
        api_key=config.openai_api_key,
        base_url=config.openai_base_url,
        model_name=config.model_name,
        temperature=0.1
    )

    extractor = ModelEntityExtractor(llm)

    # 测试用例
    test_cases = [
        "查一下600095.sh最新收盘价",
        "读取src/main.py文件",
        "执行命令: ls -la",
        "这个股票的财报",
        "刚才说的文件",
    ]

    for message in test_cases:
        print(f"\n测试消息: {message}")

        # 提取实体
        entities = await extractor.extract_entities(message)
        if entities:
            print(f"  提取的实体: {[f'{e.type}:{e.name}' for e in entities]}")
        else:
            print("  未提取到实体")

        # 模拟上下文
        context = [
            {"role": "user", "content": "查一下600095.sh最新收盘价"},
            {"role": "bot", "content": "600095.sh最新收盘价是9.43元"},
        ]

        # 解析指代
        resolved = await extractor.resolve_reference(message, context)
        if resolved:
            print(f"  解析的指代: {resolved.type}:{resolved.name}")
        else:
            print("  无指代或无法解析")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_model_extractor())