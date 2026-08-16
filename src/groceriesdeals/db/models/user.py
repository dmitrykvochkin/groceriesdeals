"""User database model."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, Column, DateTime, text
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """Identity-focused user record for anonymous and registered visitors."""

    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    anonymous_key: str = Field(unique=True, index=True, max_length=128)
    email: str | None = Field(default=None, unique=True, max_length=320)
    tool_request_count: int = Field(
        default=0,
        sa_column=Column(
            BigInteger,
            nullable=False,
            server_default=text("0"),
        ),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
