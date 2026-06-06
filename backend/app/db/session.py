from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
# 创建一个“会话工厂”，以后要操作数据库，就调用 db = SessionLocal()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# 定义一个函数 get_db，返回一个数据库会话
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        # 不直接return，而是使用yield，还能继续执行后面的语句
        yield db
    finally:
        db.close()