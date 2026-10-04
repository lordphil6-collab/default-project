"""Phase 2 models test — sync SQLite, no live Postgres needed."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.db import Base
from backend.app import models as m


def test_org_scoped_models_and_unknown_semantics():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    S = sessionmaker(engine)
    s = S()
    org = m.Organization(name="Acme Forwarders")
    s.add(org)
    s.flush()
    c = m.Customer(org_id=org.id, name="Client A")
    s.add(c)
    s.flush()
    sit = m.Situation(org_id=org.id, customer_id=c.id, status="New", missing=["weight"])
    s.add(sit)
    s.flush()
    q = m.AgentQuotation(org_id=org.id, rfq_id="r1", agent="Agent B", destination_charges=None)
    s.add(q)
    s.commit()
    assert sit.missing == ["weight"]
    assert q.destination_charges is None  # Unknown stays NULL, never 0
    # org scoping: exactly one situation for this org
    assert s.query(m.Situation).filter_by(org_id=org.id).count() == 1
