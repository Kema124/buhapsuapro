# Генеральное ТЗ и План Рефакторинга (Проект BuhApsuaPro -> GlobalAcc)

## Цель проекта
Превратить текущее приложение (PyQt + SQLite + прямое обращение к БД) в профессиональную учетную платформу уровня 1С:Предприятие.
**Стек:** PyQt6 (Frontend) + PostgreSQL (СУБД) + SQLAlchemy 2.0 (ORM) + Alembic (Миграции). В будущем выделение FastAPI сервера.

## Ключевые архитектурные изменения:
1. **Переход на PostgreSQL:** Использование `NUMERIC(19,4)` для точного учета финансов.
2. **Бухгалтерское ядро:** Внедрение сущностей `Account` (План счетов) и `LedgerEntry` (Регистр бухгалтерии / Журнал проводок).
3. **Паттерн Unit of Work:** Документ и его проводки должны сохраняться строго в одной транзакции.
4. **Базовые классы:** Единый абстрактный класс `BaseDocument` для всей первички.

---

## ШАГ 1: Инфраструктура и Ядро (ТЕКУЩАЯ ЗАДАЧА)

Необходимо обновить зависимости, настроить подключение к PostgreSQL и создать базовые ORM-модели бухгалтерского учета.

### Целевой код для файлов Шага 1:

#### 1. `requirements.txt`
```text
PySide6>=6.5.0
SQLAlchemy>=2.0.0
alembic>=1.11.0
psycopg2-binary>=2.9.6

2. config.py (Новый файл в корне)
Python
import os

# Строка подключения к PostgreSQL.
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+psycopg2://postgres:postgres@localhost:5432/buh_pro"
)

3. database/db.py (Полностью переписать)
Python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

4. database/models.py (Полностью переписать)
Python
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from database.db import Base

class AccountType(enum.Enum):
    ACTIVE = "Активный"
    PASSIVE = "Пассивный"
    ACTIVE_PASSIVE = "Активно-Пассивный"

class Account(Base):
    """Справочник: План счетов бухгалтерского учета"""
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    account_type = Column(Enum(AccountType), nullable=False)
    
    is_folder = Column(Boolean, default=False)
    parent_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    parent = relationship("Account", remote_side=[id], backref="sub_accounts")

class LedgerEntry(Base):
    """Регистр бухгалтерии: Журнал проводок (Двойная запись)"""
    __tablename__ = "ledger_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    period = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    recorder_type = Column(String(100), nullable=False)
    recorder_id = Column(Integer, nullable=False)
    
    account_dr_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    account_cr_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    
    amount = Column(Numeric(19, 4), nullable=False)
    content = Column(String(255), nullable=True)
    
    account_dr = relationship("Account", foreign_keys=[account_dr_id])
    account_cr = relationship("Account", foreign_keys=[account_cr_id])

class BaseDocument(Base):
    """Абстрактный класс для всех первичных документов"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    doc_number = Column(String(50), nullable=False, index=True)
    doc_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    is_posted = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)

5. database/uow.py (Новый файл)
Python
from database.db import SessionLocal

class UnitOfWork:
    """Паттерн Unit of Work для управления транзакциями."""
    def __init__(self):
        self.session = SessionLocal()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        if exc_type is not None:
            self.rollback()
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

---

## ШАГ 2: Базовые Справочники, Первый Документ и Миграции

### Целевой код для файлов Шага 2:

#### 1. `database/models.py` (Добавить в конец файла)
```python
class Organization(Base):
    """Справочник: Организации (наши юр. лица)"""
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    inn = Column(String(12), unique=True, nullable=False)

class Counterparty(Base):
    """Справочник: Контрагенты (Покупатели и Поставщики)"""
    __tablename__ = "counterparties"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    inn = Column(String(12), unique=True, nullable=False)
    is_folder = Column(Boolean, default=False)
    parent_id = Column(Integer, ForeignKey("counterparties.id"), nullable=True)

class Invoice(BaseDocument):
    """Документ: Счет на оплату покупателю"""
    __tablename__ = "doc_invoices"
    
    # Поля id, doc_number, doc_date, is_posted унаследованы от BaseDocument
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    counterparty_id = Column(Integer, ForeignKey("counterparties.id"), nullable=False)
    total_amount = Column(Numeric(19, 4), default=0)
    
    organization = relationship("Organization")
    counterparty = relationship("Counterparty")
    items = relationship("InvoiceItem", backref="invoice", cascade="all, delete-orphan")

class InvoiceItem(Base):
    """Табличная часть документа 'Счет на оплату'"""
    __tablename__ = "doc_invoice_items"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("doc_invoices.id"), nullable=False)
    
    product_name = Column(String(255), nullable=False)
    quantity = Column(Numeric(19, 3), nullable=False)
    price = Column(Numeric(19, 4), nullable=False)
    amount = Column(Numeric(19, 4), nullable=False)

2. alembic/env.py (Полностью заменить содержимое)
Python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

import os
import sys
# Добавляем корень проекта в sys.path, чтобы Alembic видел наши модули
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import DATABASE_URL
from database.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Подменяем URL в alembic на тот, что указан в нашем config.py
config.set_main_option("sqlalchemy.url", DATABASE_URL)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()