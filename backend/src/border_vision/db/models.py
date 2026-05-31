import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, create_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    source = Column(String(512), nullable=False)
    boundary_line_y = Column(Integer, nullable=True)
    calibration = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class CrossingEvent(Base):
    __tablename__ = "crossing_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    camera_id = Column(Integer, nullable=True)
    track_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    direction = Column(String(10), nullable=False)
    direction = Column(String(10), nullable=False)
    foot_x = Column(Integer, nullable=True)
    foot_y = Column(Integer, nullable=True)
    bag_count = Column(Integer, default=0)
    bag_types = Column(Text, nullable=True)
    review_status = Column(String(20), default="auto_accepted")
    fusion_score = Column(Float, nullable=True)
    match_type = Column(String(20), nullable=True)
    person_id = Column(Integer, nullable=True)
    metadata_json = Column(Text, nullable=True)
