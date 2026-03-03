"""
Knowledge Base Service
Provides a curated knowledge base with articles tagged by persona, category, and topic.
Supports semantic search via keyword matching.
"""
import re
from typing import List, Optional
from models.schemas import PersonaType, KnowledgeBaseResult

# ─────────────────────────────────────────────
# Knowledge Base Articles
# ─────────────────────────────────────────────

KNOWLEDGE_BASE = [
    # ─── API & Integration ───
    {
        "article_id": "KB-001",
        "title": "REST API Authentication Guide",
        "category": "API & Integration",
        "tags": ["api", "authentication", "oauth", "jwt", "token", "bearer", "curl", "request"],
        "personas": [PersonaType.TECHNICAL_EXPERT, PersonaType.GENERAL_USER],
        "content": {
            PersonaType.TECHNICAL_EXPERT: (
                "**API Authentication – Technical Reference**\n\n"
                "All API endpoints require Bearer token authentication via OAuth 2.0 (RFC 6749). "
                "Obtain an access token using client credentials flow:\n\n"
                "```\nPOST /oauth/token\nContent-Type: application/x-www-form-urlencoded\n\n"
                "grant_type=client_credentials&client_id=<id>&client_secret=<secret>\n```\n\n"
                "Tokens expire after **3600 seconds (1 hour)**. Implement token refresh with exponential backoff. "
                "The API enforces rate limits: 100 req/min per client. Use the `Retry-After` header on 429 responses. "
                "JWT payload includes `sub`, `iat`, `exp`, and `scopes` claims.\n\n"
                "**Error Codes:** 401 (invalid token), 403 (insufficient scope), 429 (rate limited)."
            ),
            PersonaType.GENERAL_USER: (
                "**How to Connect to Our API**\n\n"
                "To use our API, you'll need an API key (like a password for your app). Here's how to get started:\n\n"
                "1. Go to **Settings → Developer → API Keys** and click 'Generate New Key'.\n"
                "2. Copy your key and keep it safe – don't share it!\n"
                "3. Add it to your requests as a header: `Authorization: Bearer YOUR_KEY`\n\n"
                "Your key lasts for 1 hour, then you'll need a new one. If you see a '401 error', "
                "it usually means your key has expired. Just generate a new one!"
            ),
            PersonaType.FRUSTRATED_USER: (
                "I understand it's frustrating when API connections don't work – let's fix this quickly! 🔧\n\n"
                "**Most common causes of API errors:**\n"
                "✅ Expired token → Generate a new API key in Settings → Developer → API Keys\n"
                "✅ Wrong header format → Make sure it's: `Authorization: Bearer YOUR_KEY`\n"
                "✅ Rate limit hit → Wait 60 seconds and try again\n\n"
                "If none of these work, I'll escalate this to our technical team right away."
            ),
            PersonaType.BUSINESS_EXECUTIVE: (
                "**API Integration Overview for Business Leaders**\n\n"
                "Our API uses industry-standard OAuth 2.0 authentication, ensuring enterprise-grade security "
                "compliant with SOC 2 Type II and ISO 27001. Key business considerations:\n\n"
                "- **Uptime SLA:** 99.9% availability guaranteed\n"
                "- **Rate Limits:** Up to 100,000 requests/day on Enterprise plans\n"
                "- **Security:** All tokens expire after 1 hour, minimizing breach risk\n"
                "- **Support:** Dedicated integration support team available\n\n"
                "For volume licensing or custom rate limits, contact your account manager."
            ),
        }
    },
    {
        "article_id": "KB-002",
        "title": "Webhook Configuration & Event Subscriptions",
        "category": "API & Integration",
        "tags": ["webhook", "event", "notification", "callback", "http", "endpoint", "payload", "signature"],
        "personas": [PersonaType.TECHNICAL_EXPERT],
        "content": {
            PersonaType.TECHNICAL_EXPERT: (
                "**Webhooks – Configuration & Verification**\n\n"
                "Webhooks deliver real-time event notifications via HTTP POST to your endpoint. "
                "Supported events: `order.created`, `payment.completed`, `user.signup`, `subscription.renewed`.\n\n"
                "**Signature Verification (HMAC-SHA256):**\n"
                "```python\nimport hmac, hashlib\n\ndef verify(payload, signature, secret):\n"
                "    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()\n"
                "    return hmac.compare_digest(expected, signature)\n```\n\n"
                "**Retry policy:** 3 retries with exponential backoff (1s, 5s, 30s). "
                "Your endpoint must return 2xx within 10 seconds or the delivery is marked failed. "
                "Failed deliveries are retried for up to 24 hours.\n\n"
                "Configure webhooks via: `POST /api/v2/webhooks` with `url`, `events[]`, and `secret` fields."
            ),
            PersonaType.GENERAL_USER: (
                "**What are Webhooks?**\n\n"
                "Webhooks let our system notify your app instantly when something happens "
                "(like a new order or payment). Think of it like a doorbell – we ring it, and your app answers!\n\n"
                "To set one up, go to **Settings → Integrations → Webhooks** and add your URL."
            ),
        }
    },

    # ─── Billing & Subscriptions ───
    {
        "article_id": "KB-003",
        "title": "Billing & Subscription Management",
        "category": "Billing",
        "tags": ["billing", "payment", "invoice", "subscription", "plan", "upgrade", "downgrade", "refund", "charge"],
        "personas": [PersonaType.BUSINESS_EXECUTIVE, PersonaType.GENERAL_USER, PersonaType.FRUSTRATED_USER],
        "content": {
            PersonaType.BUSINESS_EXECUTIVE: (
                "**Enterprise Subscription & Billing Overview**\n\n"
                "Your Enterprise subscription provides:\n"
                "- **Flexible billing cycles:** Monthly or annual (15% savings on annual)\n"
                "- **Centralized invoicing:** Consolidated invoices with PO number support\n"
                "- **Usage analytics:** Real-time spend dashboards in the Admin Portal\n"
                "- **Volume discounts:** Available for 50+ seat licenses\n\n"
                "**Key contacts:**\n"
                "- Billing inquiries: billing@company.com (24h SLA)\n"
                "- Contract renewals: Your dedicated Account Executive\n"
                "- Emergency billing: Priority line +1-800-XXX-XXXX\n\n"
                "Tax compliance: We support VAT, GST, and US sales tax automation."
            ),
            PersonaType.GENERAL_USER: (
                "**Managing Your Subscription**\n\n"
                "You can manage your subscription anytime in **Settings → Billing**:\n\n"
                "- **View invoices:** Download PDF invoices for any billing period\n"
                "- **Update payment method:** Add/remove credit cards or bank accounts\n"
                "- **Upgrade/Downgrade:** Change your plan (takes effect next billing cycle)\n"
                "- **Cancel:** Cancel anytime – no cancellation fees\n\n"
                "Billing happens on the same date each month. Need help? Chat with us below!"
            ),
            PersonaType.FRUSTRATED_USER: (
                "I completely understand billing issues are stressful – let's sort this out immediately! 💳\n\n"
                "**Quick fixes for common billing problems:**\n"
                "✅ Unexpected charge → Check Settings → Billing → Invoice History for details\n"
                "✅ Payment failed → Update card in Settings → Billing → Payment Methods\n"
                "✅ Overcharged → Our billing team can issue a refund within 24 hours\n\n"
                "**I'm connecting you to our billing specialist right now.** "
                "You won't have to explain this again – I'm sending them your full conversation history."
            ),
        }
    },
    {
        "article_id": "KB-004",
        "title": "Refund & Cancellation Policy",
        "category": "Billing",
        "tags": ["refund", "cancel", "cancellation", "money back", "charge", "dispute"],
        "personas": [PersonaType.GENERAL_USER, PersonaType.FRUSTRATED_USER, PersonaType.BUSINESS_EXECUTIVE],
        "content": {
            PersonaType.GENERAL_USER: (
                "**Refund & Cancellation Policy**\n\n"
                "We offer a **30-day money-back guarantee** on all plans. If you're not satisfied, "
                "contact us within 30 days of purchase for a full refund – no questions asked.\n\n"
                "- Monthly plans: Cancel anytime; access continues until period end\n"
                "- Annual plans: Pro-rated refund available within 30 days\n\n"
                "To request a refund: Settings → Billing → Request Refund, or email billing@company.com"
            ),
            PersonaType.FRUSTRATED_USER: (
                "You deserve your money back, and we'll make this right! 🙏\n\n"
                "**Refund guarantee:** We have a 30-day no-questions-asked refund policy.\n\n"
                "I'm escalating your refund request right now as HIGH PRIORITY. "
                "Our billing team will process it within 2-3 business days and you'll receive "
                "a confirmation email. Is this billing email correct: [your registered email]?"
            ),
            PersonaType.BUSINESS_EXECUTIVE: (
                "**Enterprise Refund & SLA Credits**\n\n"
                "Enterprise accounts are eligible for:\n"
                "- **SLA credits** for downtime exceeding 99.9% uptime guarantee\n"
                "- **Pro-rated refunds** for annual contracts cancelled within 30 days\n"
                "- **Dispute resolution** within 5 business days via your Account Executive\n\n"
                "Credit notes are issued against future invoices or as direct bank transfers per your preference."
            ),
        }
    },

    # ─── Technical Troubleshooting ───
    {
        "article_id": "KB-005",
        "title": "Performance Issues & Latency Troubleshooting",
        "category": "Technical",
        "tags": ["performance", "slow", "latency", "timeout", "p99", "p95", "cache", "debug", "profiling", "response time"],
        "personas": [PersonaType.TECHNICAL_EXPERT, PersonaType.FRUSTRATED_USER],
        "content": {
            PersonaType.TECHNICAL_EXPERT: (
                "**Performance Diagnostics Guide**\n\n"
                "**Step 1 – Baseline measurement:**\n"
                "```bash\ncurl -w '@curl-format.txt' -o /dev/null -s https://api.company.com/health\n```\n\n"
                "**Common bottlenecks:**\n"
                "1. **N+1 queries** – Use `?include=relations` to eager-load related resources\n"
                "2. **Missing indexes** – Check slow query logs; add composite indexes on filter+sort columns\n"
                "3. **Cold starts** – For Lambda/serverless, implement connection pooling via RDS Proxy\n"
                "4. **Cache misses** – Verify Redis TTL and cache key strategies\n"
                "5. **Rate limiting** – Check `X-RateLimit-Remaining` header; implement client-side throttling\n\n"
                "**Observability stack:** We expose OpenTelemetry-compatible traces. "
                "Enable via: `X-Trace-Enabled: true` header. Traces available in your Grafana dashboard.\n\n"
                "P99 latency targets: <200ms (read), <500ms (write). Current status: status.company.com"
            ),
            PersonaType.FRUSTRATED_USER: (
                "I know slow performance is incredibly frustrating, especially when you're trying to get work done. "
                "Let's fix this now! ⚡\n\n"
                "**Quick checks (takes 2 minutes):**\n"
                "1. Check our status page: **status.company.com** – is there an ongoing incident?\n"
                "2. Try a different browser or clear your cache (Ctrl+Shift+Delete)\n"
                "3. Check your internet connection speed\n\n"
                "If the problem persists, I'm escalating this to our performance team with your details. "
                "You'll get a personal callback within 30 minutes."
            ),
        }
    },
    {
        "article_id": "KB-006",
        "title": "Error Codes Reference Guide",
        "category": "Technical",
        "tags": ["error", "error code", "4xx", "5xx", "400", "401", "403", "404", "500", "503", "exception", "stack trace"],
        "personas": [PersonaType.TECHNICAL_EXPERT],
        "content": {
            PersonaType.TECHNICAL_EXPERT: (
                "**HTTP Error Code Reference**\n\n"
                "| Code | Meaning | Resolution |\n"
                "|------|---------|------------|\n"
                "| 400  | Bad Request – malformed JSON/missing fields | Validate payload against OpenAPI spec |\n"
                "| 401  | Unauthorized – invalid/expired token | Refresh OAuth token |\n"
                "| 403  | Forbidden – insufficient scope | Request additional OAuth scopes |\n"
                "| 404  | Not Found – resource doesn't exist | Verify resource ID and endpoint URL |\n"
                "| 409  | Conflict – duplicate resource | Check idempotency key or use PATCH |\n"
                "| 422  | Unprocessable Entity – validation failed | Check `errors[]` array in response body |\n"
                "| 429  | Too Many Requests – rate limited | Respect `Retry-After` header |\n"
                "| 500  | Internal Server Error | Retry with backoff; contact support with `X-Request-Id` |\n"
                "| 503  | Service Unavailable – maintenance | Check status.company.com |\n\n"
                "All errors include `request_id`, `code`, `message`, and `details` in the JSON response body."
            ),
            PersonaType.GENERAL_USER: (
                "**Understanding Error Messages**\n\n"
                "If you see an error, here's what it means:\n"
                "- **'Not found' (404):** The page or item doesn't exist\n"
                "- **'Access denied' (403):** You don't have permission – check with your admin\n"
                "- **'Something went wrong' (500):** A temporary server issue – try again in a few minutes\n\n"
                "Still stuck? Copy the error code and paste it in this chat – I'll help right away!"
            ),
        }
    },

    # ─── Account & Access ───
    {
        "article_id": "KB-007",
        "title": "Account Access & Password Reset",
        "category": "Account",
        "tags": ["password", "reset", "login", "access", "locked", "2fa", "mfa", "sso", "account", "sign in"],
        "personas": [PersonaType.GENERAL_USER, PersonaType.FRUSTRATED_USER, PersonaType.TECHNICAL_EXPERT],
        "content": {
            PersonaType.GENERAL_USER: (
                "**Can't Log In? Here's How to Fix It**\n\n"
                "**Password reset (easiest fix):**\n"
                "1. Go to the login page and click **'Forgot Password'**\n"
                "2. Enter your email address\n"
                "3. Check your inbox for a reset link (expires in 15 minutes)\n"
                "4. Create a new password\n\n"
                "**Account locked?** After 5 failed attempts, your account locks for 30 minutes. "
                "You can unlock it immediately via the email we send, or wait 30 minutes.\n\n"
                "**Still can't get in?** Contact support with your username and we'll verify your identity."
            ),
            PersonaType.FRUSTRATED_USER: (
                "Being locked out of your account is so frustrating – I'll get you back in right away! 🔑\n\n"
                "**Fastest solution:**\n"
                "1. Click **'Forgot Password'** on the login page\n"
                "2. Check BOTH your inbox and spam folder for the reset email\n"
                "3. The link expires in 15 minutes – use it right away\n\n"
                "If the email isn't arriving, tell me your registered email address "
                "(in the chat) and I'll manually trigger a reset and stay with you until you're in."
            ),
            PersonaType.TECHNICAL_EXPERT: (
                "**Authentication Troubleshooting**\n\n"
                "**SSO issues:** Verify SAML assertions include `email` and `sub` attributes. "
                "Check IdP metadata is current (re-import if certificate rotated).\n\n"
                "**MFA/TOTP:** Ensure device time is NTP-synchronized (TOTP is time-sensitive ±30s).\n\n"
                "**Programmatic access:** Use service accounts with API keys, not user accounts. "
                "Service accounts aren't affected by MFA or session policies.\n\n"
                "**Token introspection:** `POST /oauth/introspect` returns token metadata including scopes and expiry."
            ),
        }
    },
    {
        "article_id": "KB-008",
        "title": "Team & User Management",
        "category": "Account",
        "tags": ["team", "user", "invite", "role", "permission", "admin", "member", "remove", "access control", "rbac"],
        "personas": [PersonaType.BUSINESS_EXECUTIVE, PersonaType.TECHNICAL_EXPERT, PersonaType.GENERAL_USER],
        "content": {
            PersonaType.BUSINESS_EXECUTIVE: (
                "**Enterprise User & Access Management**\n\n"
                "Our RBAC system provides granular access control aligned with enterprise governance:\n\n"
                "**Roles:** Owner → Admin → Manager → Member → Viewer (5-tier hierarchy)\n"
                "**Features:**\n"
                "- Bulk user provisioning via SCIM 2.0 (integrates with Okta, Azure AD, OneLogin)\n"
                "- Audit logs with 12-month retention (SOC 2 compliant)\n"
                "- Department-level access policies\n"
                "- SSO enforcement to ensure only company accounts can access\n\n"
                "Contact your Account Executive to enable automated provisioning."
            ),
            PersonaType.TECHNICAL_EXPERT: (
                "**User Provisioning & SCIM Integration**\n\n"
                "SCIM 2.0 endpoint: `https://api.company.com/scim/v2`\n"
                "Supports: Users, Groups, and EnterpriseUser extension.\n\n"
                "**Okta integration:** Use our Okta app from the Okta Integration Network. "
                "Map `email` → `userName`, `department` → `groups`.\n\n"
                "**Manual API:** `POST /api/v2/users` with `email`, `role`, `groups[]`. "
                "Bulk import via CSV: `POST /api/v2/users/bulk` (max 1000/request).\n\n"
                "Roles: `owner`, `admin`, `manager`, `member`, `viewer`. "
                "Permissions are additive; higher roles inherit lower-role permissions."
            ),
        }
    },

    # ─── Product Features ───
    {
        "article_id": "KB-009",
        "title": "Getting Started – Quick Start Guide",
        "category": "Getting Started",
        "tags": ["getting started", "setup", "onboarding", "new user", "tutorial", "first steps", "how to", "begin"],
        "personas": [PersonaType.GENERAL_USER, PersonaType.BUSINESS_EXECUTIVE],
        "content": {
            PersonaType.GENERAL_USER: (
                "**Welcome! Let's Get You Started 🚀**\n\n"
                "**Step 1:** Complete your profile in **Settings → Profile**\n"
                "**Step 2:** Connect your first integration in **Settings → Integrations**\n"
                "**Step 3:** Invite your team via **Settings → Team → Invite Members**\n"
                "**Step 4:** Set up your first project in **Projects → New Project**\n\n"
                "Need help at any step? Our onboarding wizard is available in the top menu, "
                "or just ask me anything here!"
            ),
            PersonaType.BUSINESS_EXECUTIVE: (
                "**Enterprise Onboarding Overview**\n\n"
                "Your dedicated Customer Success Manager will guide your team through a structured onboarding:\n\n"
                "**Week 1:** Environment setup, SSO configuration, admin training\n"
                "**Week 2:** Department rollout, integration setup, data migration\n"
                "**Week 3:** Team training, workflow configuration, KPI baseline\n"
                "**Week 4:** Go-live, performance review, optimization planning\n\n"
                "**Success metrics:** We track adoption rate, time-to-value, and ROI monthly. "
                "Your first business review is scheduled 30 days post-launch."
            ),
        }
    },
    {
        "article_id": "KB-010",
        "title": "Data Export & Backup",
        "category": "Data Management",
        "tags": ["export", "data", "backup", "download", "csv", "json", "gdpr", "data portability", "migration"],
        "personas": [PersonaType.TECHNICAL_EXPERT, PersonaType.BUSINESS_EXECUTIVE, PersonaType.GENERAL_USER],
        "content": {
            PersonaType.TECHNICAL_EXPERT: (
                "**Data Export API Reference**\n\n"
                "Async export endpoint: `POST /api/v2/exports`\n"
                "Payload: `{\"format\": \"json|csv|parquet\", \"resources\": [\"orders\",\"users\",\"events\"], "
                "\"date_from\": \"ISO8601\", \"date_to\": \"ISO8601\"}`\n\n"
                "Returns `export_id`. Poll `GET /api/v2/exports/{export_id}` for status. "
                "Completed exports are available for 72 hours via pre-signed S3 URL.\n\n"
                "**Streaming for large datasets:** Use `Accept: application/x-ndjson` for streaming JSON Lines. "
                "Max export size: 10GB. For larger datasets, use date-range pagination."
            ),
            PersonaType.BUSINESS_EXECUTIVE: (
                "**Data Portability & Compliance**\n\n"
                "We are committed to your data sovereignty:\n"
                "- **GDPR Article 20 compliant** data portability\n"
                "- Full data export available in CSV, JSON, or Excel formats\n"
                "- Data retention: configurable from 30 days to 7 years (HIPAA/FINRA options)\n"
                "- Automated backups with 99.999% durability (cross-region redundancy)\n"
                "- **Right to erasure:** Full account and data deletion within 30 days of request\n\n"
                "Export your full dataset anytime from **Admin → Data Management → Export**."
            ),
            PersonaType.GENERAL_USER: (
                "**Downloading Your Data**\n\n"
                "You can download all your data anytime:\n\n"
                "1. Go to **Settings → Privacy → Download My Data**\n"
                "2. Choose what to export (everything, or specific sections)\n"
                "3. Click **'Request Export'**\n"
                "4. You'll get an email with a download link within 1 hour\n\n"
                "The file will be in a standard format you can open with Excel or Google Sheets."
            ),
        }
    },
]


