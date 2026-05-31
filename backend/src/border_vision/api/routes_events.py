import csv
import io
from datetime import datetime
from fastapi import APIRouter, Query, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import StreamingResponse

from ..db.database import async_session
from ..db.models import CrossingEvent

router = APIRouter(prefix="/api/v2", tags=["events"])


@router.get("/events")
async def list_events(
    direction: str | None = None,
    track_id: int | None = None,
    limit: int = Query(default=100, le=1000),
    offset: int = 0,
):
    async with async_session() as session:
        stmt = select(CrossingEvent).order_by(CrossingEvent.timestamp.desc())
        if direction:
            stmt = stmt.where(CrossingEvent.direction == direction)
        if track_id is not None:
            stmt = stmt.where(CrossingEvent.track_id == track_id)
        stmt = stmt.offset(offset).limit(limit)
        result = await session.execute(stmt)
        events = result.scalars().all()
        return [
            {
                "id": e.id,
                "camera_id": e.camera_id,
                "track_id": e.track_id,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "direction": e.direction,
                "foot_x": e.foot_x,
                "foot_y": e.foot_y,
                "bag_count": e.bag_count,
                "bag_types": e.bag_types,
                "review_status": e.review_status,
                "fusion_score": e.fusion_score,
                "match_type": e.match_type,
                "person_id": e.person_id,
            }
            for e in events
        ]


@router.get("/events/{event_id}")
async def get_event(event_id: int):
    async with async_session() as session:
        stmt = select(CrossingEvent).where(CrossingEvent.id == event_id)
        result = await session.execute(stmt)
        e = result.scalar_one_or_none()
        if e is None:
            return {"error": "not found"}
        return {
            "id": e.id,
            "camera_id": e.camera_id,
            "track_id": e.track_id,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "direction": e.direction,
            "foot_x": e.foot_x,
            "foot_y": e.foot_y,
            "bag_count": e.bag_count,
            "bag_types": e.bag_types,
            "review_status": e.review_status,
            "fusion_score": e.fusion_score,
            "match_type": e.match_type,
            "person_id": e.person_id,
        }


@router.get("/export/events")
async def export_events(format: str = "csv"):
    async with async_session() as session:
        stmt = select(CrossingEvent).order_by(CrossingEvent.timestamp.desc())
        result = await session.execute(stmt)
        events = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "camera_id", "track_id", "timestamp", "direction",
        "foot_x", "foot_y", "bag_count", "bag_types", "review_status",
        "fusion_score", "match_type", "person_id",
    ])
    for e in events:
        writer.writerow([
            e.id, e.camera_id, e.track_id,
            e.timestamp.isoformat() if e.timestamp else "",
            e.direction, e.foot_x, e.foot_y,
            e.bag_count, e.bag_types, e.review_status,
            e.fusion_score, e.match_type, e.person_id,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=crossing_events.csv"},
    )
