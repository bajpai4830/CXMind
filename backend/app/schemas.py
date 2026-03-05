from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class InteractionCreate(BaseModel):
    customer_id: str | None = Field(default=None, max_length=128)
    channel: str = Field(..., min_length=1, max_length=64, examples=["support_ticket", "email", "social"])
    text: str = Field(..., min_length=1, max_length=5000)


class InteractionOut(BaseModel):
    id: int
    customer_id: str | None
    channel: str
    text: str
    sentiment_compound: float
    sentiment_label: str
    topic: str | None
    created_at: dt.datetime

    model_config = {"from_attributes": True}


class AnalyticsSummary(BaseModel):
    total_interactions: int
    avg_sentiment_compound: float
    by_channel: list[dict]
    by_label: list[dict]

