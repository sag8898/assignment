"""
Escalation Service
Determines when to escalate and manages context handoff to human agents.
"""
import uuid
from datetime import datetime
from typing import List
from models.schemas import (
    PersonaType, EscalationReason, EscalationContext,
    EscalationRequest, EscalationResponse, ChatMessage
)


# ─────────────────────────────────────────────
# Escalation Rules
# ─────────────────────────────────────────────

ESCALATION_RULES = {
    "frustration_threshold": 0.65,     # Auto-escalate if frustration >= 65%
    "repeated_contact_threshold": 3,   # Escalate if user contacts 3+ times in session
    "explicit_keywords": [
        "speak to a human", "human agent", "real person", "speak with someone",
        "talk to a person", "escalate", "manager", "supervisor", "complaint",
        "refund immediately", "cancel my account", "legal action", "lawsuit",
        "your boss", "higher up", "transfer me"
    ],
    "complex_issue_keywords": [
        "data loss", "data breach", "security incident", "compliance violation",
        "production down", "outage", "critical", "cannot access", "system failure",
        "all users affected", "entire company", "revenue impact"
    ],
}

TEAM_ROUTING = {
    PersonaType.TECHNICAL_EXPERT: {
        "team": "Tier-2 Engineering Support",
        "description": "Senior engineers with deep system access",
        "wait_time": "< 2 hours",
        "priority_multiplier": 1.2,
    },
    PersonaType.FRUSTRATED_USER: {
        "team": "Priority Customer Experience",
        "description": "Specialized de-escalation and resolution team",
        "wait_time": "< 15 minutes",
        "priority_multiplier": 2.0,
    },
    PersonaType.BUSINESS_EXECUTIVE: {
        "team": "Enterprise Account Management",
        "description": "Account executives and Customer Success Directors",
        "wait_time": "< 1 hour",
        "priority_multiplier": 1.8,
    },
    PersonaType.GENERAL_USER: {
        "team": "General Customer Support",
        "description": "Trained support specialists",
        "wait_time": "3-5 minutes",
        "priority_multiplier": 1.0,
    },
}


def should_escalate(
    message: str,
    persona: PersonaType,
    frustration_score: float,
    conversation_history: List[ChatMessage],
) -> tuple[bool, EscalationReason | None]:
    """
    Determine if the conversation should be escalated to a human agent.

    Returns:
        (should_escalate: bool, reason: EscalationReason | None)
    """
    message_lower = message.lower()

    # Rule 1: Explicit escalation request
    for keyword in ESCALATION_RULES["explicit_keywords"]:
        if keyword in message_lower:
            return True, EscalationReason.EXPLICIT_REQUEST

    # Rule 2: High frustration
    if frustration_score >= ESCALATION_RULES["frustration_threshold"]:
        return True, EscalationReason.HIGH_FRUSTRATION

    # Rule 3: Complex/critical issue
    for keyword in ESCALATION_RULES["complex_issue_keywords"]:
        if keyword in message_lower:
            return True, EscalationReason.COMPLEX_ISSUE

    # Rule 4: Repeated contact (3+ messages in history from user)
    user_message_count = sum(1 for msg in conversation_history if msg.role == "user")
    if user_message_count >= ESCALATION_RULES["repeated_contact_threshold"]:
        # Only escalate on repeated contact if frustration is elevated
        if frustration_score >= 0.3:
            return True, EscalationReason.REPEATED_CONTACT

    return False, None


def generate_conversation_summary(
    conversation_history: List[ChatMessage],
    current_message: str,
    persona: PersonaType,
) -> str:
    """Generate a concise summary for the receiving human agent."""
    user_messages = [msg for msg in conversation_history if msg.role == "user"]
    user_messages_text = [f"- {msg.content}" for msg in user_messages[-5:]]

    summary = (
        f"**Customer Persona:** {persona.value.replace('_', ' ').title()}\n"
        f"**Conversation Length:** {len(conversation_history)} messages\n"
        f"**Current Issue:** {current_message[:300]}\n\n"
        f"**Recent Customer Messages:**\n" +
        "\n".join(user_messages_text[-3:]) if user_messages_text else "No previous messages"
    )
    return summary


def create_escalation_context(
    session_id: str,
    reason: EscalationReason,
    persona: PersonaType,
    frustration_score: float,
    conversation_history: List[ChatMessage],
    current_message: str,
) -> EscalationContext:
    """Create a full escalation context for handoff."""
    team_config = TEAM_ROUTING[persona]

    # Determine priority
    base_priority_score = frustration_score * team_config["priority_multiplier"]
    if reason in (EscalationReason.COMPLEX_ISSUE, EscalationReason.HIGH_FRUSTRATION):
        base_priority_score += 0.3
    if reason == EscalationReason.EXPLICIT_REQUEST:
        base_priority_score += 0.2

    if base_priority_score >= 0.9:
        priority = "CRITICAL"
    elif base_priority_score >= 0.65:
        priority = "HIGH"
    elif base_priority_score >= 0.35:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    summary = generate_conversation_summary(conversation_history, current_message, persona)

    return EscalationContext(
        session_id=session_id,
        reason=reason,
        persona=persona,
        frustration_score=frustration_score,
        conversation_summary=summary,
        recommended_team=team_config["team"],
        priority=priority,
        customer_info={
            "session_id": session_id,
            "message_count": len(conversation_history),
            "escalation_reason": reason.value,
            "estimated_frustration": f"{frustration_score:.0%}",
        },
    )


def process_escalation(request: EscalationRequest) -> EscalationResponse:
    """Process a hard escalation request and create a ticket."""
    team_config = TEAM_ROUTING[request.persona]
    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"

    # Determine priority
    priority_score = request.frustration_score * team_config["priority_multiplier"]
    if request.reason in (EscalationReason.HIGH_FRUSTRATION, EscalationReason.COMPLEX_ISSUE):
        priority_score += 0.3

    if priority_score >= 0.9:
        priority = "CRITICAL"
    elif priority_score >= 0.65:
        priority = "HIGH"
    elif priority_score >= 0.35:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    context_summary = generate_conversation_summary(
        request.conversation_history,
        request.conversation_history[-1].content if request.conversation_history else "N/A",
        request.persona,
    )

    return EscalationResponse(
        ticket_id=ticket_id,
        assigned_team=team_config["team"],
        priority=priority,
        estimated_wait_time=team_config["wait_time"],
        context_summary=context_summary,
        success=True,
    )
