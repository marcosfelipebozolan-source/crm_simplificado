from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select
from ..models import Contact, ContactCreate, ContactRead
from ..database import engine

router = APIRouter(prefix="/contacts", tags=["contacts"])

def get_session():
    with Session(engine) as session:
        yield session

@router.post("/", response_model=ContactRead, status_code=201)
def create_contact(data: ContactCreate, session: Session = Depends(get_session)):
    contact = Contact.model_validate(data)
    session.add(contact)
    session.commit()
    session.refresh(contact)
    return contact

@router.get("/", response_model=List[ContactRead])
def list_contacts(
    session: Session = Depends(get_session),
    q: Optional[str] = Query(None, description="Busca por nome ou e-mail"),
    company_id: Optional[int] = Query(None, description="Filtrar por empresa"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    stmt = select(Contact)
    if q:
        stmt = stmt.where((Contact.name.contains(q)) | (Contact.email.contains(q)))
    if company_id:
        stmt = stmt.where(Contact.company_id == company_id)
    stmt = stmt.offset(offset).limit(limit)
    return session.exec(stmt).all()

@router.get("/{contact_id}", response_model=ContactRead)
def get_contact(contact_id: int, session: Session = Depends(get_session)):
    contact = session.get(Contact, contact_id)
    if not contact:
        raise HTTPException(404, "Contact not found")
    return contact

@router.put("/{contact_id}", response_model=ContactRead)
def update_contact(contact_id: int, data: ContactCreate, session: Session = Depends(get_session)):
    contact = session.get(Contact, contact_id)
    if not contact:
        raise HTTPException(404, "Contact not found")
    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(contact, k, v)
    session.add(contact)
    session.commit()
    session.refresh(contact)
    return contact

@router.delete("/{contact_id}", status_code=204)
def delete_contact(contact_id: int, session: Session = Depends(get_session)):
    contact = session.get(Contact, contact_id)
    if not contact:
        raise HTTPException(404, "Contact not found")
    session.delete(contact)
    session.commit()
    return
