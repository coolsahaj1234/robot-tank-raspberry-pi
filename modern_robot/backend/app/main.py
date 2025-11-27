from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import socketio
import asyncio
from app.core.robot import robot
from app.api import router as api_router

# Initialize FastAPI
app = FastAPI(title="Modern Robot Command Center", version="1.0.0")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the client URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO Setup
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio, app)

async def broadcast_status(state):
    await sio.emit('status', {'robot_state': state})

@app.on_event("startup")
async def startup_event():
    print("Starting Robot System...")
    robot.set_emit_status_callback(broadcast_status)
    await robot.start()

@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down Robot System...")
    await robot.stop()

# Include API Routes
app.include_router(api_router, prefix="/api")

# Socket.IO Events
@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    await sio.emit('status', {'status': 'connected', 'robot_state': robot.get_state()}, to=sid)

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

@sio.on('control_command')
async def handle_control(sid, data):
    # data: {'command': 'move', 'params': {'x': 0.5, 'y': 0.5}}
    await robot.execute_command(data)
    await sio.emit('robot_response', {'status': 'ok', 'action': data.get('command')}, to=sid)

@sio.on('set_autonomy')
async def set_autonomy(sid, data):
    # data: {'level': 'manual' | 'semi' | 'auto'}
    level = data.get('level')
    robot.set_autonomy_level(level)
    await sio.emit('autonomy_changed', {'level': level}, to=sid)

if __name__ == "__main__":
    uvicorn.run("app.main:socket_app", host="0.0.0.0", port=8000, reload=True)

