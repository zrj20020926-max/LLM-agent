from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.core.cors import setup_cors
from app.db.base import Base
from app.db.session import engine
from app import models  # 触发 app/models/__init__.py 执行，进而导入 Conversation 和 Message


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME)
    setup_cors(app)
    app.include_router(api_router)

    # 注册一个启动事件，让 SQLAlchemy 根据你定义的模型类创建数据库表
    @app.on_event("startup")
    def create_database_tables() -> None:
        # Base.metadata保存了所有继承 Base 的模型表信息
        # create_all根据 metadata 里登记的表结构，在数据库中创建表
        Base.metadata.create_all(bind=engine)

    return app


app = create_app()

# 后端的总入口
# 启动命令 
# uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
# 前一个app是项目app，后面的是main.py中创建的app实例
