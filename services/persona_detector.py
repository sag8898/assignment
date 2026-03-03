"""
Persona Detection Service
Analyzes user messages to detect customer persona type and frustration level.
"""
import re
from typing import List, Tuple
from models.schemas import PersonaType, PersonaDetectionResult


# --- Keyword Signals ---

TECHNICAL_SIGNALS = [
    # Technical terminology
    r'\b(api|sdk|cli|curl|json|xml|http|https|rest|graphql|grpc|oauth|jwt|webhook)\b',
    r'\b(ssl|tls|certificate|dns|dns-record|cname|a-record|mx-record)\b',
    r'\b(stack trace|error code|exception|null pointer|segfault|memory leak|race condition)\b',
    r'\b(docker|kubernetes|k8s|helm|terraform|ansible|ci[/ ]?cd|devops|mlops)\b',
    r'\b(python|javascript|typescript|java|go|rust|c\+\+|node\.js|react|vue|angular)\b',
    r'\b(database|sql|nosql|mongodb|postgres|redis|elasticsearch|kafka|rabbitmq)\b',
    r'\b(microservice|serverless|lambda|azure function|cloud function|endpoint|payload)\b',
    r'\b(debug|logs|trace|breakpoint|profil|benchmark|latency|throughput|p99|p95)\b',
    r'\b(version|release|changelog|migration|schema|query|index|partition)\b',
    r'\b(dependency|library|package|module|namespace|import|export)\b',
    r'\b(regex|algorithm|data structure|cache|hash|token|encoding|utf-8)\b',
    r'\b(repository|branch|commit|pull request|merge|rebase|revert)\b',
    r'\b(environment variable|env|config|yaml|toml|ini|dotenv)\b',
    r'\b(rate limit|timeout|retry|exponential backoff|circuit breaker)\b',
    # Asking for technical details
    r'\b(how does .* work internally|under the hood|implementation|architecture)\b',
]

EXECUTIVE_SIGNALS = [
    # Business language
    r'\b(roi|kpi|kpis|revenue|cost reduction|savings|budget|quarter|quarterly|fiscal)\b',
    r'\b(sla|slo|sli|compliance|regulatory|audit|governance|risk|mitigation)\b',
    r'\b(stakeholder|board|c-suite|cio|cto|ceo|vp |vice president)\b',
    r'\b(enterprise|customer acquisition|churn|retention|growth|scalability)\b',
    r'\b(contract|renewals|licensing|subscription|tier|plan|pricing)\b',
    r'\b(report|dashboard|analytics|insights|metrics|performance)\b',
    r'\b(business impact|downtime cost|productivity|efficiency|streamline)\b',
    r'\b(vendor|partner|integration|procurement|onboarding|roadmap)\b',
    r'\b(team|department|organization|cross-functional|alignment|strategy)\b',
    r'\b(invest|investment|cost-benefit|return|total cost of ownership|tco)\b',
    r'\b(market|competitive|benchmark|industry standard|best practice)\b',
    r'\b(timeline|deadline|milestone|deliverable|launch|rollout)\b',
    # Formal tone indicators
    r'\b(please provide|kindly|at your earliest|i would like to)\b',
    r'\b(per our|as per|pursuant to|in accordance with)\b',
]

FRUSTRATION_SIGNALS = [
    # Explicit frustration
    r'\b(frustrated|annoyed|angry|furious|livid|upset|outraged|ridiculous|unacceptable)\b',
    r'\b(useless|broken|terrible|horrible|worst|awful|pathetic|garbage)\b',
    r'\b(fed up|sick of|tired of|had enough|done with|give up)\b',
    r'\b(waste of time|wasting my time|not working|keeps failing|still broken)\b',
    r'\b(not helping|doesn\'t help|no help|useless support|terrible service)\b',
    # Repeated contact signals
    r'\b(again|third time|multiple times|keep contacting|repeatedly|nth time)\b',
    r'\b(still not fixed|still having|still broken|still failing|still the same)\b',
    # Urgency signals (only strong frustration markers, not business terms)
    r'\b(immediately|right now|asap|emergency|down|outage)\b',
    r'\b(losing money|lost data|cannot work|blocked|production down)\b',
    # Exclamation usage
    r'!{2,}',  # Multiple exclamations
    r'\b(why|WHY|WTF|WTH|what the|seriously)\b',
]


def _count_matches(text: str, patterns: List[str]) -> Tuple[int, List[str]]:
    """Count pattern matches in text and return matched signals."""
    count = 0
    matched_signals = []
    text_lower = text.lower()
    for pattern in patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        if matches:
            count += len(matches)
            # Store deduplicated match
            for m in set(matches):
                signal_str = m if isinstance(m, str) else str(m)
                if signal_str not in matched_signals:
                    matched_signals.append(signal_str[:50])  # cap length
    return count, matched_signals


