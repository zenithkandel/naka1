from collections import defaultdict
import numpy as np
from boxmot import BoTSORT


class TrackManager:
    def __init__(self):
        self.tracker = BoTSORT(
            track_high_thresh=0.45,
            track_low_thresh=0.15,
            new_track_thresh=0.5,
            track_buffer=60,
            match_thresh=0.8,
            proximity_thresh=0.5,
            appearance_thresh=0.6,
            fuse_score=True,
            with_reid=False,
        )
        self.active_tracks = {}
        self.track_history = defaultdict(list)

    def update(self, detections: list, frame: np.ndarray):
        if len(detections) == 0:
            return []

        dets = np.array([
            [d["bbox"][0], d["bbox"][1], d["bbox"][2], d["bbox"][3], d["confidence"]]
            for d in detections
        ], dtype=np.float32)

        if len(dets) == 0:
            return []

        tracks = self.tracker.update(dets, frame)

        results = []
        for track in tracks:
            track_id = int(track[4])
            x1, y1, x2, y2 = map(int, track[:4])
            results.append({
                "track_id": track_id,
                "bbox": [x1, y1, x2, y2],
            })
            self.active_tracks[track_id] = {
                "bbox": [x1, y1, x2, y2],
            }

        self.active_tracks = {t["track_id"]: t for t in results}
        return results

    def get_foot_position(self, track_id: int):
        track = self.active_tracks.get(track_id)
        if track is None:
            return None
        x1, y1, x2, y2 = track["bbox"]
        return ((x1 + x2) // 2, y2)

    def remove_lost(self, track_ids: set):
        for tid in list(self.active_tracks.keys()):
            if tid not in track_ids:
                del self.active_tracks[tid]
