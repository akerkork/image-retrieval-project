import os
import uuid
import sys
import threading
from src.core.messaging import EventPublisher, EventSubscriber
from src.core.events import BaseEvent, QuerySubmittedPayload, UploadRequestedPayload

def listen_for_notifications():
    """Background thread to listen for system notifications like completed uploads."""
    subscriber = EventSubscriber()
    subscriber.subscribe(["annotation.stored"])
    
    for event in subscriber.listen():
        image_id = event.payload.get("image_id")
        status = event.payload.get("status")
        
        print(f"\n[SYSTEM NOTIFICATION] Image {image_id} annotation stored (Status: {status}).")
        print("Enter search topic, or 'upload <filepath>' (or type 'exit' to quit): ", end="", flush=True)

def run_cli():
    publisher = EventPublisher()
    
    print("--------------------------------------------------")
    print("      IMAGE RETRIEVAL SYSTEM - INTERACTIVE CLI    ")
    print("--------------------------------------------------")
    
    notification_thread = threading.Thread(target=listen_for_notifications, daemon=True)
    notification_thread.start()
    
    try:
        while True:
            user_input = input("\nEnter search topic, or 'upload <filepath>' (or type 'exit' to quit): ").strip()
            
            if user_input.lower() == 'exit':
                print("Exiting...")
                sys.exit(0)
                
            if not user_input:
                continue

            # UPLOAD VIA REDIS EVENT
            if user_input.lower().startswith('upload '):
                raw_path = user_input[7:].strip()
                absolute_path = os.path.abspath(raw_path)
                
                if not os.path.exists(absolute_path):
                    print(f"Error: Could not find file at '{absolute_path}'. Please check the path.")
                    continue
                
                print(f"\n>> Requesting upload for '{absolute_path}'...")
                
                # Publish the upload request to Redis
                payload = UploadRequestedPayload(file_path=absolute_path, source="cli_user")
                event = BaseEvent(topic="upload.requested", payload=payload.model_dump())
                publisher.publish(event)
                
                print("Upload request sent. Waiting for background processing to complete...")
                
            # SEARCH VIA REDIS EVENT
            else:
                query_text = user_input
                query_id = f"qry_{uuid.uuid4().hex[:8]}"
                payload = QuerySubmittedPayload(query_id=query_id, text=query_text)
                event = BaseEvent(topic="query.submitted", payload=payload.model_dump())
                
                print(f"\n>> Sending query '{query_text}' to the system...")
                publisher.publish(event)
                
                subscriber = EventSubscriber()
                subscriber.subscribe(["query.completed"])
                
                print("Waiting for Vector DB results...")
                for response_event in subscriber.listen():
                    if response_event.payload.get("query_id") == query_id:
                        results = response_event.payload.get("results", [])
                        
                        print("\n================ RESULTS ================")
                        if not results:
                            print("No visually similar images found.")
                        else:
                            for idx, match in enumerate(results, 1):
                                match_image_id = match.get('image_id')
                                distance = match.get('distance')
                                print(f"{idx}. Image: {match_image_id} (Distance: {distance:.4f})")
                        print("=========================================")
                        break 

    except KeyboardInterrupt:
        print("\nExiting CLI...")
        sys.exit(0)

if __name__ == "__main__":
    run_cli()