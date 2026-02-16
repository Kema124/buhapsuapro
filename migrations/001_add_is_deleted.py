import sqlite3

DB_PATH = "data/АНО_Гума/accounting.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE contagents ADD COLUMN is_deleted INTEGER DEFAULT 0")
except Exception as e:
    print("Поле уже добавлено или ошибка:", e)

conn.commit()
conn.close()
