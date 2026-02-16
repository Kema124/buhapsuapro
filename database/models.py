from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    # В твоём проекте ИНН для организации — 8 цифр (как в UI), но в БД пусть будет строка.
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

    address: Mapped[str | None] = mapped_column(String, nullable=True)
    note: Mapped[str | None] = mapped_column(String, nullable=True)

    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    organization_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=True)
    organization: Mapped[Organization | None] = relationship("Organization")

    def __repr__(self) -> str:
        return f"<Contagent {self.name}>"


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    contagent_id: Mapped[int] = mapped_column(Integer, ForeignKey("contagents.id"))

    number: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    sum: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # draft | active | closed
    status: Mapped[str] = mapped_column(String(20), default="draft")

    # для архива
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    contagent: Mapped[Contagent | None] = relationship("Contagent")

    def __repr__(self) -> str:
        return f"<Contract {self.number}>"


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    contract_id: Mapped[int] = mapped_column(Integer, ForeignKey("contracts.id"))

    number: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    sum: Mapped[int] = mapped_column(Integer, nullable=False)

    # draft | posted | canceled
    status: Mapped[str] = mapped_column(String(20), default="draft")

    contract: Mapped[Contract | None] = relationship("Contract")

    def __repr__(self) -> str:
        return f"<Invoice {self.number}>"
