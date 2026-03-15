import os

# 1. Новый config.py: собираем URL по частям!
config_code = """import os
from sqlalchemy.engine import URL

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Собираем URL через объект - это на 100% защищает от невидимых символов
db_url_object = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password="postgres",  # <--- Если у вас другой пароль, впишите его сюда
    host="localhost",
    port=5432,
    database="buh_pro"
)

# Превращаем в безопасную строку
DATABASE_URL = db_url_object.render_as_string(hide_password=False)
"""

# 2. Железобетонный alembic/env.py
env_code = """import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config import DATABASE_URL
from database.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    if configuration is None:
        configuration = {}
    # Принудительно передаем наш безопасный URL
    configuration["sqlalchemy.url"] = DATABASE_URL
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
"""

# Перезаписываем файлы
with open("config.py", "w", encoding="utf-8") as f:
    f.write(config_code)

with open(os.path.join("alembic", "env.py"), "w", encoding="utf-8") as f:
    f.write(env_code)

print("✅ Файлы обновлены! Теперь используется безопасный сборщик URL.")