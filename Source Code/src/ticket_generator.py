"""
ticket_generator.py
Generates realistic mock enterprise AI support tickets and saves them as JSON.
Simulates the kind of tickets an OpenAI / AI platform support team would receive.
"""

import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from faker import Faker

fake = Faker()

# ── Ticket templates by category ─────────────────────────────────────────────

TICKET_TEMPLATES = {
    "api": [
        {
            "subject": "API returning 500 errors on chat completions endpoint",
            "body": (
                "Hi support, we've been getting intermittent 500 Internal Server Errors "
                "from the /v1/chat/completions endpoint since approximately 14:30 UTC today. "
                "This is affecting ~30% of our requests. Our API key is valid and we haven't "
                "changed any configuration. Request ID from one failed call: {req_id}. "
                "Please advise urgently — this is impacting production."
            ),
            "priority": "critical",
        },
        {
            "subject": "Rate limit errors despite being on paid plan",
            "body": (
                "We are consistently hitting 429 rate limit errors even though our usage "
                "is well below the documented TPM limits for our tier. Account ID: {account_id}. "
                "This started after we upgraded our plan last week. Is there a propagation delay "
                "for limit increases? JSON error: {{\"error\": {{\"type\": \"rate_limit_exceeded\", "
                "\"code\": \"rate_limit_exceeded\"}}}}."
            ),
            "priority": "high",
        },
        {
            "subject": "API response latency spike — P99 went from 800ms to 8s",
            "body": (
                "Starting around 09:00 UTC our P99 latency for the completions API jumped "
                "from ~800ms to over 8 seconds. P50 looks normal. We're using gpt-4o with "
                "max_tokens=1000. Is there a known degradation? We've checked our network "
                "and it's not on our side. Dashboard shows no status page incidents."
            ),
            "priority": "high",
        },
        {
            "subject": "Streaming API cutting off responses mid-sentence",
            "body": (
                "Our streaming implementation using SSE is receiving partial responses — "
                "the stream stops mid-sentence and sends a [DONE] token early. This happens "
                "on roughly 1 in 20 requests. We're using the Python SDK v1.12.0. "
                "Have you seen this issue? Could it be related to our max_tokens setting?"
            ),
            "priority": "medium",
        },
        {
            "subject": "Embeddings endpoint returning inconsistent vector dimensions",
            "body": (
                "We're calling the embeddings endpoint and occasionally getting vectors "
                "with different dimensions than expected. Our downstream vector DB rejects "
                "these. Model: text-embedding-3-small. Expected 1536 dimensions, "
                "occasionally getting 512. Is this a known issue?"
            ),
            "priority": "medium",
        },
    ],
    "billing": [
        {
            "subject": "Charged twice for the same billing period",
            "body": (
                "I see two identical charges of ${amount} on my credit card for the month "
                "of {month}. Invoice IDs: INV-{inv1} and INV-{inv2}. Please investigate "
                "and issue a refund for the duplicate charge. My account email is {email}."
            ),
            "priority": "high",
        },
        {
            "subject": "Usage spike I don't recognize on my invoice",
            "body": (
                "My invoice this month is 10x higher than usual — ${amount} vs the normal "
                "~${normal_amount}. I haven't changed my application code or increased traffic. "
                "Can you provide a detailed breakdown of which API calls drove this usage? "
                "Specifically the token counts per model per day for the last 30 days."
            ),
            "priority": "high",
        },
        {
            "subject": "Free tier credits not applied to invoice",
            "body": (
                "I signed up under a promotion that included ${credit_amount} in API credits. "
                "My latest invoice doesn't reflect this credit. Account created: {date}. "
                "Promo code used: {promo}. Please apply the credits to my account."
            ),
            "priority": "medium",
        },
        {
            "subject": "Unable to update payment method — card keeps declining",
            "body": (
                "I'm trying to update my billing card but keep getting a generic decline error "
                "despite the card being valid and having sufficient funds. I've tried 3 different "
                "cards. My account is at risk of suspension. Browser: Chrome 122, no VPN."
            ),
            "priority": "high",
        },
    ],
    "account": [
        {
            "subject": "Cannot access organization after SSO migration",
            "body": (
                "Our company migrated to SSO last week and several team members can no longer "
                "access the organization. They're getting 'Organization not found' errors after "
                "authentication. Org ID: {org_id}. Affected users: {user_count}. "
                "SSO provider: Okta. The SSO itself works — the issue is post-authentication."
            ),
            "priority": "critical",
        },
        {
            "subject": "API key mysteriously invalidated — need urgent replacement",
            "body": (
                "Our production API key stopped working at approximately 02:00 UTC. "
                "All requests now return 401 Unauthorized. We did not rotate the key. "
                "No one on our team revoked it. Is there any way to see the key activity log? "
                "We need a replacement key urgently as this is a production system."
            ),
            "priority": "critical",
        },
        {
            "subject": "Team member added to wrong organization",
            "body": (
                "I accidentally added a contractor to our main organization instead of the "
                "sandbox org. They now have visibility into production API keys and usage data. "
                "Please help me remove them immediately and confirm what data they may have accessed."
            ),
            "priority": "high",
        },
        {
            "subject": "Request to increase API rate limits for enterprise use case",
            "body": (
                "We're building a high-throughput document processing pipeline and need "
                "increased TPM limits for gpt-4o. Current limit: 800,000 TPM. "
                "Requested: 5,000,000 TPM. We have a business justification document available. "
                "Who should we speak to about an enterprise agreement?"
            ),
            "priority": "medium",
        },
    ],
    "safety": [
        {
            "subject": "Model producing outputs that violate our content policy",
            "body": (
                "We're building a children's education platform and despite our system prompt "
                "restrictions, the model occasionally produces age-inappropriate content. "
                "I can provide specific examples with the exact prompts and outputs. "
                "We need guidance on additional safeguards. This is a legal and compliance issue."
            ),
            "priority": "critical",
        },
        {
            "subject": "Possible prompt injection attack on our application",
            "body": (
                "We believe a user is attempting prompt injection attacks on our application — "
                "trying to override our system prompt instructions. We've logged several attempts "
                "where user messages contain phrases like 'ignore previous instructions'. "
                "What mitigations do you recommend? Are there API-level safeguards available?"
            ),
            "priority": "high",
        },
        {
            "subject": "Model hallucinating citations in medical context",
            "body": (
                "Our medical information platform is seeing the model generate plausible-looking "
                "but entirely fabricated journal citations. Users are relying on these as real "
                "sources. We need guidance on how to reduce hallucination rates for "
                "citation-heavy prompts. Is RAG the recommended approach?"
            ),
            "priority": "high",
        },
    ],
    "other": [
        {
            "subject": "Documentation unclear on context window management",
            "body": (
                "The documentation for managing long conversations is unclear about what happens "
                "when we exceed the context window. Does the API automatically truncate? "
                "Which end gets truncated — the beginning or end? Is there an error thrown? "
                "We're building a long-running agent and need to handle this correctly."
            ),
            "priority": "low",
        },
        {
            "subject": "Feature request: webhook notifications for long-running jobs",
            "body": (
                "For our batch processing use case, we'd love webhook support so we can "
                "receive a callback when async jobs complete rather than polling. "
                "Is this on the roadmap? In the meantime, what's the recommended polling interval "
                "to avoid rate limiting?"
            ),
            "priority": "low",
        },
        {
            "subject": "Request for SLA documentation for enterprise compliance audit",
            "body": (
                "Our compliance team requires formal SLA documentation including uptime guarantees, "
                "incident response times, and data retention policies. We're undergoing a SOC2 "
                "audit and need these documents by end of month. Who should I contact?"
            ),
            "priority": "medium",
        },
    ],
}


