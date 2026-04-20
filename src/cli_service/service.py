import uuid
import sys
from src.core.messaging import EventPublisher, EventSubscriber
from src.core.events import BaseEvent, QuerySubmittedPayload

def run_search_cli():
    publisher = EventPublisher()
    
    print("--------------------------------------------------")
    print("      IMAGE RETRIEVAL SYSTEM - SEARCH CLI         ")
    print("--------------------------------------------------")
    
    try:
        while True:
            # Get user input
            query_text = input("\nEnter search topic (or type 'exit' to quit): ").strip()
            
            if query_text.lower() == 'exit':
                print("Exiting...")
                sys.exit(0)
                
            if not query_text:
                continue

            # Publish the search query
            query_id = f"qry_{uuid.uuid4().hex[:8]}"
            payload = QuerySubmittedPayload(query_id=query_id, text=query_text)
            event = BaseEvent(topic="query.submitted", payload=payload.model_dump())
            
            print(f"\n>> Sending query '{query_text}' to the system...")
            publisher.publish(event)
            
            # Listen for the specific response from the Vector DB
            subscriber = EventSubscriber()
            subscriber.subscribe(["query.completed"])
            
            print("Waiting for Vector DB results...")
            for response_event in subscriber.listen():
                
                # Check if this response belongs to the specific query
                if response_event.payload.get("query_id") == query_id:
                    results = response_event.payload.get("results", [])
                    
                    print("\n================ RESULTS ================")
                    if not results:
                        print("No visually similar images found.")
                    else:
                        for idx, match in enumerate(results, 1):
                            image_id = match.get('image_id')
                            distance = match.get('distance')
                            print(f"{idx}. Image: {image_id} (Distance: {distance:.4f})")
                    print("=========================================")
                    break 

    except KeyboardInterrupt:
        print("\nExiting CLI...")
        sys.exit(0)

if __name__ == "__main__":
    run_search_cli()