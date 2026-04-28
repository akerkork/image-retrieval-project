import os
import json
from google import genai
from PIL import Image
from src.core.messaging import EventPublisher, EventSubscriber
from src.core.events import BaseEvent, InferenceCompletedPayload, BoundingBox

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def run_inference_service():
    subscriber = EventSubscriber()
    publisher = EventPublisher()
    
    subscriber.subscribe(["image.submitted"])
    print("[InferenceService] Listening for events...")
    
    for event in subscriber.listen():
        image_id = event.payload.get("image_id")
        image_path = event.payload.get("path")
        print(f"\n[InferenceService] Running Gemini Inference on {image_id}...")
        
        try:
            img = Image.open(image_path)
            prompt = """
            Detect the main objects in this image. 
            Return ONLY a raw JSON array. Do not use markdown formatting or code blocks.
            Format: [{"label": "string", "bbox": [ymin, xmin, ymax, xmax], "conf": 0.99}]
            """
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[prompt, img]
            )
            raw_text = response.text.strip()
            
            if raw_text.startswith('```json'):
                raw_text = raw_text[7:-3].strip()
                
            detections = json.loads(raw_text)
            objects = [BoundingBox(**det) for det in detections]
            
            payload = InferenceCompletedPayload(image_id=image_id, objects=objects)
            out_event = BaseEvent(topic="inference.completed", payload=payload.model_dump())
            publisher.publish(out_event)
            print(f"[InferenceService] Published {len(objects)} objects for {image_id}.")
            
        except Exception as e:
            print(f"[InferenceService] Failed to process {image_id}: {e}")

if __name__ == "__main__":
    run_inference_service()