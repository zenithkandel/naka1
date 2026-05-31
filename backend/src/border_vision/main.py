import asyncio
import os
import sys
import signal
import argparse
import cv2
from dotenv import load_dotenv

from .core.camera import CameraSource
from .core.pipeline import Pipeline
from .api.app import app
from .api.routes_stream import set_pipeline, broadcast_event
from .db.database import init_db

load_dotenv()

_pipeline_ref = None


async def run_pipeline(camera_source, boundary_line_y=None):
    global _pipeline_ref

    cam = CameraSource(source=camera_source, width=640, height=480)

    pipeline = Pipeline(
        camera_source=cam,
        yolo_model=os.getenv("YOLO_MODEL", "yolov8s"),
        confidence=float(os.getenv("YOLO_CONFIDENCE", "0.45")),
        use_openvino=os.getenv("USE_OPENVINO", "true").lower() == "true",
        hysteresis_frames=int(os.getenv("HYSTERESIS_FRAMES", "5")),
        boundary_line_y=boundary_line_y,
    )

    set_pipeline(pipeline)
    _pipeline_ref = pipeline

    pipeline.on_event(lambda e: asyncio.create_task(broadcast_event(e)))

    await pipeline.run()


def parse_boundary_line(frame, window_name="BorderVision - Click to set boundary line"):
    print("Draw a boundary line by clicking two points on the frame.")
    print("Press any key after selecting to confirm, or 'c' to clear and skip.")

    points = []

    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            points.append((x, y))
            cv2.circle(param, (x, y), 4, (0, 255, 255), -1)
            if len(points) == 2:
                cv2.line(param, points[0], points[1], (0, 255, 255), 2)
            cv2.imshow(window_name, param)

    display = frame.copy()
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, mouse_callback, display)
    cv2.imshow(window_name, display)

    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('c'):
            points.clear()
            display = frame.copy()
            cv2.imshow(window_name, display)
        elif key != 255:
            break

    cv2.destroyWindow(window_name)

    if len(points) == 2:
        line_y = (points[0][1] + points[1][1]) // 2
        print(f"Boundary line set at y={line_y}")
        return line_y
    return None


def main():
    parser = argparse.ArgumentParser(description="BorderVision v2.0")
    parser.add_argument("--camera", type=str, default=None,
                        help="Camera source: device index, RTSP URL, or video file path")
    parser.add_argument("--boundary", type=int, default=None,
                        help="Boundary line Y coordinate (optional)")
    parser.add_argument("--calibrate", action="store_true",
                        help="Open calibration window to draw boundary line")
    parser.add_argument("--api-only", action="store_true",
                        help="Run API server without pipeline")
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)

    args = parser.parse_args()

    source = args.camera or os.getenv("CAMERA_SOURCE", "0")
    boundary_line_y = args.boundary

    if args.api_only:
        import uvicorn
        uvicorn.run(app, host=args.host, port=args.port)
        return

    if args.calibrate:
        cam = CameraSource(source=source, width=640, height=480)
        cam.open()
        ret, frame = cam.read()
        cam.release()
        if ret:
            boundary_line_y = parse_boundary_line(frame)
        else:
            print("Cannot read frame for calibration")
            sys.exit(1)

    host = args.host
    port = args.port

    async def start():
        server_task = asyncio.create_task(
            run_pipeline(source, boundary_line_y)
        )

        config = uvicorn.Config(app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)

        await asyncio.gather(
            server_task,
            server.serve(),
        )

    try:
        asyncio.run(start())
    except KeyboardInterrupt:
        if _pipeline_ref:
            _pipeline_ref.stop()
        print("\nBorderVision stopped.")


if __name__ == "__main__":
    main()