def _fill_template(template: dict) -> dict:
    """Fill template placeholders with fake data."""
    body = template["body"].format(
        req_id=str(uuid.uuid4())[:8].upper(),
        account_id=f"acc_{uuid.uuid4().hex[:10]}",
        amount=random.randint(50, 500),
        normal_amount=random.randint(20, 80),
        month=fake.month_name(),
        inv1=uuid.uuid4().hex[:8].upper(),
        inv2=uuid.uuid4().hex[:8].upper(),
        email=fake.email(),
        credit_amount=random.choice([25, 50, 100]),
        date=fake.date_this_year().isoformat(),
        promo=f"PROMO-{uuid.uuid4().hex[:6].upper()}",
        org_id=f"org_{uuid.uuid4().hex[:10]}",
        user_count=random.randint(2, 15),
    )
    return {
        "subject": template["subject"],
        "body": body,
        "priority": template["priority"],
    }


def generate_ticket(days_back: int = 30) -> dict:
    """Generate a single realistic support ticket."""
    category = random.choice(list(TICKET_TEMPLATES.keys()))
    template = random.choice(TICKET_TEMPLATES[category])
    filled = _fill_template(template)

    created_at = datetime.now(timezone.utc) - timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )

    return {
        "ticket_id": f"TKT-{uuid.uuid4().hex[:8].upper()}",
        "created_at": created_at.isoformat(),
        "customer": fake.company(),
        "subject": filled["subject"],
        "body": filled["body"],
        "priority": filled["priority"],
        "status": random.choices(
            ["open", "in_progress", "resolved"],
            weights=[0.4, 0.2, 0.4]
        )[0],
        "category": category,  # ground truth — will be overwritten by AI triage
    }


def generate_batch(n: int = 50, days_back: int = 30) -> list[dict]:
    """Generate a batch of tickets."""
    return [generate_ticket(days_back) for _ in range(n)]


def save_tickets_to_json(tickets: list[dict], filepath: str):
    """Save tickets to a JSON file."""
    with open(filepath, "w") as f:
        json.dump(tickets, f, indent=2)
    print(f"[generator] Saved {len(tickets)} tickets to {filepath}")


def load_tickets_from_json(filepath: str) -> list[dict]:
    """Load tickets from a JSON file."""
    with open(filepath) as f:
        return json.load(f)


if __name__ == "__main__":
    import os
    os.makedirs("data", exist_ok=True)
    tickets = generate_batch(n=50)
    save_tickets_to_json(tickets, "data/tickets.json")
    print(f"Sample ticket:\n{json.dumps(tickets[0], indent=2)}")
