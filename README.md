# 🤖 AI Code Review Agent

> An autonomous AI agent that reviews GitHub Pull Requests instantly — detecting bugs, security vulnerabilities, and code quality issues — and posts structured feedback as GitHub comments.

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/LLM-LLaMA_3.3_70B-orange)](https://groq.com)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

---

## ✨ What It Does

Every time a Pull Request is **opened, updated, or reopened** on your GitHub repository, this agent:

1. 📥 Receives the event via a GitHub Webhook
2. 🔍 Fetches the diff for every changed file
3. 🧠 Sends each file to an LLM (LLaMA 3.3 70B via Groq) for analysis
4. 🛡️ Applies content-aware, evidence-based prompt rules to prevent false positives
5. 💬 Posts a structured, actionable review comment directly on the PR

---

## 🖼️ Example Output

```
## 🤖 AI Code Review

### What this PR does
Adds retry logic and caching to the CodeReviewAgent class.

### Risk Level
🟠 MEDIUM — Unhandled exception on cache write failure.

### Issues Found
| Severity | File         | Issue                    | Evidence                        |
|----------|--------------|--------------------------|---------------------------------|
| 🟠       | src/cache.py | No error handling on I/O | `with open(CACHE_FILE, "w") as f:` |

### File Verdicts
| File          | Score | Verdict      |
|---------------|-------|--------------|
| src/agent.py  | 9/10  | APPROVE ✅   |
| src/cache.py  | 7/10  | NEEDS REVIEW 👀 |

### Overall Verdict
**NEEDS REVIEW 👀**
```

---

## 🏗️ Architecture

```
GitHub PR Event
      │
      ▼
 POST /webhook  (FastAPI — src/webhook.py)
      │ HMAC-SHA256 signature verified
      │
      ▼
 CodeReviewAgent  (src/agent.py)
      │
      ├── Cache check (SHA-256 keyed JSON)
      │       └── HIT → return cached review (no LLM call)
      │
      ├── _derive_hints()  ← content-aware, no SQL hint unless SQL is in the diff
      │
      ├── build_review_prompt()  ← evidence-required, truncation-aware
      │
      ├── Groq API  (llama-3.3-70b-versatile)
      │       └── call_with_retry()  ← exponential backoff on rate limits
      │
      └── GitHub Comment  (PyGithub)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| API Server | FastAPI + Uvicorn |
| LLM | LLaMA 3.3 70B via Groq (free tier) |
| GitHub Integration | PyGithub |
| Caching | SHA-256 keyed JSON file |
| Retry Logic | Custom exponential backoff |
| Deployment | Render (render.yaml included) |

---

## ⚙️ Setup

### 1. Clone the repo
```bash
git clone https://github.com/Sudesh-2002/code-review-agent.git
cd code-review-agent
```

### 2. Create a virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_WEBHOOK_SECRET=your_webhook_secret
```

| Variable | Where to get it |
|----------|----------------|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) — free |
| `GITHUB_TOKEN` | GitHub → Settings → Developer Settings → Personal Access Tokens (needs `repo` scope) |
| `GITHUB_WEBHOOK_SECRET` | Any random string — you'll paste the same value into the GitHub Webhook config |

### 5. Run locally
```bash
python main.py
```
The server starts at `http://localhost:8000`. Visit `/` for a health check.

### 6. Expose with ngrok (for local testing)
```bash
ngrok http 8000
```
Copy the `https://xxxx.ngrok.io` URL — you'll use it as the webhook URL.

### 7. Add GitHub Webhook
Go to your target repo → **Settings → Webhooks → Add webhook**:

| Field | Value |
|-------|-------|
| Payload URL | `https://your-ngrok-url/webhook` |
| Content type | `application/json` |
| Secret | Same value as `GITHUB_WEBHOOK_SECRET` in your `.env` |
| Events | Pull requests only |

---

## 🚀 Deploy to Render (Free)

This repo includes a `render.yaml` for one-click deployment.

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → **New → Blueprint**
3. Connect your GitHub repo
4. Add your 3 environment variables in the Render dashboard
5. Copy the deployed URL (e.g. `https://code-review-agent.onrender.com`)
6. Update your GitHub Webhook URL to `https://code-review-agent.onrender.com/webhook`

> **Note:** Render's free tier spins down after 15 minutes of inactivity. The first webhook hit after spin-down will take ~30 seconds. Upgrade to a paid tier or use Railway for always-on hosting.

---

## 📁 Project Structure

```
code-review-agent/
├── src/
│   ├── agent.py          # Core review pipeline — orchestrates everything
│   ├── github_client.py  # GitHub API: fetch PRs, post comments
│   ├── webhook.py        # FastAPI server — receives GitHub webhook events
│   ├── prompts.py        # LLM prompt templates + content-aware hint engine
│   ├── cache.py          # SHA-256 keyed review cache (avoids redundant LLM calls)
│   ├── retry.py          # Exponential backoff for Groq rate limits
│   └── logger.py         # Structured logging
├── scripts/
│   ├── test_agent.py     # Manual: run a review against a real PR
│   ├── test_github.py    # Manual: verify GitHub token and repo access
│   └── test_setup.py     # Manual: verify Groq API key works
├── cache/
│   └── reviews.json      # Auto-generated review cache
├── main.py               # Entry point — starts Uvicorn
├── render.yaml           # Render deployment config
├── requirements.txt
└── .env                  # Never commit this!
```

---

## 🧠 How False Positives Are Prevented

Standard AI code review tools hallucinate issues. This agent avoids that with three techniques:

1. **Content-aware hints** — SQL injection focus is only added to the prompt when `SELECT`, `cursor.execute`, `sqlite3`, etc. actually appear in the diff. No more SQL warnings on files with zero SQL.

2. **Evidence requirement** — The system prompt requires every flagged issue to include a direct quote from the diff. If the LLM can't quote a line, it must not flag the issue.

3. **Truncation notice** — When a diff exceeds 3000 characters and gets cut, the LLM is explicitly told what was omitted and instructed not to speculate about unseen code.

---

## 🛡️ Security

- All incoming webhooks are verified using **HMAC-SHA256** against your `GITHUB_WEBHOOK_SECRET`
- The `.env` file is in `.gitignore` — never committed
- The GitHub token uses minimum required scopes (`repo`)

---

## 📋 Manual Test Scripts

```bash
# Verify Groq API key
python scripts/test_setup.py

# Verify GitHub token and repo access
python scripts/test_github.py

# Run a review against a specific PR (edit REPO and PR_NUMBER first)
python scripts/test_agent.py
```

---

## 🗺️ Roadmap

- [ ] Inline PR comments (line-level, not just PR-level)
- [ ] Persistent cache with Redis (for cloud deployments)
- [ ] pytest unit test suite with mocked Groq/GitHub
- [ ] Support for multiple LLM providers (OpenAI, Anthropic)
- [ ] Per-repo configuration via `.codereview.yaml`

---

## 📄 License

MIT — free to use, fork, and build on.

---

> Built by [Sudesh](https://github.com/Sudesh-2002) · Powered by LLaMA 3.3 70B via Groq