import numpy as np
from ultralytics import YOLO


class YOLODetector:
    def __init__(
        self,
        model_name: str = "yolov8s",
        confidence: float = 0.45,
        use_openvino: bool = True,
    ):
        if use_openvino:
            model_name = f"{model_name}_openvino_model"
        self.model = YOLO(model_name)
        self.confidence = confidence
        self.names = self.model.names

    def detect(self, frame: np.ndarray):
        results = self.model(
            frame,
            conf=self.confidence,
            verbose=False,
        )
        return results

    def get_persons_and_bags(self, results):
        detections = []
        if len(results) == 0:
            return detections
        boxes = results[0].boxes
        if boxes is None:
            return detections
        for i in range(len(boxes)):
            cls_id = int(boxes.cls[i].item())
            conf = float(boxes.conf[i].item())
            x1, y1, x2, y2 = boxes.xyxy[i].tolist()
            label = self.names.get(cls_id, "unknown")
            if label in ("person", "backpack", "handbag", "suitcase"):
                detections.append({
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    "confidence": conf,
                    "class_id": cls_id,
                    "label": label,
                })
        return detections
