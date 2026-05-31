import cv2
import os
from pathlib import Path


class CameraSource:
    def __init__(self, source: str | int = 0, width: int = 640, height: int = 480):
        self.source = source
        self.width = width
        self.height = height
        self._cap = None

    def open(self):
        if self._cap is not None:
            self.release()
        if isinstance(self.source, str) and self.source.isdigit():
            self._cap = cv2.VideoCapture(int(self.source))
        elif isinstance(self.source, int):
            self._cap = cv2.VideoCapture(self.source)
        elif isinstance(self.source, str) and Path(self.source).exists():
            self._cap = cv2.VideoCapture(self.source)
        elif isinstance(self.source, str):
            self._cap = cv2.VideoCapture(self.source)
        else:
            self._cap = cv2.VideoCapture(0)

        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open camera source: {self.source}")

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        return self

    def read(self):
        if self._cap is None:
            return False, None
        return self._cap.read()

    def release(self):
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    @property
    def fps(self):
        if self._cap is None:
            return 0
        return self._cap.get(cv2.CAP_PROP_FPS)

    @property
    def frame_size(self):
        if self._cap is None:
            return (0, 0)
        w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return (w, h)

    def __del__(self):
        self.release()
