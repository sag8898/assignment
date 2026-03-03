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
    r'\b(api|restapi|rest[-\s]api|sdk|cli|curl|json|xml|http|https|rest|graphql|grpc|oauth|jwt|webhook)\b',
    r'\b(ssl|tls|certificate|dns|dns-record|cname|a-record|mx-record)\b',
    r'\b(authentication|auth|login|password|mfa|2fa|security|encryption|token)\b',
    r'\b(stack trace|error code|exception|null pointer|segfault|memory leak|race condition)\b',
    r'\b(docker|kubernetes|k8s|helm|terraform|ansible|ci[/ ]?cd|devops|mlops)\b',
    r'\b(python|javascript|typescript|java|go|rust|c\+\+|node\.js|react|vue|angular)\b',
    r'\b(database|sql|nosql|mongodb|postgres|redis|elasticsearch|kafka|rabbitmq)\b',
    r'\b(microservice|serverless|lambda|azure function|cloud function|endpoint|payload)\b',
    r'\b(debug|logs|trace|breakpoint|profiling|latency|throughput|p99|p95)\b',
    r'\b(schema|query|index|partition|sharding|clustering)\b',
    r'\b(dependency|library|package|module|namespace|import|export)\b',
    r'\b(regex|algorithm|data structure|cache|hash|encoding|utf-8)\b',
    r'\b(repository|branch|commit|pull request|merge|rebase|revert|git)\b',
    r'\b(environment variable|env|config|yaml|toml|ini|dotenv)\b',
    r'\b(rate limit|timeout|retry|exponential backoff|circuit breaker)\b',
    # Asking for technical details
    r'\b(how does .* work internally|under the hood|implementation|architecture)\b',
]

EXECUTIVE_SIGNALS = [
    # Business language
    r'\b(roi|kpi|kpis|revenue|cost reduction|savings|budget|quarter|quarterly|fiscal|revenue|profit|loss|margin|p&l|ebitda)\b',
    r'\b(sla|slo|sli|compliance|regulatory|audit|governance|risk|mitigation|iso|soc2|gdpr)\b',
    r'\b(stakeholder|board|c-suite|cio|cto|ceo|vp |vice president|director|manager|leadership)\b',
    r'\b(enterprise|customer acquisition|churn|retention|growth|scalability|market[\s-]?share|expansion)\b',
    r'\b(contract|renewals|licensing|subscription|tier|plan|pricing|billing|invoice|po|purchase order)\b',
    r'\b(sales|deals?|leads?|prospects?|pipeline|forecast|quotes?|proposal|mql|sql|opportunity)\b',
    r'\b(report|dashboard|analytics|insights|metrics|performance|quarterly|strategic|alignment)\b',
    r'\b(business impact|downtime cost|productivity|efficiency|streamline|roi|tco)\b',
    r'\b(vendor|partner|integration|procurement|onboarding|roadmap|strategy|procurement)\b',
    r'\b(market|competitive|benchmark|industry standard|best practice)\b',
    r'\b(timeline|deadline|milestone|deliverable|launch|rollout|budget)\b',
    # Formal tone indicators
    r'\b(please provide|kindly|at your earliest|i would like to|would you mind|appreciate if)\b',
    r'\b(per our|as per|pursuant to|in accordance with|regarding|with respect to)\b',
]

