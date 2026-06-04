from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.core.cors import setup_cors


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME)
    setup_cors(app)
    app.include_router(api_router)
    return app


app = create_app()

# 后端的总入口
# 启动命令 
# uvicorn app.main:app --reload --host 127.0.0.1 --port 8000