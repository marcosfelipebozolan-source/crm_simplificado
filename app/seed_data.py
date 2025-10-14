# app/seed_data.py
from random import choice, randint, uniform
from datetime import date, timedelta
from sqlmodel import Session, select
from .database import engine, create_db_and_tables
from .models import Company, Contact, Deal

STAGES = [
    "prospeccao", "oportunidade", "identificacao",
    "viabilidade", "precificacao", "proposta", "contrato",
]

TARGET_COMPANIES = 3
TARGET_CONTACTS  = 4
TARGET_DEALS     = 12

def top_up_data(session: Session):
    # --- Companies ---
    existing_companies = session.exec(select(Company)).all()
    need_companies = max(0, TARGET_COMPANIES - len(existing_companies))
    base_companies = [
        Company(name="TechNova", email="contato@technova.com", phone="11988887777", website="www.technova.com.br", notes="Cliente em prospecção inicial"),
        Company(name="AgroVale", email="vendas@agrovale.com.br", phone="11977776666"),
        Company(name="Saude+ Clínicas", email="contato@saudemais.com", phone="1133334444"),
    ]
    # insira diferentes das já existentes pelo nome
    existing_names = {c.name for c in existing_companies}
    for c in base_companies:
        if need_companies <= 0:
            break
        if c.name not in existing_names:
            session.add(c)
            need_companies -= 1
    session.commit()

    companies = session.exec(select(Company)).all()

    # --- Contacts ---
    existing_contacts = session.exec(select(Contact)).all()
    need_contacts = max(0, TARGET_CONTACTS - len(existing_contacts))
    base_contacts = [
        ("Ana Silva", "ana@technova.com", "Compras"),
        ("Bruno Souza", "bruno@agrovale.com.br", "Diretor"),
        ("Carla Lima", "carla@saudemais.com", "Gerente"),
        ("Diego Alves", "diego@technova.com", "TI"),
    ]
    i = 0
    while need_contacts > 0 and companies:
        nome, email, role = base_contacts[i % len(base_contacts)]
        session.add(Contact(name=nome, email=email, role=role, company_id=choice(companies).id))
        i += 1
        need_contacts -= 1
    session.commit()

    # --- Deals ---
    existing_deals = session.exec(select(Deal)).all()
    need_deals = max(0, TARGET_DEALS - len(existing_deals))
    prob_map = {
        "prospeccao": 10, "oportunidade": 20, "identificacao": 30, "viabilidade": 40,
        "precificacao": 60, "proposta": 75, "contrato": 95
    }
    for _ in range(need_deals):
        comp = choice(companies)
        value = round(uniform(5000, 60000), 2)
        stage = choice(STAGES)
        expected = date.today() + timedelta(days=randint(7, 60))
        session.add(Deal(
            title=f"Projeto {comp.name} #{randint(100,999)}",
            company_id=comp.id,
            value=value,
            stage=stage,
            probability=prob_map[stage],
            expected_close_date=str(expected),
            owner="Marcos",
            notes="Seed automático (top-up)"
        ))
    session.commit()

def main():
    create_db_and_tables()
    with Session(engine) as session:
        top_up_data(session)
        print("Seed/top-up concluído.")

if __name__ == "__main__":
    main()
