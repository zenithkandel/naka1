from collections import defaultdict


class CrossingDetector:
    def __init__(self, line_y: int = None, hysteresis_frames: int = 5):
        self.line_y = line_y
        self.hysteresis_frames = hysteresis_frames
        self._sides = {}
        self._counters = defaultdict(int)
        self._triggered = set()

    def set_boundary(self, line_y: int):
        self.line_y = line_y

    def get_side(self, foot_y: int) -> str:
        if self.line_y is None:
            return "unknown"
        return "below" if foot_y >= self.line_y else "above"

    def update(self, track_id: int, foot_position: tuple):
        if foot_position is None or self.line_y is None:
            return None

        foot_x, foot_y = foot_position
        current_side = self.get_side(foot_y)

        if track_id not in self._sides:
            self._sides[track_id] = current_side
            return None

        prev_side = self._sides[track_id]

        if current_side != prev_side:
            self._counters[track_id] += 1
            if self._counters[track_id] >= self.hysteresis_frames:
                if track_id not in self._triggered:
                    self._triggered.add(track_id)
                    direction = "in" if current_side == "above" else "out"
                    self._sides[track_id] = current_side
                    return {
                        "track_id": track_id,
                        "direction": direction,
                        "foot_position": (foot_x, foot_y),
                        "frame_side": current_side,
                    }
        else:
            if track_id in self._triggered:
                self._triggered.discard(track_id)
            self._counters[track_id] = 0

        return None

    def remove_track(self, track_id: int):
        self._sides.pop(track_id, None)
        self._counters.pop(track_id, None)
        self._triggered.discard(track_id)