FRUSTRATION_SIGNALS = [
    # Explicit frustration
    r'\b(?:frustrat(?:ed|ing)|annoy(?:ed|ing)|angry|furi(?:ous|ly)|livid|upset|outrag(?:ed|eous)|ridiculous|unacceptable)\b',
    r'\b(?:useless|broken|terrible|horrible|worst|awful|pathetic|garbage|crap|junk)\b',
    r'\b(?:unhappy|disappointed|dissatisfied|complaint|regret|cancel|refund)\b',
    r'\b(?:fed up|sick of|tired of|had enough|done with|give up)\b',
    r'\b(?:waste of time|wasting my time|not working|keeps failing|still broken)\b',
    r'\b(?:not helping|doesn\'t help|no help|useless support|terrible service)\b',
    # Repeated contact signals (only if multiple)
    r'\b(?:third time|multiple times|keep contacting|repeatedly|nth time|again and again)\b',
    r'\b(?:still not fixed|still having|still broken|still failing|still the same)\b',
    # Urgency signals (only strong frustration markers, not business terms)
    r'\b(?:immediately|right now|asap|emergency|down|outage)\b',
    r'\b(?:losing money|lost data|cannot work|blocked|production down)\b',
    # Exclamation usage (only multiple or strong markers)
    r'!{2,}',  # Multiple exclamations
    r'\b(?:WTF|WTH|what the|seriously|are you serious|unbelievable)\b',
]

GENERAL_SIGNALS = [
    # Conversation "reset" words or broad terms
    r'\b(hello|hi|hey|greetings|good morning|good afternoon|good evening)\b',
    r'\b(thanks?|thank you|thx|cool|ok|okay|fine|great|awesome|understand|understood)\b',
    r'\b(how are you|how is it going|what is up|who are you|how do you work)\b',
    r'\b(help|support|questions?|info|information|details)\b',
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

    # 1. Detect signals in CURRENT message (High weight)
    curr_tech_cnt, curr_tech_sig = _count_matches(message, TECHNICAL_SIGNALS)
    curr_exec_cnt, curr_exec_sig = _count_matches(message, EXECUTIVE_SIGNALS)
    curr_frust_cnt, curr_frust_sig = _count_matches(message, FRUSTRATION_SIGNALS)
    curr_gen_cnt, curr_gen_sig = _count_matches(message, GENERAL_SIGNALS)

    # 2. Detect signals in HISTORY (MUCH lower weight to prevent "stickiness")
    history_text = " ".join(conversation_history[-4:])
    hist_tech_cnt, _ = _count_matches(history_text, TECHNICAL_SIGNALS)
    hist_exec_cnt, _ = _count_matches(history_text, EXECUTIVE_SIGNALS)
    hist_frust_cnt, _ = _count_matches(history_text, FRUSTRATION_SIGNALS)
    hist_gen_cnt, _ = _count_matches(history_text, GENERAL_SIGNALS)

    # Combined counts: Current message is weighted 10x more than individual history signals
    tech_count = (curr_tech_cnt * 10.0) + (hist_tech_cnt * 0.5)
    exec_count = (curr_exec_cnt * 10.0) + (hist_exec_cnt * 0.5)
    frust_count = (curr_frust_cnt * 10.0) + (hist_frust_cnt * 0.5)
    gen_count = (curr_gen_cnt * 5.0) + (hist_gen_cnt * 0.5)

    # Combined signals for display
    tech_signals = curr_tech_sig
    exec_signals = curr_exec_sig
    frust_signals = curr_frust_sig

    frustration_score = _calculate_frustration_score(message, conversation_history)

    # Scores – Apply stronger baseline for General User when current message is short or has general intent
    scores = {
        PersonaType.TECHNICAL_EXPERT: tech_count * 2.5,
        PersonaType.BUSINESS_EXECUTIVE: exec_count * 2.5,
        PersonaType.FRUSTRATED_USER: (frust_count * 2.0) + (frustration_score * 4.0),
        PersonaType.GENERAL_USER: 4.0 + (gen_count * 3.0),  # Baseline + general signal boost
    }

    # Select dominant persona
    dominant_persona = max(scores, key=lambda k: scores[k])
    dominant_score = scores[dominant_persona]

    # Frustration overrides ONLY if VERY high frustration
    # AND the current message has frustration signals
    if frustration_score >= 0.75 and curr_frust_cnt >= 1 and dominant_persona != PersonaType.FRUSTRATED_USER:
        dominant_persona = PersonaType.FRUSTRATED_USER
        dominant_score = scores[PersonaType.FRUSTRATED_USER]

    # Confidence calculation
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
