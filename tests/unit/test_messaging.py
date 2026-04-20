import pytest
from unittest.mock import MagicMock, patch
from src.core.messaging import EventPublisher, EventSubscriber
from src.core.events import BaseEvent, ImageSubmittedPayload

@patch('src.core.messaging.redis.Redis')
def test_publisher_sends_valid_json(mock_redis_class):
    # Setup mock
    mock_redis_instance = MagicMock()
    mock_redis_class.return_value = mock_redis_instance
    
    # Initialize publisher
    publisher = EventPublisher()
    
    # Create a test event
    payload = ImageSubmittedPayload(image_id="img123", path="/test.jpg", source="pytest")
    event = BaseEvent(topic="image.submitted", payload=payload.model_dump())
    
    # Execute
    publisher.publish(event)
    
    # Assert publish was called exactly once
    mock_redis_instance.publish.assert_called_once()
    
    # Check the arguments passed to redis.publish
    called_topic, called_message = mock_redis_instance.publish.call_args[0]
    assert called_topic == "image.submitted"
    assert "img123" in called_message
    assert "event_id" in called_message

@patch('src.core.messaging.redis.Redis')
def test_subscriber_ignores_malformed_data(mock_redis_class):
    mock_pubsub = MagicMock()
    # Simulate Redis yielding one valid message and one garbage message
    valid_json = '{"topic": "test", "event_id": "123e4567-e89b-12d3-a456-426614174000", "timestamp": "2026-04-16T12:00:00Z", "payload": {}}'
    mock_pubsub.listen.return_value = [
        {'type': 'message', 'data': valid_json},
        {'type': 'message', 'data': 'not a real json string'}
    ]
    
    mock_redis_instance = MagicMock()
    mock_redis_instance.pubsub.return_value = mock_pubsub
    mock_redis_class.return_value = mock_redis_instance
    
    # Execute
    subscriber = EventSubscriber()
    subscriber.subscribe(["test"])
    
    # We should only get 1 yielded event back, because the second one failed parsing
    events = list(subscriber.listen())
    assert len(events) == 1
    assert events[0].topic == "test"