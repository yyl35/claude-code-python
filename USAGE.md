# DevOps Agent 聊天界面使用指南

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境
```bash
cp .env.example .env
# 编辑 .env 文件，设置你的API密钥
```

### 3. 启动聊天服务器
```bash
python start_chat.py
```

### 4. 访问Web界面
打开浏览器访问：http://localhost:8001

## 功能特性

### 🎨 现代化聊天界面
- 响应式设计，支持桌面和移动设备
- 实时消息传递（WebSocket）
- 美观的UI样式和动画效果
- 本地存储对话历史

### 🧠 智能记忆功能
- **对话历史**：完整记录所有对话
- **会话管理**：自动创建和管理会话
- **上下文记忆**：保留对话上下文
- **关键词提取**：自动提取对话重点

### 🔧 代理功能
- **文件操作**：读取、写入、创建文件
- **命令执行**：执行系统命令和脚本
- **数据获取**：获取股票、市场数据
- **代码开发**：创建和修改代码文件

## 使用示例

### 基本任务
```
用户：读取 /etc/hosts 文件
代理：[执行结果] 127.0.0.1 localhost ...

用户：在当前目录执行 ls -la 命令
代理：[执行结果] total 48 ...
```

### 复杂任务
```
用户：帮我创建一个Python脚本，读取CSV文件并计算平均值
代理：[执行结果] 已创建文件：calculate_average.py ...
```

### 对话记忆
```
用户：刚才我们创建了什么文件？
代理：刚才创建了 calculate_average.py 文件...
```

## API接口

### WebSocket端点
- `ws://localhost:8001/ws/{session_id}` - 实时聊天

### REST API
- `GET /` - Web界面
- `GET /api/health` - 健康检查
- `GET /api/status` - 服务器状态

## 故障排除

### 常见问题

#### 1. 无法启动服务器
```
[错误] 导入模块失败: No module named 'fastapi'
```
**解决**：
```bash
pip install -r requirements.txt
```

#### 2. 连接失败
```
[错误] 无法连接到服务器
```
**解决**：
- 检查端口8001是否被占用
- 确认防火墙设置
- 检查服务器日志

#### 3. 代理无法处理任务
```
[错误] 代理初始化失败
```
**解决**：
- 检查 `.env` 文件配置
- 确认API密钥有效
- 检查MCP服务器状态

#### 4. 中文显示乱码
```
控制台显示乱码
```
**解决**：
- 使用支持UTF-8的终端（如Windows Terminal）
- 或直接访问Web界面：http://localhost:8001

## 开发指南

### 项目结构
```
devops-agent/
├── src/
│   ├── chat_server.py      # 聊天服务器
│   ├── chat_memory.py      # 记忆管理器
│   ├── main.py            # 代理主程序
│   └── ...               # 其他模块
├── start_chat.py         # 启动脚本
├── test_chat.py          # 测试脚本
└── README_CHAT.md        # 详细文档
```

### 扩展功能

#### 添加新消息类型
1. 在 `chat_server.py` 中添加消息处理器
2. 在前端JavaScript中添加处理逻辑
3. 更新API文档

#### 自定义界面
1. 修改 `chat_server.py` 中的HTML/CSS
2. 添加新的JavaScript功能
3. 使用外部资源文件

## 高级配置

### 环境变量
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

## 性能优化

### 服务器优化
- **连接池**：维护WebSocket连接池
- **缓存**：缓存常用操作结果
- **异步处理**：所有I/O操作异步化

### 前端优化
- **虚拟滚动**：大量消息时优化性能
- **懒加载**：按需加载历史消息
- **本地缓存**：充分利用浏览器缓存

## 安全建议

### 生产环境部署
1. **启用HTTPS**：配置SSL证书
2. **身份验证**：添加登录认证
3. **访问控制**：配置防火墙规则
4. **输入验证**：所有输入都经过验证

### 数据安全
1. **会话隔离**：不同用户会话完全独立
2. **文件权限**：严格控制文件系统访问
3. **日志脱敏**：日志中不包含敏感信息

## 许可证

MIT License