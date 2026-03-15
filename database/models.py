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