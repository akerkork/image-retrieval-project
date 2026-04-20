from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# Base Envelope
class BaseEvent(BaseModel):
    """
    The standard event envelope required for all messages in the system.
    """
    type: str = "event"
    topic: str
    # Automatically generate a unique UUID if one isn't provided
    event_id: UUID = Field(default_factory=uuid4)
    # Automatically set the timestamp to current UTC time
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # The actual data
    payload: Dict[str, Any]


# Specific Payload Schemas
class ImageSubmittedPayload(BaseModel):
    """Payload schema for the 'image.submitted' topic."""
    image_id: str
    path: str
    source: str

class BoundingBox(BaseModel):
    """Helper schema for detected objects."""
    label: str
    bbox: List[float]
    conf: float

class InferenceCompletedPayload(BaseModel):
    """Payload schema for the 'inference.completed' topic"""
    image_id: str
    objects: List[BoundingBox]

class EmbeddingCreatedPayload(BaseModel):
    """Payload schema for the 'embedding.created' topic"""
    image_id: str
    object_id: int  # Index or ID of the specific object in the image
    embedding: List[float]
    
class QuerySubmittedPayload(BaseModel):
    """Payload schema for the 'query.submitted' topic"""
    query_id: str
    text: str

class AnnotationCorrectedPayload(BaseModel):
    """Payload schema for the 'annotation.corrected' topic"""
    image_id: str
    # The corrected list of objects/bounding boxes
    objects: List[BoundingBox]

class QueryEmbeddingCreatedPayload(BaseModel):
    """Payload schema for the 'query_embedding.created' topic"""
    query_id: str
    embedding: List[float]
    k: int = 5

class SearchResult(BaseModel):
    """Helper schema for individual search results"""
    image_id: str
    distance: float

class QueryCompletedPayload(BaseModel):
    """Payload schema for the 'query.completed' topic"""
    query_id: str
    results: List[SearchResult]