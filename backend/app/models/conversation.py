from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


# SQLAlchemy ORM 模型类，映射到数据库表 `conversations`。
# 类本身是 Python 类，ORM 查询数据库时返回的是该类的实例对象。
class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), default="新会话", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    messages = relationship(
        "Message", # 关联到 Message 模型
        back_populates="conversation", # 和 Message 里面的 conversation 关系互相对应
        cascade="all, delete-orphan", # 删除 Conversation 时，它下面的 Message 也会被删除; 如果某条消息不再属于任何会话，也会被删除
        passive_deletes=True, # 如果数据库外键设置了级联删除，SQLAlchemy 不需要先把所有消息查出来再一条条删
    )
