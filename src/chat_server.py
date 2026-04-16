#!/usr/bin/env python3
"""
DevOps Agent聊天服务器
基于FastAPI的Web服务器，提供聊天界面和API接口
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from .config import config
from .main import DevOpsAgent
from .memory.manager import MemoryManager, initialize_memory_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ChatServer:
    """聊天服务器类"""

    def __init__(self):
        self.app = FastAPI(
            title="DevOps Agent Chat Server",
            description="DevOps智能代理聊天服务器",
            version="1.0.0"
        )

        # 配置CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # 生产环境应该限制
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # 初始化组件
        self.agent = None
        self.memory_manager: Optional[MemoryManager] = None
        self.active_connections: Dict[str, WebSocket] = {}

        # 设置路由
        self.setup_routes()

    def setup_routes(self):
        """设置API路由"""

        @self.app.get("/")
        async def root():
            """根路径，返回前端页面"""
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>DevOps Agent Chat</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <!-- Marked.js for Markdown rendering -->
                <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
                <style>
                    /* Apple-style CSS */
                    :root {
                        --bg-primary: #f5f5f7;
                        --bg-secondary: #ffffff;
                        --bg-tertiary: #f2f2f7;
                        --text-primary: #1d1d1f;
                        --text-secondary: #86868b;
                        --text-tertiary: #a2a2a7;
                        --accent-blue: #007aff;
                        --accent-green: #34c759;
                        --accent-red: #ff3b30;
                        --accent-yellow: #ffcc00;
                        --border-color: #d1d1d6;
                        --shadow-light: 0 4px 20px rgba(0, 0, 0, 0.05);
                        --shadow-medium: 0 8px 30px rgba(0, 0, 0, 0.1);
                        --border-radius-small: 12px;
                        --border-radius-medium: 18px;
                        --border-radius-large: 24px;
                        --spacing-xs: 8px;
                        --spacing-sm: 12px;
                        --spacing-md: 16px;
                        --spacing-lg: 20px;
                        --spacing-xl: 24px;
                        --spacing-xxl: 32px;
                    }

                    * {
                        box-sizing: border-box;
                    }

                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                        margin: 0;
                        padding: 0;
                        background-color: var(--bg-primary);
                        color: var(--text-primary);
                        line-height: 1.5;
                        -webkit-font-smoothing: antialiased;
                        -moz-osx-font-smoothing: grayscale;
                        min-height: 100vh;
                    }

                    .container {
                        max-width: 1200px;
                        margin: 0 auto;
                        padding: var(--spacing-md);
                        height: 100vh;
                        display: flex;
                        flex-direction: column;
                    }

                    .chat-container {
                        background: var(--bg-secondary);
                        border-radius: var(--border-radius-large);
                        box-shadow: var(--shadow-medium);
                        overflow: hidden;
                        height: 100%;
                        display: flex;
                        flex-direction: column;
                        border: 1px solid var(--border-color);
                    }

                    .header {
                        background: var(--bg-secondary);
                        color: var(--text-primary);
                        padding: var(--spacing-xl) var(--spacing-xxl);
                        text-align: center;
                        border-bottom: 1px solid var(--border-color);
                    }

                    .header h1 {
                        margin: 0;
                        font-size: 28px;
                        font-weight: 700;
                        letter-spacing: -0.5px;
                    }

                    .header p {
                        margin: var(--spacing-xs) 0 0;
                        color: var(--text-secondary);
                        font-size: 15px;
                        font-weight: 400;
                    }

                    .status-bar {
                        padding: var(--spacing-sm) var(--spacing-xxl);
                        background: var(--bg-tertiary);
                        border-bottom: 1px solid var(--border-color);
                        font-size: 13px;
                        color: var(--text-secondary);
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    }

                    .connection-status {
                        display: flex;
                        align-items: center;
                        gap: var(--spacing-sm);
                    }

                    .status-dot {
                        width: 10px;
                        height: 10px;
                        border-radius: 50%;
                        background: var(--text-tertiary);
                    }

                    .status-dot.connected {
                        background: var(--accent-green);
                        animation: pulse 2s infinite;
                    }

                    @keyframes pulse {
                        0%, 100% { opacity: 1; }
                        50% { opacity: 0.5; }
                    }

                    .clear-history {
                        background: transparent;
                        border: 1px solid var(--border-color);
                        border-radius: var(--border-radius-small);
                        padding: var(--spacing-xs) var(--spacing-md);
                        font-size: 12px;
                        color: var(--text-secondary);
                        cursor: pointer;
                        transition: all 0.2s ease;
                        font-weight: 500;
                    }

                    .clear-history:hover {
                        background: var(--bg-tertiary);
                        border-color: var(--accent-blue);
                        color: var(--accent-blue);
                    }

                    .chat-area {
                        flex: 1;
                        overflow-y: auto;
                        padding: var(--spacing-xxl);
                        display: flex;
                        flex-direction: column;
                        gap: var(--spacing-lg);
                        background: var(--bg-secondary);
                    }

                    .message {
                        max-width: 85%;
                        padding: var(--spacing-md) var(--spacing-lg);
                        border-radius: var(--border-radius-medium);
                        line-height: 1.5;
                        word-wrap: break-word;
                        position: relative;
                    }

                    .user-message {
                        align-self: flex-end;
                        background: var(--accent-blue);
                        color: white;
                        border-bottom-right-radius: 4px;
                    }

                    .bot-message {
                        align-self: flex-start;
                        background: var(--bg-tertiary);
                        color: var(--text-primary);
                        border-bottom-left-radius: 4px;
                    }

                    .message-content {
                        overflow-wrap: break-word;
                        word-break: break-word;
                    }

                    .message-content p {
                        margin: 0 0 var(--spacing-xs) 0;
                    }

                    .message-content p:last-child {
                        margin-bottom: 0;
                    }

                    .message-content ul,
                    .message-content ol {
                        margin: var(--spacing-xs) 0;
                        padding-left: var(--spacing-lg);
                    }

                    .message-content li {
                        margin-bottom: var(--spacing-xs);
                    }

                    .message-content code {
                        font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
                        font-size: 13px;
                        background: rgba(0, 0, 0, 0.05);
                        padding: 2px 6px;
                        border-radius: 4px;
                    }

                    .message-content pre {
                        background: rgba(0, 0, 0, 0.05);
                        padding: var(--spacing-md);
                        border-radius: var(--border-radius-small);
                        overflow-x: auto;
                        margin: var(--spacing-sm) 0;
                    }

                    .message-content pre code {
                        background: transparent;
                        padding: 0;
                    }

                    .message-content blockquote {
                        border-left: 4px solid var(--border-color);
                        margin: var(--spacing-sm) 0;
                        padding-left: var(--spacing-md);
                        color: var(--text-secondary);
                    }

                    .message-content table {
                        border-collapse: collapse;
                        width: 100%;
                        margin: var(--spacing-sm) 0;
                    }

                    .message-content th,
                    .message-content td {
                        border: 1px solid var(--border-color);
                        padding: var(--spacing-xs) var(--spacing-sm);
                        text-align: left;
                    }

                    .message-content th {
                        background: var(--bg-tertiary);
                        font-weight: 600;
                    }

                    .message-time {
                        font-size: 11px;
                        color: var(--text-tertiary);
                        margin-top: var(--spacing-xs);
                        text-align: right;
                        font-weight: 400;
                    }

                    .typing-indicator {
                        display: none;
                        align-self: flex-start;
                        background: var(--bg-tertiary);
                        padding: var(--spacing-md) var(--spacing-lg);
                        border-radius: var(--border-radius-medium);
                        border-bottom-left-radius: 4px;
                        margin-bottom: var(--spacing-lg);
                    }

                    .typing-dots {
                        display: flex;
                        gap: 6px;
                    }

                    .typing-dot {
                        width: 8px;
                        height: 8px;
                        background: var(--text-tertiary);
                        border-radius: 50%;
                        animation: typing 1.4s infinite;
                    }

                    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
                    .typing-dot:nth-child(3) { animation-delay: 0.4s; }

                    @keyframes typing {
                        0%, 60%, 100% { transform: translateY(0); }
                        30% { transform: translateY(-6px); }
                    }

                    .input-area {
                        border-top: 1px solid var(--border-color);
                        padding: var(--spacing-xl) var(--spacing-xxl);
                        background: var(--bg-secondary);
                    }

                    .input-group {
                        display: flex;
                        gap: var(--spacing-md);
                        align-items: center;
                    }

                    #message-input {
                        flex: 1;
                        padding: var(--spacing-md) var(--spacing-lg);
                        border: 1px solid var(--border-color);
                        border-radius: var(--border-radius-medium);
                        font-size: 15px;
                        font-family: inherit;
                        background: var(--bg-secondary);
                        color: var(--text-primary);
                        outline: none;
                        transition: all 0.2s ease;
                        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
                    }

                    #message-input:focus {
                        border-color: var(--accent-blue);
                        box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
                    }

                    #message-input::placeholder {
                        color: var(--text-tertiary);
                    }

                    #send-button {
                        background: var(--accent-blue);
                        color: white;
                        border: none;
                        border-radius: var(--border-radius-medium);
                        padding: var(--spacing-md) var(--spacing-xl);
                        font-size: 15px;
                        font-weight: 600;
                        cursor: pointer;
                        transition: all 0.2s ease;
                        box-shadow: 0 2px 8px rgba(0, 122, 255, 0.3);
                        white-space: nowrap;
                    }

                    #send-button:hover {
                        background: #0056cc;
                        transform: translateY(-1px);
                        box-shadow: 0 4px 12px rgba(0, 122, 255, 0.4);
                    }

                    #send-button:active {
                        transform: translateY(0);
                        box-shadow: 0 1px 4px rgba(0, 122, 255, 0.3);
                    }

                    #send-button:disabled {
                        opacity: 0.5;
                        cursor: not-allowed;
                        transform: none;
                        box-shadow: none;
                        background: var(--accent-blue);
                    }

                    @media (max-width: 768px) {
                        .container {
                            padding: var(--spacing-xs);
                        }

                        .header,
                        .status-bar,
                        .input-area {
                            padding: var(--spacing-lg);
                        }

                        .chat-area {
                            padding: var(--spacing-lg);
                        }

                        .message {
                            max-width: 95%;
                        }

                        .header h1 {
                            font-size: 24px;
                        }

                        .header p {
                            font-size: 14px;
                        }
                    }

                    /* Dark mode support */
                    @media (prefers-color-scheme: dark) {
                        :root {
                            --bg-primary: #000000;
                            --bg-secondary: #1c1c1e;
                            --bg-tertiary: #2c2c2e;
                            --text-primary: #ffffff;
                            --text-secondary: #98989d;
                            --text-tertiary: #6c6c70;
                            --border-color: #38383a;
                            --shadow-light: 0 4px 20px rgba(0, 0, 0, 0.3);
                            --shadow-medium: 0 8px 30px rgba(0, 0, 0, 0.4);
                        }

                        .message-content code,
                        .message-content pre {
                            background: rgba(255, 255, 255, 0.1);
                        }
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="chat-container">
                        <div class="header">
                            <h1>🤖 DevOps智能代理</h1>
                            <p>通过自然语言完成代码开发和运维任务</p>
                        </div>

                        <div class="status-bar">
                            <div class="connection-status">
                                <div class="status-dot" id="status-dot"></div>
                                <span id="status-text">连接中...</span>
                            </div>
                            <button class="clear-history" onclick="clearChatHistory()">清空历史</button>
                        </div>

                        <div class="chat-area" id="chat-area">
                            <div class="message bot-message">
                                <div class="message-content">
                                    👋 你好！我是DevOps智能代理，我可以帮你：
                                    <ul>
                                        <li>执行系统命令和脚本</li>
                                        <li>读取、创建和修改文件</li>
                                        <li>获取股票和市场数据</li>
                                        <li>完成各种运维任务</li>
                                    </ul>
                                    有什么我可以帮你的吗？
                                </div>
                                <div class="message-time">系统消息</div>
                            </div>
                        </div>

                        <div class="typing-indicator" id="typing-indicator">
                            <div class="typing-dots">
                                <div class="typing-dot"></div>
                                <div class="typing-dot"></div>
                                <div class="typing-dot"></div>
                            </div>
                        </div>

                        <div class="input-area">
                            <div class="input-group">
                                <input type="text" id="message-input" placeholder="输入你的任务... (例如：读取/etc/hosts文件)" autocomplete="off">
                                <button id="send-button" onclick="sendMessage()">发送</button>
                            </div>
                        </div>
                    </div>
                </div>

                <script>
                    // Initialize marked.js with options
                    marked.setOptions({
                        breaks: true,
                        gfm: true,
                        headerIds: false,
                        mangle: false,
                        sanitize: false, // Allow HTML in Markdown (be careful)
                        smartLists: true,
                        smartypants: true,
                        xhtml: false
                    });

                    let ws = null;
                    let sessionId = null;
                    let timeoutTimer = null;
                    const RESPONSE_TIMEOUT = 900000; // 15分钟超时（900,000毫秒）

                    // 获取或创建会话ID（持久化）
                    function getOrCreateSessionId() {
                        // 尝试从localStorage获取现有的sessionId
                        let savedSessionId = localStorage.getItem('chat_session_id');
                        if (savedSessionId) {
                            console.log('使用已保存的会话ID:', savedSessionId);
                            return savedSessionId;
                        }
                        // 生成新的会话ID并保存
                        const newSessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                        localStorage.setItem('chat_session_id', newSessionId);
                        console.log('生成新的会话ID:', newSessionId);
                        return newSessionId;
                    }

                    // 连接WebSocket
                    function connectWebSocket() {
                        sessionId = getOrCreateSessionId();
                        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                        const wsUrl = `${protocol}//${window.location.host}/ws/${sessionId}`;

                        console.log('连接WebSocket:', wsUrl);
                        ws = new WebSocket(wsUrl);

                        ws.onopen = function() {
                            console.log('WebSocket连接已建立');
                            updateConnectionStatus(true);

                            // 加载历史记录
                            loadChatHistory();
                        };

                        ws.onmessage = function(event) {
                            const data = JSON.parse(event.data);
                            handleWebSocketMessage(data);
                        };

                        ws.onclose = function() {
                            console.log('WebSocket连接已关闭');
                            updateConnectionStatus(false);

                            // 清除超时计时器
                            if (timeoutTimer) {
                                clearTimeout(timeoutTimer);
                                timeoutTimer = null;
                            }

                            // 5秒后重连
                            setTimeout(connectWebSocket, 5000);
                        };

                        ws.onerror = function(error) {
                            console.error('WebSocket错误:', error);
                            updateConnectionStatus(false);

                            // 清除超时计时器
                            if (timeoutTimer) {
                                clearTimeout(timeoutTimer);
                                timeoutTimer = null;
                            }
                        };
                    }

                    // 处理WebSocket消息
                    function handleWebSocketMessage(data) {
                        console.log('收到消息:', data);

                        // 隐藏打字指示器
                        document.getElementById('typing-indicator').style.display = 'none';

                        // 清除超时计时器（当收到最终响应时）
                        if (data.type === 'chat_response' || data.type === 'error') {
                            if (timeoutTimer) {
                                clearTimeout(timeoutTimer);
                                timeoutTimer = null;
                            }
                        }

                        switch(data.type) {
                            case 'chat_response':
                                addMessage(data.message, 'bot', data.timestamp);
                                // 更新session_id（如果服务器返回了新的）
                                if (data.session_id && data.session_id !== sessionId) {
                                    console.log('更新会话ID:', data.session_id);
                                    sessionId = data.session_id;
                                    localStorage.setItem('chat_session_id', sessionId);
                                }
                                break;

                            case 'error':
                                addMessage(`❌ 错误: ${data.message}`, 'bot', data.timestamp);
                                break;

                            case 'status':
                                console.log('状态更新:', data.message);
                                // 更新session_id（如果服务器返回了新的）
                                if (data.session_id && data.session_id !== sessionId) {
                                    console.log('更新会话ID（状态）:', data.session_id);
                                    sessionId = data.session_id;
                                    localStorage.setItem('chat_session_id', sessionId);
                                }
                                break;

                            case 'history':
                                // 加载历史消息
                                loadHistoryMessages(data.messages);
                                // 更新session_id（如果服务器返回了新的）
                                if (data.session_id && data.session_id !== sessionId) {
                                    console.log('更新会话ID（历史）:', data.session_id);
                                    sessionId = data.session_id;
                                    localStorage.setItem('chat_session_id', sessionId);
                                }
                                break;
                        }
                    }

                    // 更新连接状态
                    function updateConnectionStatus(connected) {
                        const statusDot = document.getElementById('status-dot');
                        const statusText = document.getElementById('status-text');

                        if (connected) {
                            statusDot.className = 'status-dot connected';
                            statusText.textContent = '已连接';
                        } else {
                            statusDot.className = 'status-dot';
                            statusText.textContent = '连接断开';
                        }
                    }

                    // 添加消息到聊天区域（支持Markdown）
                    function addMessage(text, sender, timestamp = null, skipSave = false) {
                        const chatArea = document.getElementById('chat-area');
                        const messageDiv = document.createElement('div');

                        messageDiv.className = `message ${sender}-message`;

                        // Create message content container
                        const contentDiv = document.createElement('div');
                        contentDiv.className = 'message-content';

                        // Convert Markdown to HTML
                        try {
                            contentDiv.innerHTML = marked.parse(text);
                        } catch (e) {
                            console.error('Markdown解析失败:', e);
                            contentDiv.textContent = text;
                        }

                        messageDiv.appendChild(contentDiv);

                        // 添加时间戳
                        const timeDiv = document.createElement('div');
                        timeDiv.className = 'message-time';
                        timeDiv.textContent = timestamp || new Date().toLocaleTimeString();
                        messageDiv.appendChild(timeDiv);

                        chatArea.appendChild(messageDiv);

                        // 滚动到底部
                        chatArea.scrollTop = chatArea.scrollHeight;

                        // 保存到本地存储（除非跳过）
                        if (!skipSave) {
                            saveMessageToLocalStorage(text, sender, timestamp);
                        }
                    }

                    // 保存消息到本地存储
                    function saveMessageToLocalStorage(text, sender, timestamp) {
                        const messages = JSON.parse(localStorage.getItem('chat_messages') || '[]');
                        messages.push({
                            text: text,
                            sender: sender,
                            timestamp: timestamp || new Date().toISOString(),
                            date: new Date().toLocaleDateString()
                        });
                        localStorage.setItem('chat_messages', JSON.stringify(messages));
                    }

                    // 加载历史消息
                    function loadHistoryMessages(messages) {
                        const chatArea = document.getElementById('chat-area');

                        // 清空现有消息（除了欢迎消息）
                        const welcomeMessage = chatArea.querySelector('.bot-message');
                        chatArea.innerHTML = '';
                        if (welcomeMessage) {
                            chatArea.appendChild(welcomeMessage);
                        }

                        // 清空本地存储，准备用服务器历史替换
                        localStorage.removeItem('chat_messages');

                        // 添加历史消息（跳过保存到本地存储，稍后批量保存）
                        messages.forEach(msg => {
                            addMessage(msg.text, msg.sender, msg.timestamp, true);
                        });

                        // 将服务器历史保存到本地存储
                        if (messages.length > 0) {
                            localStorage.setItem('chat_messages', JSON.stringify(messages));
                        }
                    }

                    // 从本地存储加载聊天历史
                    function loadChatHistory() {
                        const messages = JSON.parse(localStorage.getItem('chat_messages') || '[]');
                        loadHistoryMessages(messages);
                    }

                    // 清空聊天历史
                    function clearChatHistory() {
                        if (confirm('确定要清空聊天历史吗？')) {
                            localStorage.removeItem('chat_messages');
                            loadChatHistory();

                            // 通知服务器清空历史
                            if (ws && ws.readyState === WebSocket.OPEN) {
                                ws.send(JSON.stringify({
                                    type: 'clear_history'
                                }));
                            }
                        }
                    }

                    // 发送消息
                    function sendMessage() {
                        const input = document.getElementById('message-input');
                        const button = document.getElementById('send-button');
                        const message = input.value.trim();

                        if (!message) return;

                        // 清除之前的超时计时器
                        if (timeoutTimer) {
                            clearTimeout(timeoutTimer);
                            timeoutTimer = null;
                        }

                        // 禁用输入和按钮
                        input.disabled = true;
                        button.disabled = true;

                        // 显示用户消息
                        addMessage(message, 'user');

                        // 显示打字指示器
                        const typingIndicator = document.getElementById('typing-indicator');
                        typingIndicator.style.display = 'flex';

                        // 发送WebSocket消息
                        if (ws && ws.readyState === WebSocket.OPEN) {
                            ws.send(JSON.stringify({
                                type: 'chat_message',
                                message: message,
                                session_id: sessionId
                            }));

                            // 设置响应超时计时器（15分钟）
                            timeoutTimer = setTimeout(function() {
                                addMessage('⏰ 处理超时（15分钟），服务器仍在处理中，请稍候...', 'bot');
                                typingIndicator.style.display = 'none';
                                // 不恢复输入，让用户等待
                            }, RESPONSE_TIMEOUT);
                        } else {
                            addMessage('❌ 连接已断开，请刷新页面重试', 'bot');
                            typingIndicator.style.display = 'none';
                            // 恢复输入
                            input.disabled = false;
                            button.disabled = false;
                        }

                        // 清空输入框（仅在连接正常时）
                        if (ws && ws.readyState === WebSocket.OPEN) {
                            input.value = '';
                            input.disabled = false;
                            button.disabled = false;
                            input.focus();
                        }

                        // 滚动到底部
                        const chatArea = document.getElementById('chat-area');
                        chatArea.scrollTop = chatArea.scrollHeight;
                    }

                    // 回车发送消息
                    document.getElementById('message-input').addEventListener('keypress', function(e) {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            sendMessage();
                        }
                    });

                    // 页面加载时连接WebSocket
                    window.addEventListener('load', function() {
                        connectWebSocket();
                        document.getElementById('message-input').focus();
                    });
                </script>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)

        @self.app.get("/api/health")
        async def health_check():
            """健康检查端点"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "service": "devops-agent-chat"
            }

        @self.app.get("/api/status")
        async def get_status():
            """获取服务器状态"""
            agent_status = "initialized" if self.agent else "not_initialized"
            connections = len(self.active_connections)

            memory_stats = self.memory_manager.get_stats() if self.memory_manager else {}
            return {
                "agent_status": agent_status,
                "active_connections": connections,
                "memory_stats": memory_stats,
                "timestamp": datetime.now().isoformat()
            }

        @self.app.websocket("/ws/{session_id}")
        async def websocket_endpoint(websocket: WebSocket, session_id: str):
            """WebSocket端点"""
            await websocket.accept()

            # 处理会话ID：如果session_id是"new"或空，创建新会话
            # 否则尝试使用提供的session_id，如果不存在则创建新会话
            actual_session_id = session_id

            if session_id in ["new", "", "null", "undefined"]:
                # 创建新会话
                actual_session_id = self.memory_manager.create_session()
                logger.info(f"创建新会话: {actual_session_id}")
            elif session_id not in self.memory_manager.sessions:
                # 检查是否有最近的会话可以恢复
                recent_session = self.memory_manager.find_recent_session(hours=24)
                if recent_session:
                    logger.info(f"会话 {session_id} 不存在，恢复最近会话: {recent_session}")
                    actual_session_id = recent_session
                else:
                    # 创建新会话，但使用提供的session_id作为标识
                    actual_session_id = self.memory_manager.create_session(session_id)
                    logger.info(f"使用提供的ID创建新会话: {actual_session_id}")

            self.active_connections[actual_session_id] = websocket

            try:
                # 发送连接成功消息
                await websocket.send_json({
                    "type": "status",
                    "message": "连接成功",
                    "session_id": actual_session_id,
                    "original_session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                })

                # 发送历史记录
                if self.memory_manager:
                    history = self.memory_manager.get_session_history(actual_session_id)
                    logger.info(f"WebSocket连接: original={session_id}, actual={actual_session_id}, 历史记录数量={len(history)}")
                    await websocket.send_json({
                        "type": "history",
                        "messages": history,
                        "session_id": actual_session_id,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    logger.warning(f"记忆管理器未初始化，无法发送历史记录: session={actual_session_id}")
                    await websocket.send_json({
                        "type": "history",
                        "messages": [],
                        "session_id": actual_session_id,
                        "timestamp": datetime.now().isoformat()
                    })

                # 处理消息
                while True:
                    data = await websocket.receive_json()
                    await self.handle_websocket_message(actual_session_id, data, websocket)

            except WebSocketDisconnect:
                logger.info(f"WebSocket连接断开: original={session_id}, actual={actual_session_id}")
            except Exception as e:
                logger.error(f"WebSocket错误: {e}")
            finally:
                # 清理连接
                if actual_session_id in self.active_connections:
                    del self.active_connections[actual_session_id]

    async def handle_websocket_message(self, session_id: str, data: Dict, websocket: WebSocket):
        """处理WebSocket消息"""
        message_type = data.get("type")

        if message_type == "chat_message":
            await self.handle_chat_message(session_id, data, websocket)
        elif message_type == "clear_history":
            await self.handle_clear_history(session_id, websocket)
        elif message_type == "get_preference":
            await self.handle_get_preference(session_id, data, websocket)
        elif message_type == "set_preference":
            await self.handle_set_preference(session_id, data, websocket)

    async def handle_chat_message(self, session_id: str, data: Dict, websocket: WebSocket):
        """处理聊天消息"""
        user_message = data.get("message", "").strip()
        logger.info(f"开始处理消息: session={session_id}, message={user_message[:50]}...")

        if not user_message:
            await websocket.send_json({
                "type": "error",
                "message": "消息不能为空",
                "timestamp": datetime.now().isoformat()
            })
            return

        try:
            # 保存用户消息到记忆
            await self.memory_manager.add_message(session_id, "user", user_message)


            # 发送打字指示器状态
            await websocket.send_json({
                "type": "status",
                "message": "正在处理...",
                "timestamp": datetime.now().isoformat()
            })

            # 处理任务
            if not self.agent:
                # 初始化代理
                self.agent = DevOpsAgent()
                if not await self.agent.initialize():
                    raise Exception("代理初始化失败")

            # 执行任务（10分钟超时）
            try:
                # 使用记忆管理器增强消息
                enhanced_message = await self.memory_manager.get_enhanced_message(session_id, user_message)
                logger.info(f"增强后的消息长度: {len(enhanced_message)}")
                logger.info(f"增强消息预览: {enhanced_message[:200]}...")

                # 调试：打印模型实际收到的消息
                logger.info("=" * 80)
                logger.info("【调试】模型实际收到的消息内容：")
                logger.info(enhanced_message)
                logger.info("=" * 80)

                result = await asyncio.wait_for(self.agent.process_task(enhanced_message), timeout=600.0)
            except asyncio.TimeoutError:
                logger.warning(f"任务处理超时: {user_message[:50]}...")
                result = "⏰ 处理超时（10分钟），任务执行时间过长。建议简化查询或稍后重试。"

            # 保存代理回复到记忆
            await self.memory_manager.add_message(session_id, "bot", result)

            # 发送回复
            await websocket.send_json({
                "type": "chat_response",
                "message": result,
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id
            })
            logger.info(f"消息处理完成，已发送响应: session={session_id}, 结果长度={len(result)}")

        except Exception as e:
            logger.error(f"处理消息失败: {e}")

            # 保存错误消息
            error_msg = f"❌ 处理失败: {str(e)}"
            await self.memory_manager.add_message(session_id, "bot", error_msg)

            await websocket.send_json({
                "type": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            })

    async def handle_clear_history(self, session_id: str, websocket: WebSocket):
        """处理清空历史请求"""
        try:
            self.memory_manager.clear_session_history(session_id)

            await websocket.send_json({
                "type": "status",
                "message": "历史记录已清空",
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"清空历史失败: {e}")
            await websocket.send_json({
                "type": "error",
                "message": f"清空历史失败: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })

    async def handle_get_preference(self, session_id: str, data: Dict, websocket: WebSocket):
        """处理获取用户偏好请求"""
        try:
            key = data.get("key")
            default = data.get("default")

            if not key:
                await websocket.send_json({
                    "type": "error",
                    "message": "缺少参数: key",
                    "timestamp": datetime.now().isoformat()
                })
                return

            value = self.memory_manager.get_user_preference(key, default)

            await websocket.send_json({
                "type": "preference_value",
                "key": key,
                "value": value,
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"获取用户偏好失败: {e}")
            await websocket.send_json({
                "type": "error",
                "message": f"获取用户偏好失败: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })

    async def handle_set_preference(self, session_id: str, data: Dict, websocket: WebSocket):
        """处理设置用户偏好请求"""
        try:
            key = data.get("key")
            value = data.get("value")

            if not key:
                await websocket.send_json({
                    "type": "error",
                    "message": "缺少参数: key",
                    "timestamp": datetime.now().isoformat()
                })
                return

            self.memory_manager.set_user_preference(key, value)

            await websocket.send_json({
                "type": "status",
                "message": f"用户偏好已保存: {key}",
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"设置用户偏好失败: {e}")
            await websocket.send_json({
                "type": "error",
                "message": f"设置用户偏好失败: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })

    async def initialize(self):
        """初始化服务器"""
        logger.info("初始化聊天服务器...")

        # 创建记忆管理器实例
        memory_dir = "chat_memory"  # 默认目录
        project_root = config.workspace_path

        # 创建LLM实例用于智能实体提取
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            api_key=config.openai_api_key,
            base_url=config.openai_base_url,
            model_name=config.model_name,
            temperature=0.1
        )

        self.memory_manager = MemoryManager(
            memory_dir=memory_dir,
            project_root=project_root,
            llm=llm
        )

        # 初始化记忆管理器
        await self.memory_manager.initialize()

        logger.info("聊天服务器初始化完成")
        return True

    def run(self, host: str = "0.0.0.0", port: int = 8001):
        """运行服务器（同步版本）"""
        logger.info(f"启动聊天服务器: http://{host}:{port}")
        uvicorn.run(self.app, host=host, port=port)

    async def run_async(self, host: str = "0.0.0.0", port: int = 8001):
        """异步运行服务器"""
        config = uvicorn.Config(self.app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        logger.info(f"启动聊天服务器: http://{host}:{port}")
        await server.serve()

async def main():
    """主函数"""
    server = ChatServer()

    # 初始化
    if not await server.initialize():
        logger.error("服务器初始化失败")
        return 1

    # 运行服务器
    await server.run_async()
    return 0

if __name__ == "__main__":
    asyncio.run(main())