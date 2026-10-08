"""Phase 2 domain models. Every tenant row carries org_id (Better Auth organization)."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


def _id() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    name: Mapped[str] = mapped_column(String(200))
    trial_start: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    trial_ends: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"))
    email: Mapped[str] = mapped_column(String(320))
    role: Mapped[str] = mapped_column(String(32), default="CSR")  # CSR|Sales|Ops|Manager|Owner


class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"))
    name: Mapped[str] = mapped_column(String(200))
    contact: Mapped[str] = mapped_column(String(320), default="")


class Situation(Base):
    __tablename__ = "situations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"))
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"))
    type: Mapped[str] = mapped_column(String(64), default="import_quote")
    status: Mapped[str] = mapped_column(String(64), default="New")
    shipment: Mapped[dict] = mapped_column(JSON, default=dict)
    missing: Mapped[list] = mapped_column(JSON, default=list)
    next_action: Mapped[str] = mapped_column(String(500), default="")
    outcome: Mapped[str] = mapped_column(String(64), default="")


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"))
    situation_id: Mapped[str] = mapped_column(String(36), ForeignKey("situations.id"))


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"))
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id"))
    channel: Mapped[str] = mapped_column(String(32))  # email|whatsapp
    external_id: Mapped[str] = mapped_column(String(200), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    attachments: Mapped[list] = mapped_column(JSON, default=list)


class RFQ(Base):
    __tablename__ = "rfqs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"))
    situation_id: Mapped[str] = mapped_column(String(36), ForeignKey("situations.id"))
    status: Mapped[str] = mapped_column(String(64), default="Draft")
    scope: Mapped[dict] = mapped_column(JSON, default=dict)  # Included/Excluded/Unknown


class Agent(Base):
    __tablename__ = "agents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"))
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    routes: Mapped[list] = mapped_column(JSON, default=list)  # e.g. ["China>Lagos", "Guangzhou>Lagos"]
    services: Mapped[list] = mapped_column(JSON, default=list)  # e.g. ["ocean", "air"]
    capabilities: Mapped[list] = mapped_column(JSON, default=list)  # e.g. ["20ft", "cartons"]
    contact: Mapped[str] = mapped_column(String(320), default="")
    status: Mapped[str] = mapped_column(String(32), default="Active")  # Active|Inactive
    notes: Mapped[str] = mapped_column(Text, default="")


class RFQRecipient(Base):
    __tablename__ = "rfq_recipients"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"))
    rfq_id: Mapped[str] = mapped_column(String(36), ForeignKey("rfqs.id"))
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id"))
    status: Mapped[str] = mapped_column(String(32), default="Selected")  # Selected|Sent|Responded|Declined


class AgentQuotation(Base):
    __tablename__ = "agent_quotations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"))
    rfq_id: Mapped[str] = mapped_column(String(36), ForeignKey("rfqs.id"))
    agent: Mapped[str] = mapped_column(String(200), default="")
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    freight: Mapped[float] = mapped_column(Float, default=0.0)
    origin_charges: Mapped[float | None] = mapped_column(Float, nullable=True)  # None = Unknown
    destination_charges: Mapped[float | None] = mapped_column(Float, nullable=True)  # None = Unknown, never 0
    other_charges: Mapped[float] = mapped_column(Float, default=0.0)
    validity_days: Mapped[int] = mapped_column(default=0)
    transit_days: Mapped[int] = mapped_column(default=0)
    raw_text: Mapped[str] = mapped_column(Text, default="")
    selected: Mapped[bool] = mapped_column(default=False)


class CustomerQuotation(Base):
    __tablename__ = "customer_quotations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"))
    situation_id: Mapped[str] = mapped_column(String(36), ForeignKey("situations.id"))
    agent_quotation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    markup_rule_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    agent_total: Mapped[float] = mapped_column(Float, default=0.0)
    markup_amount: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(64), default="Draft")  # Draft|Approval Required|Approved|Sent
    final_price: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    terms: Mapped[str] = mapped_column(Text, default="")
    validity_days: Mapped[int] = mapped_column(default=0)


class MarkupRule(Base):
    __tablename__ = "markup_rules"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"))
    name: Mapped[str] = mapped_column(String(200), default="Standard")
    kind: Mapped[str] = mapped_column(String(32), default="percent")  # percent|fixed|minimum|combined
    value: Mapped[float] = mapped_column(Float, default=0.0)  # % or fixed amount
    min_margin: Mapped[float] = mapped_column(Float, default=0.0)  # floor on markup_amount


class FollowUp(Base):
    __tablename__ = "follow_ups"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"))
    situation_id: Mapped[str] = mapped_column(String(36), ForeignKey("situations.id"))
    quote_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(64), default="Due")  # Due|Overdue|Responded|Negotiation|Done


class ServiceException(Base):
    __tablename__ = "exceptions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"))
    situation_id: Mapped[str] = mapped_column(String(36), ForeignKey("situations.id"))
    category: Mapped[str] = mapped_column(String(64))  # complaint|delay|missing_info|charge|mismatch|approval|conflict|requirement_change
    detail: Mapped[str] = mapped_column(Text, default="")
    owner: Mapped[str] = mapped_column(String(320), default="")
    next_action: Mapped[str] = mapped_column(String(500), default="")
    due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="Open")  # Open|Resolved


class Plan(Base):
    __tablename__ = "plans"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    name: Mapped[str] = mapped_column(String(100))
    monthly_price: Mapped[float] = mapped_column(Float, default=0.0)


class Entitlement(Base):
    __tablename__ = "entitlements"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"))
    status: Mapped[str] = mapped_column(String(32), default="trialing")  # trialing|active|past_due|cancelled
    plan_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"))
    actor: Mapped[str] = mapped_column(String(320), default="")
    action: Mapped[str] = mapped_column(String(200))
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
