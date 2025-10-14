from __future__ import annotations
from typing import Optional, List
from datetime import date
from pydantic import EmailStr, field_validator
from sqlmodel import SQLModel, Field, Relationship

# Etapas permitidas para Deal
STAGES = [
    "prospeccao",
    "oportunidade",
    "identificacao",
    "viabilidade",
    "precificacao",
    "proposta",
    "contrato",
]

# -------------------- COMPANIES --------------------

class CompanyBase(SQLModel):
    name: str
    email: Optional[EmailStr] = None  # valida e-mail
    phone: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None

class Company(CompanyBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    contacts: List["Contact"] = Relationship(back_populates="company")
    deals: List["Deal"] = Relationship(back_populates="company")

class CompanyCreate(CompanyBase):
    pass

class CompanyRead(CompanyBase):
    id: int

# -------------------- CONTACTS --------------------

class ContactBase(SQLModel):
    name: str
    email: Optional[EmailStr] = None  # valida e-mail
    phone: Optional[str] = None
    role: Optional[str] = None

class Contact(ContactBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id")
    company: Company = Relationship(back_populates="contacts")

class ContactCreate(ContactBase):
    company_id: int

class ContactRead(ContactBase):
    id: int
    company_id: int

# -------------------- DEALS --------------------

class DealBase(SQLModel):
    title: str
    value: float = Field(default=0.0, ge=0)             # não negativo
    stage: str = Field(default="prospeccao")
    probability: int = Field(default=0, ge=0, le=100)   # 0..100
    expected_close_date: Optional[date] = None          # data ISO (YYYY-MM-DD)
    owner: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("stage")
    @classmethod
    def validate_stage(cls, v: str) -> str:
        if v not in STAGES:
            raise ValueError(f"etapa inválida. Use uma de: {', '.join(STAGES)}")
        return v

class Deal(DealBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id")
    company: Company = Relationship(back_populates="deals")

class DealCreate(DealBase):
    company_id: int

class DealRead(DealBase):
    id: int
    company_id: int
