import time
from pymongo import MongoClient
from src.core.messaging import EventPublisher, EventSubscriber
from src.core.events import BaseEvent

def get_db_collection():
    """Establishes a connection to MongoDB and returns the annotations collection."""
    client = MongoClient("mongodb://localhost:27017/")
    db = client["image_retrieval"]
    return db["annotations"]

def run_document_db_service():
    subscriber = EventSubscriber()
    publisher = EventPublisher()
    collection = get_db_collection()
    
    # Subscribe to all 3 incoming flows for the database
    subscriber.subscribe(["image.submitted", "inference.completed", "annotation.corrected"])
    print("[DocumentDB] Connected to MongoDB. Listening for events...")
    
    for event in subscriber.listen():
        image_id = event.payload.get("image_id")
        
        if event.topic == "image.submitted":
            print(f"\n[DocumentDB] Initializing record for {image_id}...")
            document = {
                "_id": image_id,
                "path": event.payload.get("path"),
                "source": event.payload.get("source"),
                "status": "processing",
                "created_at": event.timestamp.isoformat(),
                "objects": []
            }
            collection.update_one({"_id": image_id}, {"$set": document}, upsert=True)
            print(f"[DocumentDB] Record created in MongoDB for {image_id}.")
            
        elif event.topic == "inference.completed":
            print(f"\n[DocumentDB] Updating record for {image_id} with inference data...")
            update_data = {
                "status": "annotated",
                "objects": event.payload.get("objects"),
                "updated_at": event.timestamp.isoformat()
            }
            result = collection.update_one({"_id": image_id}, {"$set": update_data})
            
            if result.modified_count > 0 or result.matched_count > 0:
                print(f"[DocumentDB] MongoDB update successful for {image_id}.")
                out_event = BaseEvent(
                    topic="annotation.stored", 
                    payload={"image_id": image_id, "status": "success"}
                )
                publisher.publish(out_event)
                
        # Handle manual corrections (gemini)
        elif event.topic == "annotation.corrected":
            print(f"\n[DocumentDB] Processing manual correction for {image_id}...")
            update_data = {
                "status": "corrected", # Notice the status change
                "objects": event.payload.get("objects"),
                "updated_at": event.timestamp.isoformat()
            }
            result = collection.update_one({"_id": image_id}, {"$set": update_data})
            
            if result.modified_count > 0 or result.matched_count > 0:
                print(f"[DocumentDB] MongoDB correction successful for {image_id}.")
                # Optional: You can broadcast annotation.stored again here if needed
                out_event = BaseEvent(
                    topic="annotation.stored", 
                    payload={"image_id": image_id, "status": "corrected"}
                )
                publisher.publish(out_event)

if __name__ == "__main__":
    run_document_db_service()