# ─────────────────────────────────────────────
# Search Engine
# ─────────────────────────────────────────────

def _calculate_relevance(query: str, article: dict) -> float:
    """Calculate relevance score using keyword matching."""
    query_words = set(re.findall(r'\b\w+\b', query.lower()))
    query_str = query.lower()
    score = 0.0

    # Tag matching (high weight)
    for tag in article["tags"]:
        if tag in query_str:
            score += 0.4
        elif any(word in tag for word in query_words if len(word) > 3):
            score += 0.15

    # Title matching
    title_words = set(re.findall(r'\b\w+\b', article["title"].lower()))
    overlap = query_words & title_words
    score += len(overlap) * 0.25

    # Category matching
    if any(word in article["category"].lower() for word in query_words):
        score += 0.3

    return min(round(score, 3), 1.0)


def search_knowledge_base(
    query: str,
    persona: Optional[PersonaType] = None,
    category: Optional[str] = None,
    limit: int = 3,
) -> List[KnowledgeBaseResult]:
    """
    Search the knowledge base and return persona-adapted articles.
    """
    results = []

    for article in KNOWLEDGE_BASE:
        relevance = _calculate_relevance(query, article)
        if relevance < 0.05:
            continue

        # Category filter
        if category and category.lower() not in article["category"].lower():
            continue

        # Determine best content version for the persona
        content_map = article["content"]
        if persona and persona in content_map:
            content = content_map[persona]
        elif PersonaType.GENERAL_USER in content_map:
            content = content_map[PersonaType.GENERAL_USER]
        else:
            content = next(iter(content_map.values()))

        results.append(KnowledgeBaseResult(
            article_id=article["article_id"],
            title=article["title"],
            content=content,
            category=article["category"],
            relevance_score=relevance,
            tags=article["tags"][:6],
        ))

    # Sort by relevance, apply limit
    results.sort(key=lambda x: x.relevance_score, reverse=True)
    return results[:limit]
