import random
import uuid
import pytest
from typing import List
from src.core.events import BaseEvent, ImageSubmittedPayload
from src.core.messaging import EventPublisher

class EventGenerator:
    """Generates synthetic events for testing and system simulation"""
    
    def __init__(self, publisher: EventPublisher, seed: int = None):
        self.publisher = publisher
        if seed is not None:
            random.seed(seed)

    def generate_image_submissions(self, count: int) -> List[BaseEvent]:
            """Generates a batch of valid image.submitted events."""
            events = []
            for i in range(count):
                # Use the random module to generate the hex string so it respects the seed
                random_hex = ''.join(random.choices('0123456789abcdef', k=8))
                image_id = f"img_{random_hex}"
                
                payload = ImageSubmittedPayload(
                    image_id=image_id,
                    path=f"/simulated/path/{image_id}.jpg",
                    source="generator"
                )
                event = BaseEvent(topic="image.submitted", payload=payload.model_dump())
                events.append(event)
            return events

    def inject_faults_and_publish(self, events: List[BaseEvent], duplicate_prob: float = 0.0, drop_prob: float = 0.0):
        """Publishes events while simulating real-world failures"""
        published_count = 0
        for event in events:
            # Simulate dropped messages
            if random.random() < drop_prob:
                continue 
                
            # Publish the event
            self.publisher.publish(event)
            published_count += 1
            
            # Simulate duplicate events
            if random.random() < duplicate_prob:
                self.publisher.publish(event) # Send the exact same event again
                published_count += 1
                
        return published_count

# Unit Tests for System Guarantees
class MockDatabase:
    """A simple mock to test idempotency state."""
    def __init__(self):
        self.processed_event_ids = set()
        self.stored_images = []

    def process_event(self, event: BaseEvent):
        # If seen this event_id, ignore it 
        if event.event_id in self.processed_event_ids:
            return False 
        
        self.processed_event_ids.add(event.event_id)
        self.stored_images.append(event.payload.get('image_id'))
        return True

def test_generator_deterministic_output():
    """Test that setting a seed produces the exact same events"""
    from unittest.mock import MagicMock
    mock_publisher = MagicMock()
    
    gen1 = EventGenerator(mock_publisher, seed=42)
    events1 = gen1.generate_image_submissions(3)
    
    gen2 = EventGenerator(mock_publisher, seed=42)
    events2 = gen2.generate_image_submissions(3)
    
    assert [e.payload['image_id'] for e in events1] == [e.payload['image_id'] for e in events2]

def test_system_idempotency_with_duplicates():
    """Test that duplicate events do not create duplicate state."""
    from unittest.mock import MagicMock
    mock_publisher = MagicMock()
    
    generator = EventGenerator(mock_publisher, seed=100)
    events = generator.generate_image_submissions(5)
    
    # Force a 100% duplicate rate (every event sent twice)
    generator.inject_faults_and_publish(events, duplicate_prob=1.0, drop_prob=0.0)
    
    # In the mock publisher, extract what was "published"
    published_events = [call.args[0] for call in mock_publisher.publish.call_args_list]
    
    assert len(published_events) == 10 # 5 original + 5 duplicates
    
    # Simulate a subscriber processing these events
    db = MockDatabase()
    processed_count = 0
    
    for event in published_events:
        if db.process_event(event):
            processed_count += 1
            
    # Even though 10 messages arrived, only 5 should be processed and stored
    assert processed_count == 5
    assert len(db.stored_images) == 5