from sqlalchemy.orm import DeclarativeBase

# 定义一个 Base，以后所有数据库模型都继承它
class Base(DeclarativeBase):
    pass
