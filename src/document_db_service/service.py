import time
from pymongo import MongoClient
from src.core.messaging import EventPublisher, EventSubscriber
from src.core.events import BaseEvent

def get_db_collection():
    """Establishes a connection to MongoDB and returns the annotations collection."""
    # Connects to default local MongoDB on port 27017
    client = MongoClient("mongodb://localhost:27017/")
    db = client["image_retrieval"]
    return db["annotations"]

def run_document_db_service():
    subscriber = EventSubscriber()
    publisher = EventPublisher()
    collection = get_db_collection()
    
    # Subscribe to both the initial submission and the inference completion
    subscriber.subscribe(["image.submitted", "inference.completed"])
    print("[DocumentDB] Connected to MongoDB. Listening for events...")
    
    for event in subscriber.listen():
        image_id = event.payload.get("image_id")
        
        if event.topic == "image.submitted":
            print(f"\n[DocumentDB] Initializing record for {image_id}...")
            
            # Create the initial JSON-like document
            document = {
                "_id": image_id,  # Use the image_id as the primary key
                "path": event.payload.get("path"),
                "source": event.payload.get("source"),
                "status": "processing",
                "created_at": event.timestamp.isoformat(),
                "objects": []
            }
            
            # don't crash if it already exists
            collection.update_one({"_id": image_id}, {"$set": document}, upsert=True)
            print(f"[DocumentDB] Record created in MongoDB for {image_id}.")
            
        elif event.topic == "inference.completed":
            print(f"\n[DocumentDB] Updating record for {image_id} with inference data...")
            
            # Update the existing document with the nested objects array
            update_data = {
                "status": "annotated",
                "objects": event.payload.get("objects"),
                "updated_at": event.timestamp.isoformat()
            }
            
            result = collection.update_one({"_id": image_id}, {"$set": update_data})
            
            if result.modified_count > 0 or result.matched_count > 0:
                print(f"[DocumentDB] MongoDB update successful for {image_id}.")
                
                # Broadcast that the annotation is safely stored
                out_event = BaseEvent(
                    topic="annotation.stored", 
                    payload={"image_id": image_id, "status": "success"}
                )
                publisher.publish(out_event)
            else:
                print(f"[DocumentDB] Warning: No existing record found for {image_id} to update.")

if __name__ == "__main__":
    run_document_db_service()