"""
SQLAlchemy ORM models for the Laghu Parashari database.

Tables:
  natal_charts    — saved birth charts with full planetary data
  lesson_progress — per-session lesson completion and quiz scores
"""

from __future__ import annotations
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    Date, DateTime, JSON, Text, ForeignKey,
)
from sqlalchemy.orm import relationship
from database import Base


class NatalChart(Base):
    """
    A saved natal (birth) chart.

    Stores the raw birth data plus the fully computed chart snapshot so it
    can be retrieved without re-running the ephemeris calculation.
    """
    __tablename__ = "natal_charts"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(120), nullable=False)           # native's name
    birth_date    = Column(Date,   nullable=False)
    birth_hour    = Column(Integer, default=0)
    birth_minute  = Column(Integer, default=0)
    birth_place   = Column(String(200), default="")
    latitude      = Column(Float, nullable=False)
    longitude     = Column(Float, nullable=False)
    tz_offset     = Column(Float, nullable=False)                  # hours from UTC

    # Computed chart snapshot (JSON)
    lagna_sign      = Column(String(20), nullable=True)
    lagna_degrees   = Column(Float, nullable=True)
    moon_degrees    = Column(Float, nullable=True)
    ayanamsa        = Column(Float, nullable=True)
    planet_data     = Column(JSON, nullable=True)                  # full planets dict
    house_occupants = Column(JSON, nullable=True)                  # {1: [planet,...], ...}

    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    lesson_progress = relationship(
        "LessonProgress", back_populates="chart", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "id":             self.id,
            "name":           self.name,
            "birth_date":     self.birth_date.isoformat() if self.birth_date else None,
            "birth_hour":     self.birth_hour,
            "birth_minute":   self.birth_minute,
            "birth_place":    self.birth_place,
            "latitude":       self.latitude,
            "longitude":      self.longitude,
            "tz_offset":      self.tz_offset,
            "lagna_sign":     self.lagna_sign,
            "lagna_degrees":  self.lagna_degrees,
            "moon_degrees":   self.moon_degrees,
            "ayanamsa":       self.ayanamsa,
            "planet_data":    self.planet_data,
            "house_occupants":self.house_occupants,
            "created_at":     self.created_at.isoformat() if self.created_at else None,
        }


class LessonProgress(Base):
    """
    Tracks a student's progress through the 5-lesson curriculum.
    Keyed by chart_id (the student's saved natal chart).
    """
    __tablename__ = "lesson_progress"

    id            = Column(Integer, primary_key=True, index=True)
    chart_id      = Column(Integer, ForeignKey("natal_charts.id"), nullable=False)
    lesson_index  = Column(Integer, nullable=False)      # 0-4
    completed     = Column(Boolean, default=False)
    score         = Column(Integer, default=0)            # correct quiz answers
    max_score     = Column(Integer, default=0)            # total quiz questions
    time_spent_s  = Column(Integer, default=0)            # seconds on lesson
    notes         = Column(Text, default="")              # student notes
    completed_at  = Column(DateTime, nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    chart = relationship("NatalChart", back_populates="lesson_progress")

    def to_dict(self) -> dict:
        return {
            "id":           self.id,
            "chart_id":     self.chart_id,
            "lesson_index": self.lesson_index,
            "completed":    self.completed,
            "score":        self.score,
            "max_score":    self.max_score,
            "time_spent_s": self.time_spent_s,
            "notes":        self.notes,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
