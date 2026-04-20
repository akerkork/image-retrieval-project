import uuid
from src.core.messaging import EventPublisher
from src.core.events import BaseEvent, ImageSubmittedPayload

def simulate_upload():
    publisher = EventPublisher()
    
    # Generate a random ID for the new image
    random_hex = uuid.uuid4().hex[:8]
    image_id = f"img_{random_hex}"
    
    payload = ImageSubmittedPayload(
        image_id=image_id,
        path=f"/data/uploads/{image_id}.jpg",
        source="cli_simulator"
    )
    
    event = BaseEvent(topic="image.submitted", payload=payload.model_dump())
    
    print(f"[UploadService] Publishing 'image.submitted' for {image_id}...")
    # Publish to Redis
    publisher.publish(event)

if __name__ == "__main__":
    simulate_upload()