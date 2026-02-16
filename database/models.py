from __future__ import annotations

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship, Mapped, mapped_column
from database.db import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    inn = Column(String(12), nullable=False)
    kpp = Column(String(9), nullable=True)
    ogrn = Column(String(15), nullable=True)
    address = Column(String, nullable=True)

    # company | ip | person
    organization_type = Column(String(20), nullable=False, default="company")

    def __repr__(self):
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
    organization: Mapped["Organization"] = relationship("Organization")

    def __repr__(self):
        return f"<Contagent {self.name}>"


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    contagent_id = Column(Integer, ForeignKey("contagents.id"))

    number = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    sum = Column(Integer, nullable=True)

    # draft | active | closed
    status = Column(String, default="draft")

    # ✅ для архива договоров
    is_deleted = Column(Boolean, default=False)

    contagent = relationship("Contagent")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"))

    number = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    sum = Column(Integer, nullable=False)

    # draft | posted | canceled
    status = Column(String, default="draft")

    contract = relationship("Contract")
