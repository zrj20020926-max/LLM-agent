from fastapi import APIRouter

from app.api.v1 import chat, conversations, health, knowledge

# 把 v1 版本下面的各个接口模块统一收集起来，再交给 main.py 注册
api_router = APIRouter(prefix="/api/v1")


# 把每个模块里的路由注册到总路由里
api_router.include_router(health.router)
api_router.include_router(chat.router)
api_router.include_router(conversations.router)
api_router.include_router(knowledge.router)