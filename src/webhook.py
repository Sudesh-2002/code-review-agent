from fastapi import FastAPI, Request, HTTPException, Header
from src.agent import CodeReviewAgent
from src.logger import get_logger
import hashlib
import hmac
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
agent = CodeReviewAgent()
logger = get_logger("webhook")

def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify the request is genuinely from GitHub"""
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "").encode()
    expected = "sha256=" + hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

@app.get("/")
async def root():
    logger.info("Health check pinged")
    return {"status": "Code Review Agent is running ✅"}

@app.post("/webhook")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(None),
    x_hub_signature_256: str = Header(None)
):
    payload_bytes = await request.body()

    # Verify signature
    if x_hub_signature_256:
        if not verify_signature(payload_bytes, x_hub_signature_256):
            logger.warning("Webhook rejected — invalid signature")
            raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()

    # Only handle pull_request events
    if x_github_event != "pull_request":
        logger.debug(f"Ignored event: {x_github_event}")
        return {"status": "ignored", "reason": f"Event '{x_github_event}' not handled"}

    action = payload.get("action")

    # Only trigger on opened or new commits pushed
    if action not in ["opened", "synchronize", "reopened"]:
        logger.debug(f"Ignored action: {action}")
        return {"status": "ignored", "reason": f"Action '{action}' not handled"}

    # Extract PR details
    repo_name = payload["repository"]["full_name"]
    pr_number = payload["pull_request"]["number"]
    pr_title  = payload["pull_request"]["title"]

    logger.info(f"Webhook received — {repo_name} PR #{pr_number} '{pr_title}' [{action}]")

    # Run review in background so webhook returns instantly
    asyncio.create_task(run_review(repo_name, pr_number))

    return {
        "status": "accepted",
        "message": f"Review started for PR #{pr_number}"
    }

async def run_review(repo_name: str, pr_number: int):
    """Run the review in background"""
    try:
        agent.review_pr(repo_name, pr_number)
    except Exception as e:
        logger.error(f"Review failed for {repo_name} PR #{pr_number} — {e}")