import time
from src.core.messaging import EventPublisher, EventSubscriber
from src.core.events import BaseEvent, EmbeddingCreatedPayload

def run_embedding_service():
    subscriber = EventSubscriber()
    publisher = EventPublisher()
    
    # Subscribe to both inference and search
    subscriber.subscribe(["inference.completed", "query.submitted"])
    print("[EmbeddingService] Listening for events...")
    
    for event in subscriber.listen():
        
        # FLOW 1: image objects
        if event.topic == "inference.completed":
            image_id = event.payload.get("image_id")
            objects = event.payload.get("objects", [])
            
            print(f"\n[EmbeddingService] Generating embeddings for {len(objects)} object(s) in {image_id}...")
            time.sleep(1.5) 
            
            for idx, obj in enumerate(objects):
                # Dummy vector for the image object
                dummy_vector = [0.12, -0.45, 0.88] 
                
                payload = EmbeddingCreatedPayload(
                    image_id=image_id, 
                    object_id=idx, 
                    embedding=dummy_vector
                )
                out_event = BaseEvent(topic="embedding.created", payload=payload.model_dump())
                publisher.publish(out_event)
                
            print(f"[EmbeddingService] Published 'embedding.created' for {image_id}.")

        # FLOW 2: Natural Language Search
        elif event.topic == "query.submitted":
            query_id = event.payload.get("query_id")
            text = event.payload.get("text")
            
            print(f"\n[EmbeddingService] Vectorizing search query: '{text}'...")
            time.sleep(0.5) # Simulate NLP model time
            
            # Create a dummy vector slightly offset from our image vect so that FAISS will find it as a close match
            query_vector = [0.10, -0.40, 0.85] 
            
            out_payload = {
                "query_id": query_id,
                "embedding": query_vector,
                "k": 3 # Ask FAISS for the top 3 closest matches
            }
            out_event = BaseEvent(topic="query_embedding.created", payload=out_payload)
            publisher.publish(out_event)
            print(f"[EmbeddingService] Published 'query_embedding.created' for query {query_id}.")

if __name__ == "__main__":
    run_embedding_service()