import streamlit as st
import sys
import os
import uuid
from datetime import datetime

# Import backend services directly
try:
    from services.persona_detector import detect_persona
    from services.knowledge_base import search_knowledge_base
    from services.response_generator import generate_response
    from services.escalation_service import should_escalate, create_escalation_context
    from models.schemas import PersonaType, ChatMessage
except ImportError as e:
    st.error(f"Failed to import services: {e}\n\nMake sure the 'services' and 'models' folders are in the same directory as this script.")
    st.stop()

# ─── Page Config ───
st.set_page_config(
    page_title="SupportIQ – Persona-Adaptive Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Styling (Inject subtle layout tweaks) ───
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .stChatMessage { margin-bottom: 20px; border-radius: 12px; }
    .persona-badge { padding: 4px 10px; border-radius: 16px; font-size: 0.8rem; font-weight: 600; margin-bottom: 8px; display: inline-block; }
    .badge-tech { background: rgba(56,189,248,0.15); color: #38bdf8; border: 1px solid rgba(56,189,248,0.3); }
    .badge-executive { background: rgba(139,92,246,0.15); color: #a78bfa; border: 1px solid rgba(139,92,246,0.3); }
    .badge-frustrated { background: rgba(244,63,94,0.15); color: #fb7185; border: 1px solid rgba(244,63,94,0.3); }
    .badge-general { background: rgba(148,163,184,0.15); color: #94a3b8; border: 1px solid rgba(148,163,184,0.3); }
    .kb-card { background: rgba(255,255,255,0.03); border-radius: 8px; padding: 12px; margin-bottom: 8px; border-left: 3px solid #6366f1; }
    .stProgress > div > div > div > div { background-color: #f43f5e; }
    .sidebar .stButton button { width: 100%; text-align: left; }
</style>
""", unsafe_allow_html=True)

# ─── Initialize Session State ───
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "persona_data" not in st.session_state:
    st.session_state.persona_data = {
        "persona": PersonaType.GENERAL_USER,
        "confidence": 0.0,
        "frustration": 0.0,
        "signals": []
    }
if "kb_articles" not in st.session_state:
    st.session_state.kb_articles = []
if "escalation" not in st.session_state:
    st.session_state.escalation = None

# DEMO MESSAGES
DEMO_MESSAGES = {
    "⚙️ Technical Expert": "I'm integrating your REST API using OAuth 2.0. I'm getting a 401 on token refresh – the JWT seems valid but introspect returns expired=true. NTP is synced. Is there a clock skew window?",
    "👔 Business Executive": "Evaluating your enterprise rollout for Q2. I need ROI metrics, SOC 2 compliance status, and annual pricing for 200 seats.",
    "😤 Frustrated User": "This is RIDICULOUS! I've contacted support THREE TIMES and my account is STILL locked! I want a manager NOW or I'm demanding a full refund!!!",
}

# ─── Sidebar Layout ───
with st.sidebar:
    st.image("https://img.icons8.com/isometric/512/bot.png", width=80)
    st.title("SupportIQ Control")
    st.caption("Persona-Adaptive Agent Pipeline")
    
    st.divider()

    # --- Persona Detection Panel ---
    st.subheader("Current Persona")
    p_data = st.session_state.persona_data
    persona_type = p_data["persona"]
    
    badge_variant = {
        PersonaType.TECHNICAL_EXPERT: "badge-tech",
        PersonaType.BUSINESS_EXECUTIVE: "badge-executive",
        PersonaType.FRUSTRATED_USER: "badge-frustrated",
        PersonaType.GENERAL_USER: "badge-general"
    }.get(persona_type, "badge-general")
    
    persona_label = persona_type.value.replace('_', ' ').title()
    st.markdown(f'<div class="persona-badge {badge_variant}">{persona_label} ({int(p_data["confidence"]*100)}%)</div>', unsafe_allow_html=True)
    
    if p_data["signals"]:
        st.caption("Signals Detected:")
        st.write(", ".join(p_data["signals"][:5]))

    st.divider()

    # --- Frustration Panel ---
    st.subheader("Frustration Level")
    f_score = p_data["frustration"]
    st.progress(f_score, text=f"{int(f_score*100)}%")
    if f_score > 0.7:
        st.warning("High Frustration: Priority escalation required.")

    st.divider()

    # --- Knowledge Base Panel ---
    st.subheader("KB Articles Used")
    if not st.session_state.kb_articles:
        st.info("No articles retrieved yet.")
    else:
        for art in st.session_state.kb_articles:
            with st.container():
                st.markdown(f"""
                <div class="kb-card">
                    <div style="font-size:0.75rem; color:#888;">{art.article_id}</div>
                    <div style="font-weight:600; margin-bottom:4px;">{art.title}</div>
                    <div style="font-size:0.7rem; display:flex; justify-content:space-between;">
                        <span>{art.category}</span>
                        <span style="color:#6366f1;">{int(art.relevance_score*100)}% Match</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # --- Demo Area ---
    st.divider()
    st.subheader("Quick Demos")
    for label, text in DEMO_MESSAGES.items():
        if st.button(label):
            st.session_state.demo_text = text

# ─── Main Chat Window ───
st.title("🤝 How can I help today?")
st.markdown("I automatically adapt my tone and knowledge depth based on your persona.")

# Display Escalation Banner if active
if st.session_state.escalation:
    ctx = st.session_state.escalation
    st.error(f"🚨 **Escalation Triggered**: {ctx.reason.replace('_', ' ').title()}\n\n"
             f"Assigned to **{ctx.recommended_team}** | Priority: **{ctx.priority}**")
    with st.expander("View Escalation Context (Agent Handoff)"):
        st.json(ctx.dict())
    if st.button("Resume Chat (Clear Escalation)"):
        st.session_state.escalation = None
        st.rerun()

# Display Messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🤖" if msg["role"]=="assistant" else "👤"):
        if "persona" in msg:
            badge_class = {
                "technical_expert": "badge-tech",
                "business_executive": "badge-executive",
                "frustrated_user": "badge-frustrated",
                "general_user": "badge-general"
            }.get(msg["persona"], "badge-general")
            st.markdown(f'<div class="persona-badge {badge_class}">{msg["persona"].replace("_", " ").title()} Tone</div>', unsafe_allow_html=True)
        st.markdown(msg["content"])

# Chat Input
input_placeholder = "Type your request here..."
if "demo_text" in st.session_state:
    query = st.chat_input(input_placeholder, key="chat_input", on_submit=None) # placeholder doesn't work well with reruns
    # Hack to handle demo button click
    current_input = st.session_state.demo_text
    del st.session_state.demo_text
else:
    current_input = st.chat_input(input_placeholder)

if current_input:
    # ─── Orchestration Pipeline ───
    
    # 1. Detect Persona
    hist = [m["content"] for m in st.session_state.messages if m["role"] == "user"]
    p_result = detect_persona(current_input, hist)
    st.session_state.persona_data = {
        "persona": p_result.persona,
        "confidence": p_result.confidence,
        "frustration": p_result.frustration_score,
        "signals": p_result.signals
    }

    # 2. Retrieve KB Content
    kb_results = search_knowledge_base(current_input, p_result.persona)
    st.session_state.kb_articles = kb_results[:3]

    # 3. Check for Escalation
    # Convert history to ChatMessage models for service
    chat_history = [ChatMessage(**m) for m in st.session_state.messages]
    
    es_triggered, es_reason = should_escalate(
        message=current_input,
        persona=p_result.persona,
        frustration_score=p_result.frustration_score,
        conversation_history=chat_history
    )
    
    if es_triggered:
        esc_ctx = create_escalation_context(
            session_id=st.session_state.session_id,
            reason=es_reason,
            persona=p_result.persona,
            frustration_score=p_result.frustration_score,
            conversation_history=chat_history,
            current_message=current_input
        )
        st.session_state.escalation = esc_ctx

    # 4. Generate Response
    response_text, suggestions = generate_response(
        message=current_input,
        persona=p_result.persona,
        kb_articles=kb_results,
        should_escalate=es_triggered,
        frustration_score=p_result.frustration_score
    )

    # Add to state and Rerun
    st.session_state.messages.append({"role": "user", "content": current_input})
    st.session_state.messages.append({
        "role": "assistant", 
        "content": response_text,
        "persona": p_result.persona.value
    })
    st.rerun()

if not st.session_state.messages:
    st.info("👋 Select a demo above or type a message to see the persona detection in action.")
