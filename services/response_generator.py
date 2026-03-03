"""
Response Generation Service
Generates persona-adaptive responses using tone templates and KB content.
"""
import re
from typing import List
from models.schemas import PersonaType, KnowledgeBaseResult


# ─────────────────────────────────────────────
# Tone Configuration per Persona
# ─────────────────────────────────────────────

PERSONA_TONES = {
    PersonaType.TECHNICAL_EXPERT: {
        "name": "Technical Precision",
        "style": "precise, detailed, code-aware, peer-to-peer",
        "greeting_variants": [
            "Let me walk you through the technical details.",
            "Here's the technical breakdown:",
            "Good question — let me get into the specifics.",
        ],
        "follow_up": (
            "\n\n---\n**Need more depth?** I can provide:\n"
            "- Full API reference documentation\n"
            "- Sample code snippets in Python, Node.js, or cURL\n"
            "- Access to our developer sandbox environment"
        ),
    },
    PersonaType.FRUSTRATED_USER: {
        "name": "Empathetic Resolution",
        "style": "empathetic, urgent, solution-first, reassuring",
        "greeting_variants": [
            "I completely understand your frustration, and I'm going to fix this right now.",
            "I hear you — this is unacceptable, and we'll resolve it immediately.",
            "I sincerely apologize for the trouble you've experienced. Let's get this sorted out.",
        ],
        "follow_up": (
            "\n\n---\n**You won't have to deal with this much longer.** "
            "If this doesn't resolve it, I will personally escalate to a senior specialist "
            "who will contact you directly. Would you prefer a callback or email followup?"
        ),
    },
    PersonaType.BUSINESS_EXECUTIVE: {
        "name": "Executive Briefing",
        "style": "concise, ROI-focused, strategic, professional",
        "greeting_variants": [
            "Here's the executive summary of what you need to know:",
            "To address your business needs directly:",
            "From a strategic standpoint, here's what matters most:",
        ],
        "follow_up": (
            "\n\n---\n**Next steps:** Your dedicated Account Executive can arrange "
            "a 30-minute briefing to discuss implementation, SLAs, and ROI projections. "
            "Shall I schedule that for you?"
        ),
    },
    PersonaType.GENERAL_USER: {
        "name": "Friendly Guide",
        "style": "simple, encouraging, step-by-step, friendly",
        "greeting_variants": [
            "Great question! Here's everything you need to know:",
            "Happy to help! Let me explain that clearly:",
            "No worries — this is easier than it looks:",
        ],
        "follow_up": (
            "\n\n---\n**Still have questions?** I'm right here! "
            "Feel free to ask anything else, or I can connect you with our support team "
            "for extra help. 😊"
        ),
    },
}


# ─────────────────────────────────────────────
# Response Templates
# ─────────────────────────────────────────────

ESCALATION_MESSAGES = {
    PersonaType.TECHNICAL_EXPERT: (
        "\n\n> 🔧 **Escalating to Engineering Support**\n"
        "> I'm transferring you to our Tier-2 Technical team with your full conversation context, "
        "including all technical details discussed. Expected response time: **< 2 hours**. "
        "Reference ID will be sent to your email."
    ),
    PersonaType.FRUSTRATED_USER: (
        "\n\n> 🚨 **Immediate Escalation – Priority Ticket Created**\n"
        "> I'm connecting you with a senior support agent RIGHT NOW. "
        "I've already shared your full history so you won't need to repeat yourself. "
        "**You will be contacted within 15 minutes.** We will not rest until this is fixed."
    ),
    PersonaType.BUSINESS_EXECUTIVE: (
        "\n\n> 📋 **Escalating to Account Management**\n"
        "> Your dedicated Account Executive and our Customer Success Director have been notified. "
        "A comprehensive briefing document with your account history and issue details "
        "is being prepared. **Expected executive callback: within 1 hour.**"
    ),
    PersonaType.GENERAL_USER: (
        "\n\n> 💬 **Connecting You with a Human Agent**\n"
        "> I'm bringing in a real person to help you right now! "
        "They'll have everything we've talked about so you don't have to start over. "
        "Expected wait time: **3-5 minutes.** Hang tight! 😊"
    ),
}

NO_KB_RESPONSES = {
    PersonaType.TECHNICAL_EXPERT: (
        "I don't have a specific KB article for that, but let me help directly. "
        "Could you share the exact error message, request payload, or stack trace? "
        "That will let me pinpoint the issue faster."
    ),
    PersonaType.FRUSTRATED_USER: (
        "I want to make sure I get you the right answer immediately. "
        "Can you tell me exactly what you were doing when this happened? "
        "I'll find the solution or escalate right away."
    ),
    PersonaType.BUSINESS_EXECUTIVE: (
        "This appears to be a specialized inquiry. I'd like to connect you with the right expert "
        "who can provide a complete, accurate answer tailored to your business context. "
        "One moment while I arrange that."
    ),
    PersonaType.GENERAL_USER: (
        "Hmm, I want to make sure I give you the right information! "
        "Could you share a little more detail about what you're trying to do? "
        "I'll find the best answer for you."
    ),
}


