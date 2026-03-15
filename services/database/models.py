from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    inn: Mapped[str] = mapped_column(String(12), nullable=False)
    kpp: Mapped[str | None] = mapped_column(String(9), nullable=True)
    ogrn: Mapped[str | None] = mapped_column(String(15), nullable=True)
    address: Mapped[str | None] = mapped_column(String, nullable=True)

    # company | ip | person
    organization_type: Mapped[str] = mapped_column(String(20), nullable=False, default="company")

    def __repr__(self) -> str:
        return f"<Organization {self.name}>"


class Contagent(Base):
    __tablename__ = "contagents"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    # buyer | supplier | both
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="buyer")

    # company | ip | person
    organization_type: Mapped[str] = mapped_column(String(20), nullable=False, default="company")

    inn: Mapped[str | None] = mapped_column(String, nullable=True)
    kpp: Mapped[str | None] = mapped_column(String, nullable=True)

    # Контакты и адреса (структура хранится как JSON-строка + собранная строка)
    legal_address: Mapped[str | None] = mapped_column(String, nullable=True)
    legal_address_json: Mapped[str | None] = mapped_column(String, nullable=True)
    factual_address: Mapped[str | None] = mapped_column(String, nullable=True)
    factual_address_json: Mapped[str | None] = mapped_column(String, nullable=True)

    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    geo_lat: Mapped[str | None] = mapped_column(String(50), nullable=True)
    geo_lon: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # legacy (старое поле адреса, оставлено для совместимости со старыми БД)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    organization_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=True)
    organization: Mapped[Organization | None] = relationship("Organization")

    contracts: Mapped[list[Contract]] = relationship(
        "Contract",
        back_populates="contagent",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Contagent {self.name}>"


class Bank(Base):
    __tablename__ = "banks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    # RU | ABH (условно)
    country: Mapped[str] = mapped_column(String(10), nullable=False, default="RU")

    bik: Mapped[str | None] = mapped_column(String(20), nullable=True)
    corr_account: Mapped[str | None] = mapped_column(String(34), nullable=True)
    swift: Mapped[str | None] = mapped_column(String(20), nullable=True)

    address: Mapped[str | None] = mapped_column(String, nullable=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    note: Mapped[str | None] = mapped_column(String, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<Bank {self.name}>"


class ContagentBankAccount(Base):
    __tablename__ = "contagent_bank_accounts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    contagent_id: Mapped[int] = mapped_column(Integer, ForeignKey("contagents.id"), nullable=False, index=True)
    bank_id: Mapped[int] = mapped_column(Integer, ForeignKey("banks.id"), nullable=False, index=True)

    account_number: Mapped[str] = mapped_column(String(34), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    note: Mapped[str | None] = mapped_column(String, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    contagent: Mapped["Contagent"] = relationship("Contagent")
    bank: Mapped["Bank"] = relationship("Bank")

    def __repr__(self) -> str:
        return f"<ContagentBankAccount {self.account_number}>"

class Tax(Base):
    __tablename__ = "taxes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    # tax | fee | contribution | duty
    tax_type: Mapped[str] = mapped_column(String(30), nullable=False, default="tax")

    rate: Mapped[str | None] = mapped_column(String(40), nullable=True)  # "10%" / "1000 руб" / etc.
    kbk: Mapped[str | None] = mapped_column(String(40), nullable=True)
    periodicity: Mapped[str | None] = mapped_column(String(30), nullable=True)  # month/quarter/year/once

    note: Mapped[str | None] = mapped_column(String, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<Tax {self.name}>"


class ExpenseArticle(Base):
    __tablename__ = "expense_articles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    group: Mapped[str | None] = mapped_column(String(100), nullable=True)
    note: Mapped[str | None] = mapped_column(String, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<ExpenseArticle {self.name}>"


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    contagent_id: Mapped[int] = mapped_column(Integer, ForeignKey("contagents.id"))

    number: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    sum: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # draft | active | closed
    status: Mapped[str] = mapped_column(String(20), default="draft")

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    contagent: Mapped[Contagent | None] = relationship("Contagent", back_populates="contracts")

    def __repr__(self) -> str:
        return f"<Contract {self.number}>"


class PaymentInvoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    contract_id: Mapped[int] = mapped_column(Integer, ForeignKey("contracts.id"))

    # in | out
    direction: Mapped[str] = mapped_column(String(10), nullable=False, default="out")

    number: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    sum: Mapped[int] = mapped_column(Integer, nullable=False)

    # draft | posted | canceled
    status: Mapped[str] = mapped_column(String(20), default="draft")

    # Проводимость (по ТЗ): признак проведения + дата

    # Явные счета для проводки (на первом этапе — вручную)

    contract: Mapped[Contract | None] = relationship("Contract")


    def __repr__(self) -> str:
        return f"<PaymentInvoice {self.number}>"


class Account(Base):
    """План счетов.

    Специфика Абхазии: структура может повторять привычный российский план,
    но мы оставляем её полностью настраиваемой.
    """

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, index=True, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # active | passive | active_passive | off_balance
    account_type: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    # счет может быть группой (папкой) для субсчетов
    is_folder: Mapped[bool] = mapped_column(Boolean, default=False)

    parent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=True)
    parent: Mapped[Account | None] = relationship("Account", remote_side="Account.id")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<Account {self.code} {self.name}>"


class LedgerEntry(Base):
    """Проводки (двойная запись)."""

    __tablename__ = "ledger_entries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # Дата/время операции
    period: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # ссылка на документ-регистратор
    recorder_type: Mapped[str] = mapped_column(String(50), nullable=False)
    recorder_id: Mapped[int] = mapped_column(Integer, nullable=False)

    account_dr_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=False)
    account_cr_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=False)

    account_dr: Mapped[Account] = relationship("Account", foreign_keys=[account_dr_id])
    account_cr: Mapped[Account] = relationship("Account", foreign_keys=[account_cr_id])

    amount: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)

    # аналитика (субконто): пока 3 уровня на каждую сторону
    subconto_dr_1: Mapped[int | None] = mapped_column(Integer, nullable=True)
    subconto_dr_2: Mapped[int | None] = mapped_column(Integer, nullable=True)
    subconto_dr_3: Mapped[int | None] = mapped_column(Integer, nullable=True)
    subconto_cr_1: Mapped[int | None] = mapped_column(Integer, nullable=True)
    subconto_cr_2: Mapped[int | None] = mapped_column(Integer, nullable=True)
    subconto_cr_3: Mapped[int | None] = mapped_column(Integer, nullable=True)


    def __repr__(self) -> str:
        return f"<LedgerEntry {self.period} {self.amount}>"


class BankReceipt(Base):
    """Документ: Поступление денежных средств (Банк).

    Этап 2: первый проводимый документ, формирует запись в Регистр бухгалтерии.
    """

    __tablename__ = "doc_bank_receipts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    number: Mapped[str] = mapped_column(String(30), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)

    organization_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=True)
    organization: Mapped[Organization | None] = relationship("Organization")

    contagent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("contagents.id"), nullable=True)
    contagent: Mapped[Contagent | None] = relationship("Contagent")

    contract_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("contracts.id"), nullable=True)
    contract: Mapped[Contract | None] = relationship("Contract")

    # реквизиты платежа (пока строками; позже нормализуем)
    our_account: Mapped[str | None] = mapped_column(String(34), nullable=True)
    payer_account: Mapped[str | None] = mapped_column(String(34), nullable=True)
    purpose: Mapped[str | None] = mapped_column(String, nullable=True)

    amount: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")  # draft|posted|canceled
    posted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<BankReceipt {self.number} {self.amount}>"