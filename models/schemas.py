from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class PersonaType(str, Enum):
    TECHNICAL_EXPERT = "technical_expert"
    FRUSTRATED_USER = "frustrated_user"
    BUSINESS_EXECUTIVE = "business_executive"
    GENERAL_USER = "general_user"


class EscalationReason(str, Enum):
    HIGH_FRUSTRATION = "high_frustration"
    COMPLEX_ISSUE = "complex_issue"
    REPEATED_CONTACT = "repeated_contact"
    EXPLICIT_REQUEST = "explicit_request"
    UNRESOLVED_ISSUE = "unresolved_issue"


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    persona: Optional[PersonaType] = None
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    message: str = Field(..., description="User's message")
    conversation_history: Optional[List[ChatMessage]] = Field(default=[], description="Previous conversation messages")


class PersonaDetectionResult(BaseModel):
    persona: PersonaType
    confidence: float  # 0.0 to 1.0
    signals: List[str]  # Detected signals that led to this classification
    frustration_score: float  # 0.0 to 1.0


class KnowledgeBaseResult(BaseModel):
    article_id: str
    title: str
    content: str
    category: str
    relevance_score: float
    tags: List[str]


class EscalationContext(BaseModel):
    session_id: str
    reason: EscalationReason
    persona: PersonaType
    frustration_score: float
    conversation_summary: str
    recommended_team: str
    priority: str  # LOW, MEDIUM, HIGH, CRITICAL
    customer_info: Dict[str, Any]


class ChatResponse(BaseModel):
    session_id: str
    message: str
    persona: PersonaType
    persona_confidence: float
    tone_used: str
    kb_articles: List[KnowledgeBaseResult]
    should_escalate: bool
    escalation_context: Optional[EscalationContext] = None
    frustration_score: float
    suggestions: List[str]


class EscalationRequest(BaseModel):
    session_id: str
    reason: Optional[EscalationReason] = None
    conversation_history: List[ChatMessage]
    persona: PersonaType
    frustration_score: float


class EscalationResponse(BaseModel):
    ticket_id: str
    assigned_team: str
    priority: str
    estimated_wait_time: str
    context_summary: str
    success: bool


class KBSearchRequest(BaseModel):
    query: str
    persona: Optional[PersonaType] = None
    category: Optional[str] = None
    limit: int = Field(default=3, ge=1, le=10)
