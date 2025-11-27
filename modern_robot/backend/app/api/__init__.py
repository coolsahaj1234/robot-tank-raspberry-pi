from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.core.robot import robot

router = APIRouter()

@router.get("/status")
async def get_status():
    return {"status": "ok", "message": "Robot API is running"}

@router.get("/video/{cam_type}")
async def video_feed(cam_type: str):
    return StreamingResponse(
        robot.camera_manager.get_stream(cam_type), 
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
