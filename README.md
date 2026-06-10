# 🤖 Code Review Agent

An autonomous AI agent that automatically reviews Pull Requests on GitHub and posts structured feedback as comments.

## ✨ Features
- 🔴 Detects security vulnerabilities
- 🐛 Finds bugs and edge cases
- 🎨 Reviews code style and quality
- 📝 Posts inline and summary comments on GitHub
- ⚡ Triggers automatically on every PR via webhook

## 🛠️ Tech Stack
- **Python** — core language
- **FastAPI** — webhook server
- **Groq API** — free AI (LLaMA 3.3 70B)
- **PyGithub** — GitHub integration
- **Railway** — deployment

## ⚙️ Setup

### 1. Clone the repo
```bash
git clone https://github.com/your-username/code-review-agent.git
cd code-review-agent
```

### 2. Install dependencies
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set environment variables
Create a `.env` file:
```
GROQ_API_KEY=your_groq_api_key
GITHUB_TOKEN=your_github_token
GITHUB_WEBHOOK_SECRET=your_webhook_secret
```

### 4. Run locally
```bash
python main.py
```

### 5. Expose with ngrok
```bash
ngrok http 8000
```

### 6. Add GitHub Webhook
- Go to your repo → Settings → Webhooks → Add webhook
- Payload URL: `https://your-ngrok-url/webhook`
- Content type: `application/json`
- Events: Pull requests only

## 🚀 Deploy to Railway
See deployment section below.

## 📁 Project Structure
```
code-review-agent/
├── src/
│   ├── agent.py          # AI review logic
│   ├── github_client.py  # GitHub API client
│   ├── webhook.py        # FastAPI webhook server
│   └── prompts.py        # AI prompt templates
├── main.py               # Entry point
├── requirements.txt
└── .env
```

## 📄 License
MIT