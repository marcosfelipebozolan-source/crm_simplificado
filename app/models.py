from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class CompanyBase(SQLModel):
    name: str
    email: Optional[str] = None
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

class ContactBase(SQLModel):
    name: str
    email: Optional[str] = None
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

class DealBase(SQLModel):
    title: str
    value: float = 0.0
    stage: str = "prospeccao"  # prospeccao|oportunidade|identificacao|viabilidade|precificacao|proposta|contrato
    probability: int = 0
    expected_close_date: Optional[str] = None
    owner: Optional[str] = None
    notes: Optional[str] = None

class Deal(DealBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id")
    company: Company = Relationship(back_populates="deals")

class DealCreate(DealBase):
    company_id: int

class DealRead(DealBase):
    id: int
    company_id: int
