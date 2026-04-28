import os
import uuid
import shutil
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import uvicorn
from src.core.messaging import EventPublisher
from src.core.events import BaseEvent, ImageSubmittedPayload

app = FastAPI(title="Upload Service")
publisher = EventPublisher()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Define the expected JSON payload from the CLI
class LocalUploadRequest(BaseModel):
    file_path: str

def publish_event(image_id: str, file_path: str):
    """Background task to publish the event."""
    payload = ImageSubmittedPayload(
        image_id=image_id,
        path=file_path,
        source="cli_user"
    )
    event = BaseEvent(topic="image.submitted", payload=payload.model_dump())
    publisher.publish(event)
    print(f"[UploadService] Published 'image.submitted' for {image_id}")

@app.post("/upload")
async def upload_image(request: LocalUploadRequest, background_tasks: BackgroundTasks):
    original_path = request.file_path
    
    # Verify the file actually exists where the CLI said it is
    if not os.path.exists(original_path):
        raise HTTPException(status_code=400, detail=f"File not found at {original_path}")
        
    # Generate a unique ID
    image_id = f"img_{uuid.uuid4().hex[:8]}"
    
    # Copy the file into the Upload Service's managed directory
    ext = original_path.split('.')[-1] if '.' in original_path else 'jpg'
    new_file_path = os.path.join(UPLOAD_DIR, f"{image_id}.{ext}")
    
    shutil.copy2(original_path, new_file_path)
    print(f"[UploadService] Copied file to {new_file_path}")
    
    # Publish the Redis event in the background
    background_tasks.add_task(publish_event, image_id, new_file_path)
    
    return {"message": "Upload successful", "image_id": image_id, "path": new_file_path}

def run_upload_service():
    print("[UploadService] Starting HTTP server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    run_upload_service()