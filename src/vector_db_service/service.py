import faiss
import numpy as np
from src.core.messaging import EventPublisher, EventSubscriber
from src.core.events import BaseEvent

DIMENSION = 3

def run_vector_db_service():
    subscriber = EventSubscriber()
    publisher = EventPublisher()
    
    # Initialize the FAISS Index
    index = faiss.IndexFlatL2(DIMENSION)
    
    # State management for ID mapping
    id_to_image = {}
    current_faiss_id = 0
    
    # Store event IDs we've already seen, advice from Gemini
    processed_event_ids = set()
    
    # Subscribe to Flow 1 (indexing) and Flow 2 (searching)
    subscriber.subscribe(["embedding.created", "query_embedding.created"])
    print(f"[VectorDB] FAISS Index initialized (Dim: {DIMENSION}). Listening for events...")
    
    for event in subscriber.listen():
        
        # If we've seen this event_id, ignore it completely (Gemini)
        if event.event_id in processed_event_ids:
            print(f"[VectorDB] Ignored duplicate event: {event.event_id}")
            continue
            
        # FLOW 1: Ingestion and indexing
        if event.topic == "embedding.created":
            image_id = event.payload.get("image_id")
            
            # Domain-level idempotency: Ensure we don't index the same image twice 
            # even if it comes in a slightly different event envelope (Gemini)
            if image_id in id_to_image.values():
                 print(f"[VectorDB] Image {image_id} is already indexed. Skipping.")
                 processed_event_ids.add(event.event_id)
                 continue

            raw_vector = event.payload.get("embedding")
            
            # We reshape the 1D list into a 1x3 array
            vector_np = np.array([raw_vector], dtype=np.float32)
            
            # Add the vector to the index
            index.add(vector_np)
            
            # Map the assigned FAISS integer to the image_id
            id_to_image[current_faiss_id] = image_id
            
            print(f"[VectorDB] Indexed vector for {image_id} at internal ID {current_faiss_id}.")
            print(f"[VectorDB] Total vectors in FAISS index: {index.ntotal}")
            
            current_faiss_id += 1
            
            # Mark this event as processed
            processed_event_ids.add(event.event_id)
            
        # FLOW 2: Retrieval
        elif event.topic == "query_embedding.created":
            query_id = event.payload.get("query_id")
            query_vector = event.payload.get("embedding")
            k_neighbors = event.payload.get("k", 5) # Default to top 5
            
            print(f"\n[VectorDB] Received search query {query_id}. Searching...")
            
            # Convert query to FAISS format
            query_np = np.array([query_vector], dtype=np.float32)
            
            # Do the search
            distances, match_ids = index.search(query_np, k_neighbors)
            
            # Map the FAISS integer IDs back to the string image_ids
            results = []
            for i, faiss_id in enumerate(match_ids[0]):
                if faiss_id != -1: # -1 means FAISS didn't find enough neighbors
                    matched_image = id_to_image.get(faiss_id, "unknown")
                    results.append({
                        "image_id": matched_image,
                        "distance": float(distances[0][i])
                    })
            
            # Broadcast the results back to the CLI
            out_payload = {
                "query_id": query_id,
                "results": results
            }
            out_event = BaseEvent(topic="query.completed", payload=out_payload)
            publisher.publish(out_event)
            print(f"[VectorDB] Published 'query.completed' with {len(results)} matches.")
            
            # Mark this event as processed
            processed_event_ids.add(event.event_id)

if __name__ == "__main__":
    run_vector_db_service()