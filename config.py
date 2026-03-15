import os
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
