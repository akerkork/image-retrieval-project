import json
import redis
from typing import Iterator, List, Optional
from src.core.events import BaseEvent

class EventPublisher:
    """Handles publishing events to the Redis message broker"""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        # Allow injecting a mock redis client for testing
        self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def publish(self, event: BaseEvent) -> int:
        """
        Publishes a validated BaseEvent to its designated topic.
        Returns the number of subscribers that received the message.
        """
        # Serialize the Pydantic model to a JSON string
        message_data = event.model_dump_json()
        
        # Publish to the Redis channel matching the topic name
        return self.redis_client.publish(event.topic, message_data)


class EventSubscriber:
    """Handles subscribing to topics and getting incoming events"""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self.pubsub = self.redis_client.pubsub(ignore_subscribe_messages=True)

    def subscribe(self, topics: List[str]):
        """Subscribes to a list of topics"""
        self.pubsub.subscribe(*topics)

    def listen(self) -> Iterator[BaseEvent]:
        """
        Blocks and listens for incoming messages. 
        Gets parsed BaseEvent objects.
        """
        for message in self.pubsub.listen():
            if message and message['type'] == 'message':
                try:
                    # Attempt to parse the raw JSON back into the BaseEvent schema
                    event = BaseEvent.model_validate_json(message['data'])
                    yield event
                except Exception as e:
                    # Malformed events are logged and ignored, not crashed
                    print(f"Failed to parse incoming message: {e}")
