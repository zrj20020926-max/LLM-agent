# AgentDesk 配置速查

## 前端

```text
目录: frontend
入口: frontend/src/main.js
启动: npm run dev
构建: npm run build
服务地址: http://localhost:5173
```

前端请求地址：

```js
// frontend/src/api/request.js
const baseURL = 'http://localhost:8000/api/v1'
```

## 后端

```text
目录: backend
入口: backend/app/main.py
虚拟环境: backend/.venv
依赖文件: backend/requirements.txt
配置文件: backend/.env
启动: .venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
服务地址: http://127.0.0.1:8000
API 前缀: /api/v1
健康检查: http://127.0.0.1:8000/api/v1/health
```

依赖安装：

```powershell
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

后端配置：

```env
APP_NAME=AgentDesk
APP_ENV=development
CORS_ORIGINS=http://localhost:5173
```

## PostgreSQL

```text
运行环境: Ubuntu-22.04 WSL
Host: 127.0.0.1
Port: 5432
Database: dev_db
User: dev
Password: dev
```

连接命令：

```bash
PGPASSWORD=dev psql -h 127.0.0.1 -U dev -d dev_db
```

## VS Code

```text
默认终端: zsh -> wsl.exe -d Ubuntu-22.04 -- zsh -l
数据库插件: SQLTools + SQLTools PostgreSQL Driver
数据库连接: local-dev-postgres
```
