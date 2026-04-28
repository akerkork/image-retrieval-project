import os
from google import genai
from src.core.messaging import EventPublisher, EventSubscriber
from src.core.events import BaseEvent, EmbeddingCreatedPayload, QueryEmbeddingCreatedPayload

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def run_embedding_service():
    subscriber = EventSubscriber()
    publisher = EventPublisher()
    
    subscriber.subscribe(["inference.completed", "query.submitted"])
    print("[EmbeddingService] Listening for events...")
    
    for event in subscriber.listen():
        
        # FLOW 1: Embed Image Objects
        if event.topic == "inference.completed":
            image_id = event.payload.get("image_id")
            objects = event.payload.get("objects", [])
            
            for idx, obj in enumerate(objects):
                label = obj.get("label", "")
                
                # New SDK format for embeddings
                result = client.models.embed_content(
                    model="text-embedding-004",
                    contents=label
                )
                
                payload = EmbeddingCreatedPayload(
                    image_id=image_id, 
                    object_id=idx, 
                    embedding=result.embeddings[0].values
                )
                out_event = BaseEvent(topic="embedding.created", payload=payload.model_dump())
                publisher.publish(out_event)
                print(f"[EmbeddingService] Embedded object '{label}' for {image_id}.")

        # FLOW 2: Embed Natural Language Search Query
        elif event.topic == "query.submitted":
            query_id = event.payload.get("query_id")
            text = event.payload.get("text")
            
            result = client.models.embed_content(
                model="text-embedding-004",
                contents=text
            )
            
            payload = QueryEmbeddingCreatedPayload(
                query_id=query_id,
                embedding=result.embeddings[0].values,
                k=3
            )
            out_event = BaseEvent(topic="query_embedding.created", payload=payload.model_dump())
            publisher.publish(out_event)
            print(f"[EmbeddingService] Embedded search query {query_id}.")

if __name__ == "__main__":
    run_embedding_service()