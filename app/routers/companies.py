from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select
from ..models import Company, CompanyCreate, CompanyRead
from ..database import engine

router = APIRouter(prefix="/companies", tags=["companies"])

def get_session():
    with Session(engine) as session:
        yield session

@router.post("/", response_model=CompanyRead, status_code=201)
def create_company(data: CompanyCreate, session: Session = Depends(get_session)):
    company = Company.model_validate(data)
    session.add(company)
    session.commit()
    session.refresh(company)
    return company

@router.get("/", response_model=List[CompanyRead])
def list_companies(
    session: Session = Depends(get_session),
    q: Optional[str] = Query(None, description="Busca por nome"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    stmt = select(Company)
    if q:
        stmt = stmt.where(Company.name.contains(q))
    stmt = stmt.offset(offset).limit(limit)
    return session.exec(stmt).all()

@router.get("/{company_id}", response_model=CompanyRead)
def get_company(company_id: int, session: Session = Depends(get_session)):
    company = session.get(Company, company_id)
    if not company:
        raise HTTPException(404, "Company not found")
    return company

@router.put("/{company_id}", response_model=CompanyRead)
def update_company(company_id: int, data: CompanyCreate, session: Session = Depends(get_session)):
    company = session.get(Company, company_id)
    if not company:
        raise HTTPException(404, "Company not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(company, k, v)
    session.add(company)
    session.commit()
    session.refresh(company)
    return company

@router.delete("/{company_id}", status_code=204)
def delete_company(company_id: int, session: Session = Depends(get_session)):
    company = session.get(Company, company_id)
    if not company:
        raise HTTPException(404, "Company not found")
    session.delete(company)
    session.commit()
    return
