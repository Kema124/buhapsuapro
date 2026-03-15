import os

# Чистый код без единого скрытого символа
config_code = """import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/buh_pro"
"""

env_code = """import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(BASE_DIR))

from config import DATABASE_URL
from database.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", DATABASE_URL)
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
"""

# Принудительно перезаписываем файлы в правильной кодировке
with open("config.py", "w", encoding="utf-8") as f:
    f.write(config_code)

env_path = os.path.join("alembic", "env.py")
with open(env_path, "w", encoding="utf-8") as f:
    f.write(env_code)

print("✅ Файлы config.py и alembic/env.py успешно пересозданы чистым текстом!")