def _calculate_frustration_score(message: str, history_messages: List[str]) -> float:
    """Calculate a 0.0-1.0 frustration score."""
    all_text = " ".join([message] + history_messages[-6:])  # last 6 messages
    frust_count, _ = _count_matches(all_text, FRUSTRATION_SIGNALS)

    # All-caps ratio – only count genuine anger-caps, not technical acronyms
    # Exclude common tech/business acronyms to avoid false positives
    KNOWN_ACRONYMS = {
        'API', 'SDK', 'JWT', 'SSL', 'TLS', 'HTTP', 'HTTPS', 'REST',
        'JSON', 'XML', 'YAML', 'TOML', 'SQL', 'AUTH', 'OAUTH', 'SCIM',
        'SLA', 'SLO', 'SLI', 'KPI', 'ROI', 'TCO', 'CEO', 'CTO', 'CIO',
        'SOC', 'GDPR', 'RBAC', 'MFA', 'SSO', 'SAML', 'TOTP', 'NTP',
        'TTL', 'CDN', 'DNS', 'VPN', 'URL', 'UUID', 'HTML', 'CSS',
        'CICD', 'DEVOPS', 'MLOPS', 'ASAP', 'FAQ', 'INFO', 'DOCS',
        'REDIS', 'KAFKA', 'SMTP', 'IMAP', 'LDAP', 'OKTA', 'SAAS',
        'AWS', 'GCP', 'AZURE', 'IAM', 'HMAC', 'SHA256', 'NDJSON',
        'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'ANY', 'NULL', 'TRUE', 'FALSE',
    }
    words = message.split()
    # Only flag caps words 5+ chars that are NOT known acronyms
    caps_words = [
        w for w in words
        if len(w) >= 5 and w.isupper() and re.sub(r'[^A-Z]', '', w) not in KNOWN_ACRONYMS
    ]
    caps_ratio = len(caps_words) / max(len(words), 1)

    # Exclamation count
    exclamation_count = message.count('!')

    raw_score = (frust_count * 0.2) + (caps_ratio * 0.25) + (min(exclamation_count, 5) * 0.08)
    return min(raw_score, 1.0)


def detect_persona(message: str, conversation_history: List[str] = None) -> PersonaDetectionResult:
    """
    Analyze the user's message (and optionally conversation history) to detect persona.

    Args:
        message: The user's latest message.
        conversation_history: List of previous user messages for context.

    Returns:
        PersonaDetectionResult with persona, confidence, signals, and frustration_score.
    """
    if conversation_history is None:
        conversation_history = []

    # Combined text for analysis (weight current message more)
    analysis_text = message + " " + " ".join(conversation_history[-4:])

    tech_count, tech_signals = _count_matches(analysis_text, TECHNICAL_SIGNALS)
    exec_count, exec_signals = _count_matches(analysis_text, EXECUTIVE_SIGNALS)
    frust_count, frust_signals = _count_matches(analysis_text, FRUSTRATION_SIGNALS)

    frustration_score = _calculate_frustration_score(message, conversation_history)

    # Scores – apply multipliers so domain-specific signals beat generic patterns
    scores = {
        PersonaType.TECHNICAL_EXPERT: tech_count * 1.5,
        PersonaType.BUSINESS_EXECUTIVE: exec_count * 1.5,
        PersonaType.FRUSTRATED_USER: frust_count + (frustration_score * 3),
        PersonaType.GENERAL_USER: 1,  # baseline fallback
    }

    # Select dominant persona
    dominant_persona = max(scores, key=lambda k: scores[k])
    dominant_score = scores[dominant_persona]

    # Frustration overrides ONLY if VERY high frustration (explicit anger)
    # and no strong technical/executive signals
    strong_domain = tech_count >= 3 or exec_count >= 3
    if frustration_score >= 0.7 and not strong_domain and dominant_persona != PersonaType.FRUSTRATED_USER:
        dominant_persona = PersonaType.FRUSTRATED_USER
        dominant_score = scores[PersonaType.FRUSTRATED_USER]

    # Confidence: ratio of dominant to total signals
    total_signals = max(sum(scores.values()), 1)
    confidence = min(dominant_score / total_signals, 1.0)
    confidence = max(round(confidence, 2), 0.1)  # floor at 0.1

    # Collect signals
    signals_map = {
        PersonaType.TECHNICAL_EXPERT: tech_signals,
        PersonaType.BUSINESS_EXECUTIVE: exec_signals,
        PersonaType.FRUSTRATED_USER: frust_signals,
        PersonaType.GENERAL_USER: ["No strong signals detected"],
    }
    detected_signals = signals_map[dominant_persona][:8]  # cap at 8

    return PersonaDetectionResult(
        persona=dominant_persona,
        confidence=confidence,
        signals=detected_signals,
        frustration_score=round(frustration_score, 2),
    )
