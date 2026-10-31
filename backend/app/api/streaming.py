import os
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

try:
    from backend.app.config import settings
except ModuleNotFoundError:
    from app.config import settings

from producer.app.producer import EEGStreamingProducer

router = APIRouter(prefix="/api/streaming", tags=["Streaming"])
logger = logging.getLogger("streaming-api")

# Singleton producer instance for backend
raw_dir = os.path.join(settings.DATA_DIR, "raw")
producer_instance = EEGStreamingProducer(
    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    raw_topic=settings.TOPIC_RAW_WINDOWS,
    data_dir=raw_dir
)

class StartRequest(BaseModel):
    participant_id: Optional[str] = "S001"
    recording_id: Optional[str] = "S001R04"
    replay_speed: float = 1.0
    from_beginning: bool = False
    loop: bool = True

class SpeedRequest(BaseModel):
    speed: float

@router.get("/status")
def get_streaming_status():
    return producer_instance.get_status()

@router.get("/recent-predictions")
def get_recent_predictions():
    return producer_instance.recent_predictions

@router.post("/start")
def start_streaming(req: StartRequest):
    try:
        producer_instance.start_streaming(
            participant_id=req.participant_id or "S001",
            recording_id=req.recording_id or "S001R04",
            replay_speed=req.replay_speed,
            from_beginning=req.from_beginning,
            loop=req.loop
        )
        return {
            "status": "success",
            "message": f"Started streaming {req.recording_id} at {req.replay_speed}x speed",
            "state": producer_instance.state
        }
    except Exception as e:
        logger.error(f"Failed to start streaming: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pause")
def pause_streaming():
    producer_instance.pause_streaming()
    return {"status": "success", "state": producer_instance.state}

@router.post("/resume")
def resume_streaming():
    producer_instance.resume_streaming()
    return {"status": "success", "state": producer_instance.state}

@router.post("/stop")
def stop_streaming():
    producer_instance.stop_streaming()
    return {"status": "success", "state": producer_instance.state}

@router.post("/speed")
def set_streaming_speed(req: SpeedRequest):
    producer_instance.set_replay_speed(req.speed)
    return {"status": "success", "speed": producer_instance.replay_speed}

@router.post("/replay")
def replay_streaming(req: StartRequest):
    producer_instance.stop_streaming()
    producer_instance.start_streaming(
        participant_id=req.participant_id or "S001",
        recording_id=req.recording_id or "S001R04",
        replay_speed=req.replay_speed,
        from_beginning=True
    )
    return {
        "status": "success",
        "message": f"Replaying {req.recording_id} from beginning at {req.replay_speed}x speed",
        "state": producer_instance.state
    }

