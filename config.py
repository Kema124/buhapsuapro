import os

# Строка подключения к PostgreSQL.
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+psycopg2://postgres:postgres@localhost:5432/buh_pro"
)