# DevOps Agent 聊天界面

基于Web的聊天界面，提供自然语言交互的DevOps智能代理服务。

## 特性

- **现代化Web界面**：响应式设计，支持桌面和移动设备
- **实时聊天**：WebSocket实现实时消息传递
- **对话记忆**：完整的对话历史记录和上下文管理
- **会话管理**：支持多个独立会话
- **状态监控**：实时显示连接状态和系统信息
- **本地存储**：浏览器本地存储对话历史

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制环境变量模板并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置必要的配置：

```env
# OpenAI API配置
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.deepseek.com/v1

# MCP服务器配置
MCP_SERVER_URL=http://127.0.0.1:8000/sse

# 工作空间路径
WORKSPACE_PATH=./workspace

# 记忆文件路径
MEMORY_PATH=agent_memory.json
```

### 3. 启动聊天服务器

```bash
python start_chat.py
```

### 4. 访问Web界面

打开浏览器访问：http://localhost:8001

## 界面功能

### 主界面
- **聊天区域**：显示对话历史
- **消息输入框**：输入任务描述
- **发送按钮**：发送消息
- **状态栏**：显示连接状态和清空历史按钮

### 状态指示器
- 🔴 红色：连接断开
- 🟢 绿色：已连接（有脉冲动画）

### 键盘快捷键
- **Enter**：发送消息
- **Shift + Enter**：换行

## 使用示例

### 基本任务
```
用户：读取 /etc/hosts 文件
代理：正在读取文件...
     127.0.0.1 localhost
     ...

用户：在当前目录执行 ls -la 命令
代理：执行命令结果：
     total 48
     drwxr-xr-x  6 user  staff   192 Jan  1 12:00 .
     ...
```

### 复杂任务
```
用户：帮我创建一个Python脚本，读取CSV文件并计算平均值
代理：正在创建脚本...
     已创建文件：calculate_average.py
     脚本内容：
     import pandas as pd
     ...
```

### 对话记忆
```
用户：刚才我们创建了什么文件？
代理：刚才创建了 calculate_average.py 文件，用于读取CSV并计算平均值。
     需要我帮你修改这个文件吗？
```

## API接口

### WebSocket端点
- `ws://localhost:8001/ws/{session_id}` - 实时聊天连接

### REST API
- `GET /` - Web界面
- `GET /api/health` - 健康检查
- `GET /api/status` - 服务器状态

### WebSocket消息格式

#### 发送消息
```json
{
  "type": "chat_message",
  "message": "读取文件",
  "session_id": "session_123"
}
```

#### 接收消息类型
1. **聊天响应**
```json
{
  "type": "chat_response",
  "message": "文件内容...",
  "timestamp": "2024-01-01T12:00:00",
  "session_id": "session_123"
}
```

2. **错误消息**
```json
{
  "type": "error",
  "message": "处理失败: 文件不存在",
  "timestamp": "2024-01-01T12:00:00"
}
```

3. **状态更新**
```json
{
  "type": "status",
  "message": "正在处理...",
  "timestamp": "2024-01-01T12:00:00"
}
```

4. **历史记录**
```json
{
  "type": "history",
  "messages": [
    {
      "text": "你好",
      "sender": "user",
      "timestamp": "12:00:00",
      "date": "2024-01-01"
    }
  ],
  "timestamp": "2024-01-01T12:00:00"
}
```

## 记忆系统

### 会话管理
- 每个浏览器会话自动创建唯一ID
- 独立存储对话历史
- 支持会话恢复

### 对话历史
- 本地存储：浏览器localStorage
- 服务器存储：JSON文件持久化
- 自动清理：7天未活动的会话

### 上下文提取
- 自动提取对话关键词
- 生成对话摘要
- 支持上下文搜索

## 配置选项

### 服务器配置
通过环境变量配置：

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `OPENAI_API_KEY` | `sk-dummy-key` | OpenAI API密钥 |
| `OPENAI_BASE_URL` | `https://api.deepseek.com/v1` | API基础URL |
| `MCP_SERVER_URL` | `http://127.0.0.1:8000/sse` | MCP服务器地址 |
| `WORKSPACE_PATH` | `./workspace` | 工作空间路径 |
| `MEMORY_PATH` | `agent_memory.json` | 记忆文件路径 |

### 启动参数
```bash
# 自定义端口
python start_chat.py --port 8080

# 自定义主机
python start_chat.py --host 127.0.0.1
```

## 开发指南

### 项目结构
```
devops-agent/
├── src/
│   ├── chat_server.py      # 聊天服务器
│   ├── chat_memory.py      # 记忆管理器
│   ├── main.py            # 原有代理主程序
│   └── ...                # 其他原有模块
├── start_chat.py          # 启动脚本
├── requirements.txt       # 依赖列表
├── .env.example          # 环境变量示例
└── README_CHAT.md        # 本文档
```

### 扩展功能

#### 添加新消息类型
1. 在 `chat_server.py` 中添加新的消息处理器
2. 在前端JavaScript中添加对应的处理逻辑
3. 更新API文档

#### 自定义界面样式
1. 修改 `chat_server.py` 中的HTML/CSS
2. 添加新的JavaScript功能
3. 使用外部CSS/JS文件（需要配置静态文件服务）

#### 集成其他服务
1. 在 `ChatServer` 类中添加新的服务实例
2. 创建对应的API端点
3. 在前端添加相应的UI组件

## 故障排除

### 常见问题

#### 1. 无法启动服务器
```
错误：ModuleNotFoundError: No module named 'fastapi'
```
**解决**：安装依赖
```bash
pip install -r requirements.txt
```

#### 2. WebSocket连接失败
```
错误：WebSocket连接已断开
```
**解决**：
- 检查防火墙设置
- 确认端口8001未被占用
- 检查浏览器控制台错误

#### 3. 代理无法处理任务
```
错误：代理初始化失败
```
**解决**：
- 检查 `.env` 文件配置
- 确认API密钥有效
- 检查MCP服务器是否运行

#### 4. 界面显示异常
```
问题：样式错乱或功能异常
```
**解决**：
- 清除浏览器缓存
- 检查浏览器控制台错误
- 确认网络连接正常

### 日志查看
服务器日志显示在控制台，包含：
- 连接/断开事件
- 消息处理状态
- 错误信息
- 系统状态

## 安全考虑

### 生产环境部署
1. **启用HTTPS**：配置SSL证书
2. **限制访问**：配置防火墙规则
3. **身份验证**：添加登录认证
4. **输入验证**：所有输入都经过验证
5. **速率限制**：防止滥用

### 数据安全
1. **本地存储**：敏感数据不存储在浏览器
2. **会话隔离**：不同用户会话完全隔离
3. **文件权限**：严格控制文件系统访问
4. **日志脱敏**：日志中不包含敏感信息

## 性能优化

### 服务器优化
1. **连接池**：维护WebSocket连接池
2. **缓存**：缓存常用操作结果
3. **异步处理**：所有I/O操作异步化
4. **内存管理**：定期清理无用会话

### 前端优化
1. **虚拟滚动**：大量消息时使用虚拟滚动
2. **懒加载**：按需加载历史消息
3. **本地缓存**：充分利用浏览器缓存
4. **压缩传输**：启用Gzip压缩

## 许可证

MIT License