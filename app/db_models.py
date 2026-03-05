"""SQLAlchemy ORM models for brands and audits."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Brand(Base):
    __tablename__ = "brands"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(255), nullable=False)
    primary_domain = Column(String(255), nullable=False)
    industry = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    persona = Column(Text, nullable=True)          # free text or JSON string
    revenue_range = Column(String(100), nullable=True)  # e.g. "$1-5M"
    logo_path = Column(String(500), nullable=True)
    theme_json = Column(JSON, nullable=True)       # {primary_color, bg_color, bg_image_path}
    enrichment_status_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    audits = relationship("Audit", back_populates="brand", order_by="Audit.created_at.desc()")


class Audit(Base):
    __tablename__ = "audits"

    id = Column(String(36), primary_key=True, default=_uuid)
    brand_id = Column(String(36), ForeignKey("brands.id"), nullable=True)
    audited_url = Column(String(2048), nullable=False)
    audited_domain = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    overall_score = Column(Integer, nullable=False)
    category_results_json = Column(JSON, nullable=True)   # full audit response snapshot
    insights_json = Column(JSON, nullable=True)           # external intel snapshot
    summary_json = Column(JSON, nullable=True)            # quick wins + exec summary
    report_theme_snapshot_json = Column(JSON, nullable=True)
    status = Column(String(20), default="ok")
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)

    brand = relationship("Brand", back_populates="audits")
