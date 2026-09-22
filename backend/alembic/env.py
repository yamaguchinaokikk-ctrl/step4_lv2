from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.core.config import settings
from app.db.session import Base
from app.models import *  # noqa: F401,F403  Alembicのautogenerate用に全モデルを読み込む

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# DBパスワードに `%` エンコード文字（元の `@` `&` 等）が含まれるとconfigparserの補間構文と衝突するため、
# sqlalchemy.url をini経由で設定せず、create_engineへ直接渡す。

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(settings.database_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
