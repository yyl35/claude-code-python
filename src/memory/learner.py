#!/usr/bin/env python3
"""
记忆学习器
从工具使用中主动学习（仿照 oh-my-claudecode 的 learner.ts）
"""

import re
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import json

from .types import (
    ProjectMemory, CustomNote, HotPath, MemorySource, UserDirective,
    CACHE_EXPIRY_MS
)
from .directive_detector import DirectiveDetector


class MemoryLearner:
    """记忆学习器"""

    # 构建命令模式
    BUILD_COMMAND_PATTERNS = [
        r'npm\s+run\s+build',
        r'yarn\s+build',
        r'pnpm\s+build',
        r'python\s+setup\.py\s+build',
        r'cargo\s+build',
        r'go\s+build',
        r'make',
        r'gradle\s+build',
        r'mvn\s+package',
    ]

    # 测试命令模式
    TEST_COMMAND_PATTERNS = [
        r'npm\s+test',
        r'yarn\s+test',
        r'pnpm\s+test',
        r'python\s+-m\s+pytest',
        r'cargo\s+test',
        r'go\s+test',
        r'make\s+test',
    ]

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.directive_detector = DirectiveDetector()
        self._write_lock = asyncio.Lock()

    async def learn_from_tool_output(
        self,
        tool_name: str,
        tool_input: Dict,
        tool_output: str,
        user_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """从工具输出中学习"""
        async with self._write_lock:
            try:
                # 加载项目记忆
                memory = await self._load_project_memory()
                if not memory:
                    return {"updated": False}

                updated = False

                # 跟踪文件访问
                if tool_name in ['Read', 'Edit', 'Write']:
                    file_path = tool_input.get('file_path') or tool_input.get('filePath')
                    if file_path:
                        memory.hot_paths = self._track_access(
                            memory.hot_paths, file_path, 'file'
                        )
                        updated = True

                # 跟踪目录访问
                elif tool_name in ['Glob', 'Grep']:
                    dir_path = tool_input.get('path')
                    if dir_path:
                        memory.hot_paths = self._track_access(
                            memory.hot_paths, dir_path, 'directory'
                        )
                        updated = True

                # 从用户消息检测指令
                if user_message:
                    directives = self.directive_detector.detect_directives(user_message)
                    for directive in directives:
                        # 避免重复指令
                        if not self._directive_exists(memory.user_directives, directive):
                            memory.user_directives.append(directive)
                            updated = True

                # 从Bash命令学习
                if tool_name == 'Bash':
                    command = tool_input.get('command', '')
                    if command:
                        updated = await self._learn_from_command(
                            memory, command, tool_output, user_message
                        ) or updated

                # 保存更新
                if updated:
                    await self._save_project_memory(memory)

                return {"updated": updated, "memory": memory}

            except Exception as e:
                print(f"学习失败: {e}")
                return {"updated": False, "error": str(e)}

    async def add_custom_note(
        self,
        category: str,
        content: str,
        source: MemorySource = MemorySource.MANUAL
    ) -> bool:
        """手动添加自定义笔记"""
        async with self._write_lock:
            try:
                memory = await self._load_project_memory()
                if not memory:
                    return False

                note = CustomNote(
                    timestamp=int(datetime.now().timestamp() * 1000),
                    source=source,
                    category=category,
                    content=content
                )

                # 避免重复笔记
                if not self._note_exists(memory.custom_notes, note):
                    memory.custom_notes.append(note)

                    # 限制笔记数量
                    if len(memory.custom_notes) > 20:
                        memory.custom_notes = memory.custom_notes[-20:]

                    await self._save_project_memory(memory)
                    return True

                return False

            except Exception as e:
                print(f"添加笔记失败: {e}")
                return False

    def _track_access(
        self,
        hot_paths: List[HotPath],
        path_str: str,
        path_type: str
    ) -> List[HotPath]:
        """跟踪访问路径"""
        try:
            path = Path(path_str)
            if path.is_absolute():
                # 转换为相对路径
                try:
                    relative_path = path.relative_to(self.project_root)
                except ValueError:
                    # 路径不在项目根目录下
                    return hot_paths
            else:
                relative_path = Path(path_str)

            # 检查是否应该忽略
            if self._should_ignore_path(str(relative_path)):
                return hot_paths

            # 查找现有路径
            path_str = str(relative_path)
            existing = next(
                (hp for hp in hot_paths if hp.path == path_str),
                None
            )

            now = int(datetime.now().timestamp() * 1000)

            if existing:
                existing.access_count += 1
                existing.last_accessed = now
            else:
                hot_paths.append(HotPath(
                    path=path_str,
                    access_count=1,
                    last_accessed=now,
                    type=path_type
                ))

            # 按访问次数排序
            hot_paths.sort(key=lambda h: (-h.access_count, -h.last_accessed))

            # 限制数量
            if len(hot_paths) > 50:
                hot_paths = hot_paths[:50]

            return hot_paths

        except Exception:
            return hot_paths

    async def _learn_from_command(
        self,
        memory: ProjectMemory,
        command: str,
        output: str,
        user_message: Optional[str]
    ) -> bool:
        """从命令中学习"""
        updated = False

        # 检测构建命令
        if self._is_build_command(command):
            # 可以在这里记录构建命令模式
            pass

        # 检测测试命令
        if self._is_test_command(command):
            # 可以在这里记录测试命令模式
            pass

        # 从输出中提取环境提示
        hints = self._extract_environment_hints(output)
        for hint in hints:
            if not self._note_exists(memory.custom_notes, hint):
                memory.custom_notes.append(hint)
                updated = True

        # 限制笔记数量
        if len(memory.custom_notes) > 20:
            memory.custom_notes = memory.custom_notes[-20:]

        return updated

    def _is_build_command(self, command: str) -> bool:
        """检查是否是构建命令"""
        for pattern in self.BUILD_COMMAND_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        return False

    def _is_test_command(self, command: str) -> bool:
        """检查是否是测试命令"""
        for pattern in self.TEST_COMMAND_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        return False

    def _extract_environment_hints(self, output: str) -> List[CustomNote]:
        """从输出中提取环境提示"""
        hints = []
        timestamp = int(datetime.now().timestamp() * 1000)

        # 检测Node.js版本
        node_match = re.search(r'Node\.js\s+(v?\d+\.\d+\.\d+)', output, re.IGNORECASE)
        if node_match:
            hints.append(CustomNote(
                timestamp=timestamp,
                source=MemorySource.LEARNED,
                category='runtime',
                content=f"Node.js {node_match.group(1)}"
            ))

        # 检测Python版本
        python_match = re.search(r'Python\s+(\d+\.\d+\.\d+)', output, re.IGNORECASE)
        if python_match:
            hints.append(CustomNote(
                timestamp=timestamp,
                source=MemorySource.LEARNED,
                category='runtime',
                content=f"Python {python_match.group(1)}"
            ))

        # 检测缺失的依赖
        if 'Cannot find module' in output or 'ModuleNotFoundError' in output:
            module_match = re.search(r"Cannot find module ['\"]([^'\"]+)['\"]", output)
            if module_match:
                hints.append(CustomNote(
                    timestamp=timestamp,
                    source=MemorySource.LEARNED,
                    category='dependency',
                    content=f"缺失依赖: {module_match.group(1)}"
                ))

        # 检测环境变量需求
        env_match = re.search(
            r'(?:Missing|Required)\s+(?:environment\s+)?(?:variable|env):\s*([A-Z_][A-Z0-9_]*)',
            output,
            re.IGNORECASE
        )
        if env_match:
            hints.append(CustomNote(
                timestamp=timestamp,
                source=MemorySource.LEARNED,
                category='env',
                content=f"需要环境变量: {env_match.group(1)}"
            ))

        # 检测错误模式
        error_patterns = [
            (r'Permission denied', '权限', '需要权限'),
            (r'Connection refused', '连接', '连接被拒绝'),
            (r'File not found', '文件', '文件不存在'),
            (r'Command not found', '命令', '命令不存在'),
        ]

        for pattern, category, description in error_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                hints.append(CustomNote(
                    timestamp=timestamp,
                    source=MemorySource.LEARNED,
                    category=category,
                    content=description
                ))
                break

        return hints

    def _should_ignore_path(self, path: str) -> bool:
        """检查是否应该忽略路径"""
        ignore_patterns = [
            'node_modules',
            '.git',
            '.omc',
            'dist',
            'build',
            '.cache',
            '.next',
            '.nuxt',
            'coverage',
            '.DS_Store',
            '__pycache__',
            '.pytest_cache',
            '.venv',
            'venv',
            'env',
        ]

        for pattern in ignore_patterns:
            if pattern in path:
                return True

        return False

    def _directive_exists(self, directives: List[UserDirective], new_directive: UserDirective) -> bool:
        """检查指令是否已存在"""
        for directive in directives:
            if (directive.directive == new_directive.directive and
                directive.priority == new_directive.priority):
                return True
        return False

    def _note_exists(self, notes: List[CustomNote], new_note: CustomNote) -> bool:
        """检查笔记是否已存在"""
        for note in notes:
            if note.category == new_note.category and note.content == new_note.content:
                return True
        return False

    async def _load_project_memory(self) -> Optional[ProjectMemory]:
        """加载项目记忆"""
        memory_path = self.project_root / '.omc' / 'project_memory.json'

        try:
            if memory_path.exists():
                with open(memory_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 转换为ProjectMemory对象
                memory = ProjectMemory(
                    version=data.get('version', '1.0.0'),
                    last_scanned=data.get('last_scanned', 0),
                    project_root=data.get('project_root', str(self.project_root)),
                    user_directives=[UserDirective(**d) for d in data.get('user_directives', [])],
                    hot_paths=[HotPath(**h) for h in data.get('hot_paths', [])],
                    custom_notes=[CustomNote(**n) for n in data.get('custom_notes', [])],
                    user_preferences=data.get('user_preferences', {}),
                    entities={}  # 暂时不加载实体
                )

                # 检查是否需要重新扫描
                if self._should_rescan(memory):
                    memory.last_scanned = int(datetime.now().timestamp() * 1000)

                return memory
            else:
                # 创建新的项目记忆
                return ProjectMemory(
                    project_root=str(self.project_root),
                    last_scanned=int(datetime.now().timestamp() * 1000)
                )

        except Exception as e:
            print(f"加载项目记忆失败: {e}")
            return None

    async def _save_project_memory(self, memory: ProjectMemory) -> bool:
        """保存项目记忆"""
        memory_path = self.project_root / '.omc' / 'project_memory.json'

        try:
            # 确保目录存在
            memory_path.parent.mkdir(parents=True, exist_ok=True)

            # 转换为字典
            data = {
                'version': memory.version,
                'last_scanned': memory.last_scanned,
                'project_root': memory.project_root,
                'user_directives': [
                    {
                        'timestamp': d.timestamp,
                        'directive': d.directive,
                        'context': d.context,
                        'source': d.source.value,
                        'priority': d.priority.value,
                        'entities': d.entities
                    }
                    for d in memory.user_directives
                ],
                'hot_paths': [
                    {
                        'path': h.path,
                        'access_count': h.access_count,
                        'last_accessed': h.last_accessed,
                        'type': h.type
                    }
                    for h in memory.hot_paths
                ],
                'custom_notes': [
                    {
                        'timestamp': n.timestamp,
                        'source': n.source.value,
                        'category': n.category,
                        'content': n.content,
                        'entities': n.entities
                    }
                    for n in memory.custom_notes
                ],
                'user_preferences': memory.user_preferences
            }

            # 原子写入（先写临时文件，然后重命名）
            temp_path = memory_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # 重命名（原子操作）
            temp_path.replace(memory_path)

            return True

        except Exception as e:
            print(f"保存项目记忆失败: {e}")
            return False

    def _should_rescan(self, memory: ProjectMemory) -> bool:
        """检查是否需要重新扫描"""
        now = int(datetime.now().timestamp() * 1000)
        age = now - memory.last_scanned
        return age > CACHE_EXPIRY_MS