import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/v2", tags=["stream"])

_pipeline = None


def set_pipeline(pipeline):
    global _pipeline
    _pipeline = pipeline


def _mjpeg_generator():
    while True:
        if _pipeline is None:
            break
        jpeg = _pipeline.get_frame_jpeg()
        if jpeg is None:
            asyncio.sleep(0.03)
            continue
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n"
            b"Content-Length: " + str(len(jpeg)).encode() + b"\r\n\r\n"
            + jpeg
            + b"\r\n"
        )
        asyncio.sleep(0)


@router.get("/stream/live")
async def live_stream():
    return StreamingResponse(
        _mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


_ws_connections = set()


async def broadcast_event(event: dict):
    dead = set()
    for ws in _ws_connections:
        try:
            await ws.send_json(event)
        except Exception:
            dead.add(ws)
    _ws_connections -= dead


@router.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    await websocket.accept()
    _ws_connections.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        _ws_connections.discard(websocket)
    except Exception:
        _ws_connections.discard(websocket)
