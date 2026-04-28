import os
import uuid
import shutil
from src.core.messaging import EventPublisher, EventSubscriber
from src.core.events import BaseEvent, ImageSubmittedPayload

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def run_upload_service():
    subscriber = EventSubscriber()
    publisher = EventPublisher()
    
    subscriber.subscribe(["upload.requested"])
    print(f"[UploadService] Listening for 'upload.requested' events... (Saving to ./{UPLOAD_DIR})")
    
    for event in subscriber.listen():
        original_path = event.payload.get("file_path")
        source = event.payload.get("source", "unknown")
        
        print(f"\n[UploadService] Processing upload request for: {original_path}")
        
        if not os.path.exists(original_path):
            print(f"[UploadService] ERROR: File not found at {original_path}")
            continue
            
        # Generate an unique ID
        image_id = f"img_{uuid.uuid4().hex[:8]}"
        
        # Copy the file into the Upload Service's managed directory
        ext = original_path.split('.')[-1] if '.' in original_path else 'jpg'
        new_file_path = os.path.join(UPLOAD_DIR, f"{image_id}.{ext}")
        
        try:
            shutil.copy2(original_path, new_file_path)
            print(f"[UploadService] Successfully copied file to {new_file_path}")
            
            # Publish the official image.submitted event
            payload = ImageSubmittedPayload(
                image_id=image_id,
                path=new_file_path,
                source=source
            )
            out_event = BaseEvent(topic="image.submitted", payload=payload.model_dump())
            publisher.publish(out_event)
            print(f"[UploadService] Published 'image.submitted' for {image_id}")
            
        except Exception as e:
             print(f"[UploadService] Failed to process upload: {e}")

if __name__ == "__main__":
    run_upload_service()