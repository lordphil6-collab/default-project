"""Pydantic schemas for Phase 2 intake + reads."""
from pydantic import BaseModel, Field


class IntakeIn(BaseModel):
    customer_name: str = Field(min_length=1, max_length=200)
    channel: str = Field(pattern="^(email|whatsapp)$")
    body: str = Field(min_length=1)
    external_id: str = ""


class SituationOut(BaseModel):
    id: str
    status: str
    missing: list[str] = []
    next_action: str = ""