def generate_response(
    message: str,
    persona: PersonaType,
    kb_articles: List[KnowledgeBaseResult],
    should_escalate: bool,
    frustration_score: float,
) -> tuple[str, List[str]]:
    """
    Generate a persona-adapted response.
    """
    # ─── 1. Identify "Conversational" or "Greeting" messages ───
    # These shouldn't have heavy KB articles or long follow-ups if they are just basic chat
    greeting_patterns = [
        r'\b(hi|hello|hey|greetings|morning|afternoon|evening)\b',
        r'\b(how are you|how is it going|what\'s up|sup)\b',
        r'\b(thanks?|thank you|thx|cool|ok|okay|fine|awesome|great)\b',
    ]
    is_greeting = any(re.search(pattern, message.lower()) for pattern in greeting_patterns)
    
    conversational_patterns = greeting_patterns + [
        r'\b(who are you|what can you do|how do you work)\b',
    ]
    is_conversational = any(re.search(pattern, message.lower()) for pattern in conversational_patterns)
    
    message_length = len(message.split())
    
    # If the message is VERY short (like "hi" or "ok"), treat as conversational
    # But if there's a KB article and it's NOT a greeting, we should probably show it
    if message_length <= 2 and not kb_articles:
        is_conversational = True

    tone_config = PERSONA_TONES[persona]

    # Pick greeting
    import hashlib
    idx = int(hashlib.md5(message.encode()).hexdigest(), 16) % len(tone_config["greeting_variants"])
    greeting = tone_config["greeting_variants"][idx]

    # Build response body
    if kb_articles and not is_greeting:
        # Use the top KB article as the main response
        top_article = kb_articles[0]
        response_body = (
            f"{greeting}\n\n"
            f"### {top_article.title}\n\n"
            f"{top_article.content}"
        )

        # Mention additional articles if more than 1
        if len(kb_articles) > 1:
            related = "\n\n---\n**Related articles:**\n"
            for article in kb_articles[1:]:
                related += f"- 📄 **{article.title}** ({article.category})\n"
            response_body += related
            
        # Add persona-specific follow-up
        response_body += tone_config["follow_up"]
    elif should_escalate:
        # If escalating, give a direct empathetic greeting and skip KB
        response_body = f"{greeting}\n\n{NO_KB_RESPONSES[persona]}"
    else:
        # Generic/Conversational response
        if is_conversational:
            # Simple short responses for chat
            if persona == PersonaType.FRUSTRATED_USER:
                response_body = greeting # Keep it simple and focused on fixing things
            else:
                response_body = f"{greeting}\n\nHow can I assist you further today?"
        else:
            response_body = f"{greeting}\n\n{NO_KB_RESPONSES[persona]}"
            response_body += tone_config["follow_up"]

    # Add escalation notice (always show if triggered)
    if should_escalate:
        response_body += ESCALATION_MESSAGES[persona]

    # Generate suggestions
    suggestions = _generate_suggestions(persona, kb_articles if not is_conversational else [], frustration_score)

    return response_body, suggestions


def _generate_suggestions(
    persona: PersonaType,
    kb_articles: List[KnowledgeBaseResult],
    frustration_score: float,
) -> List[str]:
    """Generate context-aware quick-reply suggestions."""
    base_suggestions = {
        PersonaType.TECHNICAL_EXPERT: [
            "Show me the full API reference",
            "Provide a code example",
            "What are the rate limits?",
            "How do I enable debug logging?",
            "Show me the OpenAPI spec",
        ],
        PersonaType.FRUSTRATED_USER: [
            "I want to speak with a human agent",
            "This still isn't working",
            "I want a refund",
            "Escalate this immediately",
            "What is your compensation policy?",
        ],
        PersonaType.BUSINESS_EXECUTIVE: [
            "Schedule a call with account manager",
            "What is the SLA guarantee?",
            "Show me pricing for enterprise",
            "I need an executive summary",
            "What are my contract renewal options?",
        ],
        PersonaType.GENERAL_USER: [
            "How do I get started?",
            "Can you explain that more simply?",
            "I need more help",
            "Connect me with support",
            "Show me a tutorial",
        ],
    }

    suggestions = base_suggestions[persona].copy()

    # Add article-specific suggestions
    if kb_articles:
        for article in kb_articles[:2]:
            suggestions.insert(0, f"Tell me more about {article.title}")

    return suggestions[:5]


def get_tone_description(persona: PersonaType) -> str:
    """Return a human-readable description of the tone used."""
    return PERSONA_TONES[persona]["name"]
