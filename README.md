# AgentDesk 快速参考

## 前端

```text
目录: frontend
入口: frontend/src/main.js
启动: npm run dev
构建: npm run build
地址: http://localhost:5173
```

前端 API 基础地址:

```js
// frontend/src/api/request.js
const baseURL = 'http://localhost:8000/api/v1'
```

## 后端

```text
目录: backend
入口: backend/app/main.py
虚拟环境: backend/.venv
Python: 3.12
依赖文件: backend/requirements.txt
配置文件: backend/.env
启动: .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
地址: http://127.0.0.1:8000
API 前缀: /api/v1
健康检查: http://127.0.0.1:8000/api/v1/health
```

在 PowerShell 中安装依赖:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

后端配置:

```env
APP_NAME=AgentDesk
APP_ENV=development
CORS_ORIGINS=http://localhost:5173
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/agentdesk
DEEPSEEK_API_KEY=your_deepseek_api_key
```

## PostgreSQL

在 Windows 上使用 PostgreSQL。

```text
主机: localhost
端口: 5432
数据库: agentdesk
用户: postgres
密码: postgres
```

后端使用的连接串:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/agentdesk
```

当前已验证连接:

```text
数据库: agentdesk
用户: postgres
连接结果: OK
已创建表: conversations, messages
```

创建数据库:

```powershell
createdb -U postgres agentdesk
```

连接数据库:

```powershell
psql -h localhost -p 5432 -U postgres -d agentdesk
```

## VS Code

```text
默认终端: PowerShell
提示符主题: Oh My Posh
数据库扩展: SQLTools + SQLTools PostgreSQL Driver
数据库连接: local-windows-postgres
```

SQLTools 工作区连接配置已写入:

```text
.vscode/settings.json
```

连接参数:

```text
Name: local-windows-postgres
Driver: PostgreSQL
Server: localhost
Port: 5432
Database: agentdesk
Username: postgres
Password: postgres
```

在 VS Code 中连接:

```text
SQLTools -> Connections -> local-windows-postgres -> Connect
```

可选的 Oh My Posh 初始化:

```powershell
oh-my-posh init pwsh | Invoke-Expression
```
