from pydantic import BaseModel
from fastapi import APIRouter, Depends, status, HTTPException, WebSocket
from fastapi.responses import JSONResponse, HTMLResponse
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from starlette.endpoints import WebSocketEndpoint
import typing
import asyncio
import json
import os

from modules.utils.local_logger import lambro_logger
from app.modules.html_streaming_template import html
from app.api_models.api_responses.trade_model import Trade


router = APIRouter()

class KafkaConfig(BaseModel):
    bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    client_id: str = os.getenv("KAFKA_CLIENT_ID", "fast_trades")
    topic: str = os.getenv("KAFKA_TOPIC", "fast_trades")

async def get_kafka_producer():
    """Dependency that provides and manages Kafka producer lifecycle"""
    config = KafkaConfig()
    producer = AIOKafkaProducer(
        bootstrap_servers=config.bootstrap_servers,
        client_id=config.client_id,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )
    try:
        await producer.start()
        lambro_logger.info(f"Connected to Kafka at {config.bootstrap_servers}")
        yield producer
    except Exception as e:
        lambro_logger.error(f"Kafka connection failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kafka connection unavailable"
        )
    finally:
        await producer.stop()

@router.post(
    "/fast_trade/",
    response_description="Create a fast trade",
    status_code=status.HTTP_201_CREATED
)
async def create_trade(
    trade: Trade,
    producer: AIOKafkaProducer = Depends(get_kafka_producer)
):
    """
    Create a new trade and publish it to Kafka with:
    - Automatic JSON serialization
    - Error handling for Kafka connectivity issues
    - Structured logging
    """
    config = KafkaConfig()
    
    try:
        await producer.send_and_wait(
            config.topic,
            value=trade.model_dump(),
            key=str(trade.id).encode()  # Use trade ID for partitioning
        )
        lambro_logger.info(f"Trade {trade.id} sent to Kafka topic {config.topic}")
        
        return {
            "status": "created",
            "topic": config.topic,
            "trade_id": str(trade.id),
            "message": "Trade successfully queued for processing"
        }
        
    except Exception as e:
        lambro_logger.error(f"Kafka connection error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Message queue unavailable"
        )
        
    except Exception as e:
        lambro_logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/health")
async def health_check(producer: AIOKafkaProducer = Depends(get_kafka_producer)):
    """Endpoint to verify Kafka connectivity"""
    try:
        # Check if producer can communicate with Kafka
        await producer.client()
        return {"status": "healthy", "kafka": "connected"}
    except Exception:
        return {"status": "unhealthy", "kafka": "disconnected"}


@router.websocket_route("/analytics/")
class WebsocketConsumer(WebSocketEndpoint):
    
    async def on_connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        await websocket.send_json({"Trader": "connected", "Quantity": 0})

        loop = asyncio.get_event_loop()
        self.consumer = AIOKafkaConsumer(
            "fast_trades",
            loop=loop, 
            client_id="fast_trades", 
            bootstrap_servers="localhost:29092",
            enable_auto_commit=False,
        )

        await self.consumer.start()

        self.consumer_task = asyncio.create_task(
            self.send_consumer_message(websocket=websocket, topicname="fast_trades")
        )
        lambro_logger.info("connected")
    
    async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
        self.consumer_task.cancel()
        await self.consumer.stop()
        lambro_logger.info(f"counter: {self.counter}")
        lambro_logger.info("disconnected")
        lambro_logger.info("consumer stopped")

    async def on_receive(self, websocket: WebSocket, data: typing.Any) -> None:
        await websocket.send_json({"Trader": data})

    async def send_consumer_message(self, websocket: WebSocket, topicname: str) -> None:
        self.counter = 0
        while True:
            data = await consume(self.consumer, topicname)
            dataJson = json.loads(data)
            await websocket.send_json(dataJson)
            self.counter = self.counter + 1



@router.get("/analytics/")
async def get_websocket():
    return HTMLResponse(html)