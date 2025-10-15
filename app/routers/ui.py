from typing import Optional, Tuple, List
from fastapi import APIRouter, Depends, Query, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select, func
from pathlib import Path

from ..database import engine
from ..models import Company

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = PROJECT_ROOT / "templates"

router = APIRouter(prefix="/ui", tags=["ui"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

def get_session():
    with Session(engine) as s:
        yield s

def _fetch_companies(
    session: Session,
    q: Optional[str],
    order_by: str,
    desc: bool,
    page: int,
    size: int,
) -> Tuple[List[Company], int]:
    base = select(Company)
    if q:
        base = base.where(Company.name.contains(q))

    # total seguro
    total_stmt = select(func.count()).select_from(base.subquery())
    total = session.exec(total_stmt).one()

    # ordenação
    order_map = {"id": Company.id, "name": Company.name}
    order_col = order_map.get(order_by, Company.id)

    # paginação
    offset = (page - 1) * size
    items = session.exec(
        base.order_by(order_col.desc() if desc else order_col.asc()).offset(offset).limit(size)
    ).all()
    return items, total

@router.get("/", response_class=HTMLResponse)
def home():
    return RedirectResponse(url="/ui/companies")

@router.get("/companies", response_class=HTMLResponse)
def ui_companies(
    request: Request,
    session: Session = Depends(get_session),
    q: Optional[str] = Query(None),
    order_by: str = Query("id"),
    desc: bool = Query(False),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
):
    items, total = _fetch_companies(session, q, order_by, desc, page, size)
    ctx = {
        "request": request,
        "companies": items,
        "q": q or "",
        "order_by": order_by,
        "desc": desc,
        "page": page,
        "size": size,
        "total": total,
        "has_prev": page > 1,
        "has_next": page * size < total,
    }
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse("companies/_list.html", ctx)
    return templates.TemplateResponse("companies/index.html", ctx)

@router.post("/companies", response_class=HTMLResponse)
def ui_create_company(
    request: Request,
    session: Session = Depends(get_session),
    name: str = Form(...),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    website: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
):
    c = Company(name=name, email=email, phone=phone, website=website, notes=notes)
    session.add(c)
    session.commit()
    session.refresh(c)
    # volta para primeira página
    items, total = _fetch_companies(session, None, "id", False, 1, 10)
    ctx = {
        "request": request,
        "companies": items,
        "q": "",
        "order_by": "id",
        "desc": False,
        "page": 1,
        "size": 10,
        "total": total,
        "has_prev": False,
        "has_next": 10 < total,
    }
    return templates.TemplateResponse("companies/_list.html", ctx)

@router.delete("/companies/{company_id}", response_class=HTMLResponse)
def ui_delete_company(
    company_id: int,
    request: Request,
    session: Session = Depends(get_session),
    q: Optional[str] = Query(None),
    order_by: str = Query("id"),
    desc: bool = Query(False),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
):
    obj = session.get(Company, company_id)
    if obj:
        session.delete(obj)
        session.commit()

    items, total = _fetch_companies(session, q, order_by, desc, page, size)
    if not items and page > 1:
        page -= 1
        items, total = _fetch_companies(session, q, order_by, desc, page, size)

    ctx = {
        "request": request,
        "companies": items,
        "q": q or "",
        "order_by": order_by,
        "desc": desc,
        "page": page,
        "size": size,
        "total": total,
        "has_prev": page > 1,
        "has_next": page * size < total,
    }
    return templates.TemplateResponse("companies/_list.html", ctx)
