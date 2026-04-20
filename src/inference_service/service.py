import time
from src.core.messaging import EventPublisher, EventSubscriber
from src.core.events import BaseEvent, InferenceCompletedPayload, BoundingBox

def run_inference_service():
    subscriber = EventSubscriber()
    publisher = EventPublisher()
    
    subscriber.subscribe(["image.submitted"])
    print("[InferenceService] Listening for 'image.submitted' events...")
    
    for event in subscriber.listen():
        image_id = event.payload.get("image_id")
        print(f"\n[InferenceService] Received {image_id}. Running simulated ML inference...")
        
        # Simulate the time it takes to run an object detection model
        time.sleep(2)
        
        # Create dummy detected objects
        dummy_box = BoundingBox(label="car", bbox=[10.0, 20.0, 150.0, 200.0], conf=0.95)
        payload = InferenceCompletedPayload(image_id=image_id, objects=[dummy_box])
        
        # Wrap it in the base envelope and publish
        out_event = BaseEvent(topic="inference.completed", payload=payload.model_dump())
        publisher.publish(out_event)
        print(f"[InferenceService] Published 'inference.completed' for {image_id}.")

if __name__ == "__main__":
    run_inference_service()