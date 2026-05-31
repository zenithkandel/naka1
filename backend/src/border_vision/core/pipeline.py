import asyncio
import cv2
import numpy as np
from datetime import datetime
from collections import defaultdict

from ..detection.yolo import YOLODetector
from ..tracking.tracker import TrackManager
from ..crossing.detector import CrossingDetector
from ..db.database import async_session, init_db
from ..db.models import CrossingEvent


class Pipeline:
    def __init__(
        self,
        camera_source,
        yolo_model: str = "yolov8s",
        confidence: float = 0.45,
        use_openvino: bool = True,
        hysteresis_frames: int = 5,
        boundary_line_y: int | None = None,
    ):
        self.camera = camera_source
        self.detector = YOLODetector(yolo_model, confidence, use_openvino)
        self.tracker = TrackManager()
        self.crossing = CrossingDetector(boundary_line_y, hysteresis_frames)
        self.frame = None
        self.annotated_frame = None
        self.tracked_objects = []
        self.frame_count = 0
        self._running = False
        self._event_callback = None
        self._frame_callback = None
        self._person_bags = defaultdict(list)

    def on_event(self, callback):
        self._event_callback = callback

    def on_frame(self, callback):
        self._frame_callback = callback

    async def run(self):
        self._running = True
        await init_db()

        self.camera.open()

        while self._running:
            ret, frame = self.camera.read()
            if not ret:
                await asyncio.sleep(0.01)
                continue

            self.frame_count += 1
            self.frame = frame.copy()

            results = self.detector.detect(frame)
            detections = self.detector.get_persons_and_bags(results)

            person_dets = [d for d in detections if d["label"] == "person"]
            bag_dets = [d for d in detections if d["label"] != "person"]

            tracks = self.tracker.update(person_dets, frame)
            self.tracked_objects = tracks

            active_ids = {t["track_id"] for t in tracks}
            self.tracker.remove_lost(active_ids)

            for track in tracks:
                tid = track["track_id"]
                foot_pos = self.tracker.get_foot_position(tid)
                event = self.crossing.update(tid, foot_pos)
                if event and self._event_callback:
                    bags_near = self._get_bags_for_track(track["bbox"], bag_dets)
                    event["bag_count"] = len(bags_near)
                    event["bag_types"] = ",".join(b["label"] for b in bags_near)
                    event["timestamp"] = datetime.utcnow().isoformat()
                    asyncio.create_task(self._persist_event(event))
                    self._event_callback(event)

            lost_ids = set(self.crossing._sides.keys()) - active_ids
            for lid in lost_ids:
                self.crossing.remove_track(lid)

            self.annotated_frame = self._draw_overlays(frame)

            if self._frame_callback:
                self._frame_callback(self.annotated_frame, tracks)

            await asyncio.sleep(0)

        self.camera.release()

    def stop(self):
        self._running = False

    def _get_bags_for_track(self, person_bbox, bag_dets, iou_thresh=0.1):
        px1, py1, px2, py2 = person_bbox
        p_area = (px2 - px1) * (py2 - py1)
        nearby = []
        for bag in bag_dets:
            bx1, by1, bx2, by2 = bag["bbox"]
            ix1 = max(px1, bx1)
            iy1 = max(py1, by1)
            ix2 = min(px2, bx2)
            iy2 = min(py2, by2)
            if ix2 > ix1 and iy2 > iy1:
                inter = (ix2 - ix1) * (iy2 - iy1)
                iou = inter / min(p_area, (bx2 - bx1) * (by2 - by1))
                if iou > iou_thresh:
                    nearby.append(bag)
        return nearby

    async def _persist_event(self, event: dict):
        async with async_session() as session:
            db_event = CrossingEvent(
                track_id=event["track_id"],
                direction=event["direction"],
                foot_x=event["foot_position"][0],
                foot_y=event["foot_position"][1],
                bag_count=event["bag_count"],
                bag_types=event["bag_types"],
            )
            session.add(db_event)
            await session.commit()

    def _draw_overlays(self, frame: np.ndarray) -> np.ndarray:
        annotated = frame.copy()

        if self.crossing.line_y is not None:
            cv2.line(
                annotated,
                (0, self.crossing.line_y),
                (annotated.shape[1], self.crossing.line_y),
                (0, 255, 255),
                2,
            )
            cv2.putText(
                annotated,
                "BOUNDARY",
                (10, self.crossing.line_y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2,
            )

        for track in self.tracked_objects:
            x1, y1, x2, y2 = track["bbox"]
            tid = track["track_id"]
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                annotated,
                f"ID {tid}",
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )
            foot = self.tracker.get_foot_position(tid)
            if foot:
                cv2.circle(annotated, foot, 4, (0, 0, 255), -1)

        return annotated

    def get_frame_jpeg(self) -> bytes | None:
        if self.annotated_frame is None:
            return None
        ret, jpeg = cv2.imencode(".jpg", self.annotated_frame)
        if not ret:
            return None
        return jpeg.tobytes()
