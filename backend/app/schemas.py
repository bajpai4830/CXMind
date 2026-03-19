from __future__ import annotations

import datetime as dt

from pydantic import AliasChoices, BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    db_ok: bool | None = None
    db: str | None = None
    auth_enabled: bool | None = None
    time_utc: dt.datetime | None = None


class InteractionCreate(BaseModel):
    customer_id: str | None = Field(default=None, max_length=128)
    channel: str = Field(..., min_length=1, max_length=64, examples=["support_ticket", "email", "social"])
    text: str = Field(..., min_length=1, max_length=5000)

    # Optional enrichment fields (multi-channel normalization)
    interaction_type: str | None = Field(default=None, max_length=64, examples=["support_ticket", "email", "review"])
    session_id: str | None = Field(default=None, max_length=128)
    timestamp: dt.datetime | None = Field(default=None, description="Event time at source system (UTC recommended)")
    metadata: dict | None = Field(default=None)


class InteractionLogCreate(BaseModel):
    # Accept both `text` and `message` in payloads.
    customer_id: str | None = Field(default=None, max_length=128)
    channel: str = Field(..., min_length=1, max_length=64)
    text: str = Field(..., min_length=1, max_length=5000, validation_alias=AliasChoices("text", "message"))

    interaction_type: str | None = Field(default=None, max_length=64)
    session_id: str | None = Field(default=None, max_length=128)
    timestamp: dt.datetime | None = Field(default=None, validation_alias=AliasChoices("timestamp", "occurred_at"))
    metadata: dict | None = Field(default=None)
    raw_payload: dict | None = Field(default=None, description="Optional original payload for traceability")


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


class FeedbackUploadItem(BaseModel):
    customer_id: str | None = Field(default=None, max_length=128)
    channel: str = Field(default="app_review", min_length=1, max_length=64)
    text: str = Field(..., min_length=1, max_length=5000, validation_alias=AliasChoices("text", "message"))

    rating: int | None = Field(default=None, ge=1, le=5)
    title: str | None = Field(default=None, max_length=256)
    source: str | None = Field(default=None, max_length=64)

    interaction_type: str | None = Field(default="feedback", max_length=64)
    session_id: str | None = Field(default=None, max_length=128)
    timestamp: dt.datetime | None = Field(default=None, validation_alias=AliasChoices("timestamp", "occurred_at"))
    metadata: dict | None = Field(default=None)
    raw_payload: dict | None = Field(default=None)


class FeedbackUploadRequest(BaseModel):
    items: list[FeedbackUploadItem] = Field(..., min_length=1, max_length=10000)


class FeedbackUploadResponse(BaseModel):
    inserted: int


class UserRegister(BaseModel):
    email: str = Field(..., min_length=3, max_length=320, examples=["admin@company.com"])
    password: str = Field(..., min_length=8, max_length=256)


class UserLogin(BaseModel):
    email: str = Field(..., min_length=3, max_length=320)
    password: str = Field(..., min_length=8, max_length=256)


class UserOut(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool
    created_at: dt.datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

