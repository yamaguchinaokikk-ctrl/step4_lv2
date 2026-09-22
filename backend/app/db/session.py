from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# CON-007: DB接続をある程度維持する方針（設計仕様書7.2節）としてコネクションプーリングを利用する
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=1800,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        # close()のみでも未コミットのトランザクションは暗黙にロールバックされるが、
        # 挙動を暗黙の副作用に依存させず明示化する（Phase5コードレビュー指摘）。
        db.rollback()
        raise
    finally:
        db.close()
