import asyncio
import json
import logging
import threading
import time
from typing import List, Set
from fastapi import WebSocket, WebSocketDisconnect
from kafka import KafkaConsumer

try:
    from backend.app.config import settings
except ModuleNotFoundError:
    from app.config import settings

logger = logging.getLogger("websocket-live")

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        
        dead_connections = []
        payload = json.dumps(message)
        async with self._lock:
            for connection in list(self.active_connections):
                try:
                    await connection.send_text(payload)
                except Exception:
                    dead_connections.append(connection)

            for dead in dead_connections:
                self.active_connections.discard(dead)

manager = ConnectionManager()

# Background Kafka consumer thread to stream prediction events to WebSocket clients
_consumer_thread = None
_consumer_running = False

def _kafka_listener(loop: asyncio.AbstractEventLoop):
    global _consumer_running
    logger.info(f"Starting WebSocket Kafka listener on topic {settings.TOPIC_CLASSIFICATION_RESULTS}...")
    try:
        consumer = KafkaConsumer(
            settings.TOPIC_CLASSIFICATION_RESULTS,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="latest",
            enable_auto_commit=True,
            group_id="neurostream-websocket-broadcaster"
        )
        _consumer_running = True
        for msg in consumer:
            if not _consumer_running:
                break
            data = msg.value
            asyncio.run_coroutine_threadsafe(manager.broadcast(data), loop)
    except Exception as e:
        logger.warning(f"WebSocket Kafka listener encountered error or disconnected: {e}")
    finally:
        _consumer_running = False

def start_kafka_listener(loop: asyncio.AbstractEventLoop):
    global _consumer_thread, _consumer_running
    if not _consumer_running:
        _consumer_thread = threading.Thread(target=_kafka_listener, args=(loop,), daemon=True)
        _consumer_thread.start()

async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # Ensure Kafka consumer is running
    loop = asyncio.get_event_loop()
    start_kafka_listener(loop)

    try:
        try:
            from backend.app.api.streaming import producer_instance
        except ModuleNotFoundError:
            from app.api.streaming import producer_instance

        def direct_broadcast(pred):
            try:
                asyncio.run_coroutine_threadsafe(manager.broadcast(pred), loop)
            except Exception:
                pass

        producer_instance.on_prediction_callback = direct_broadcast

        # Send cached recent predictions immediately to populate the UI
        for past_pred in reversed(producer_instance.recent_predictions[:10]):
            try:
                await websocket.send_text(json.dumps(past_pred))
            except Exception:
                pass
    except Exception as hook_err:
        logger.error(f"Error hooking producer to websocket: {hook_err}")

    try:
        # Keep connection open and receive optional ping / control messages
        while True:
            text = await websocket.receive_text()
            try:
                msg = json.loads(text)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong", "timestamp": time.time()}))
            except Exception:
                pass
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket exception: {e}")
        await manager.disconnect(websocket)

