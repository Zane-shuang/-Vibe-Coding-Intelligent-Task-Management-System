from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,          # 保持健康检查
    pool_size=10,                # 常驻连接数：同时保持10个连接不关闭（按你电脑/服务器的CPU数调，一般5-20）
    max_overflow=20,             # 高峰期额外允许20个临时连接
    pool_recycle=3600,           # 连接闲置1小时就自动关闭，避免MySQL服务器踢掉你的连接
    pool_timeout=30              # 连接超时时间：30秒拿不到连接就报错，避免卡死
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()