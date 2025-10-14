from typing import List, Optional, Dict
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select, func
from ..models import Deal, DealCreate, DealRead
from ..database import engine

# Etapas possíveis do pipeline
STAGES = [
    "prospeccao",
    "oportunidade",
    "identificacao",
    "viabilidade",
    "precificacao",
    "proposta",
    "contrato",
]

router = APIRouter(prefix="/deals", tags=["deals"])


# Dependência de sessão de banco
def get_session():
    with Session(engine) as session:
        yield session


# Validação simples de etapa
def ensure_valid_stage(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if value not in STAGES:
        raise HTTPException(422, f"Etapa inválida. Use uma de: {', '.join(STAGES)}")
    return value


# ------------------- CRUD ------------------- #

@router.post("/", response_model=DealRead, status_code=201)
def create_deal(data: DealCreate, session: Session = Depends(get_session)):
    ensure_valid_stage(data.stage)
    deal = Deal.model_validate(data)
    session.add(deal)
    session.commit()
    session.refresh(deal)
    return deal


@router.get("/", response_model=List[DealRead])
def list_deals(
    session: Session = Depends(get_session),
    company_id: Optional[int] = Query(None),
    stage: Optional[str] = Query(None, description=f"Etapa ({', '.join(STAGES)})"),
    q: Optional[str] = Query(None, description="Busca por título ou notas"),
    min_value: Optional[float] = Query(None, ge=0),
    max_value: Optional[float] = Query(None, ge=0),
    order_by: str = Query("id", description="Campos: id|value|expected_close_date|probability"),
    desc: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    stmt = select(Deal)

    if company_id:
        stmt = stmt.where(Deal.company_id == company_id)
    if stage:
        ensure_valid_stage(stage)
        stmt = stmt.where(Deal.stage == stage)
    if q:
        stmt = stmt.where((Deal.title.contains(q)) | (Deal.notes.contains(q)))
    if min_value is not None:
        stmt = stmt.where(Deal.value >= min_value)
    if max_value is not None:
        stmt = stmt.where(Deal.value <= max_value)

    order_map = {
        "id": Deal.id,
        "value": Deal.value,
        "expected_close_date": Deal.expected_close_date,
        "probability": Deal.probability,
    }
    order_col = order_map.get(order_by, Deal.id)
    stmt = stmt.order_by(order_col.desc() if desc else order_col.asc())

    stmt = stmt.offset(offset).limit(limit)
    return session.exec(stmt).all()


@router.get("/{deal_id}", response_model=DealRead)
def get_deal(deal_id: int, session: Session = Depends(get_session)):
    deal = session.get(Deal, deal_id)
    if not deal:
        raise HTTPException(404, "Negócio não encontrado")
    return deal


@router.put("/{deal_id}", response_model=DealRead)
def update_deal(deal_id: int, data: DealCreate, session: Session = Depends(get_session)):
    deal = session.get(Deal, deal_id)
    if not deal:
        raise HTTPException(404, "Negócio não encontrado")
    ensure_valid_stage(data.stage)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(deal, k, v)
    session.add(deal)
    session.commit()
    session.refresh(deal)
    return deal


@router.delete("/{deal_id}", status_code=204)
def delete_deal(deal_id: int, session: Session = Depends(get_session)):
    deal = session.get(Deal, deal_id)
    if not deal:
        raise HTTPException(404, "Negócio não encontrado")
    session.delete(deal)
    session.commit()
    return


# ------------------- RELATÓRIOS ------------------- #

@router.get("/summary/stage-counts")
def stage_counts(session: Session = Depends(get_session)) -> Dict[str, int]:
    """
    Quantidade de negócios por etapa.
    """
    stmt = select(Deal.stage, func.count(Deal.id)).group_by(Deal.stage)
    rows = session.exec(stmt).all()
    counts = {stage: 0 for stage in STAGES}
    for stage, total in rows:
        counts[stage] = total
    return counts


@router.get("/summary/stage-values")
def stage_values(session: Session = Depends(get_session)) -> Dict[str, float]:
    """
    Soma total de valores por etapa.
    """
    stmt = select(Deal.stage, func.coalesce(func.sum(Deal.value), 0.0)).group_by(Deal.stage)
    rows = session.exec(stmt).all()
    totals = {stage: 0.0 for stage in STAGES}
    for stage, total in rows:
        totals[stage] = float(total or 0.0)
    return totals
