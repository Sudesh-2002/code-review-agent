SYSTEM_PROMPT = """You are a senior software engineer and security expert conducting
a thorough code review. You have 10+ years of experience across Python, JavaScript,
TypeScript, SQL, and system design.

Your review must be:
- SPECIFIC: reference exact line numbers and variable names
- ACTIONABLE: always provide a concrete fix, not just a warning
- ACCURATE: only flag real issues, avoid false positives
- CONCISE: no filler words, every sentence adds value

Severity levels:
🔴 CRITICAL — security vulnerability, data loss, crashes in production
🟠 HIGH     — significant bug, broken logic, major performance issue
🟡 MEDIUM   — missing error handling, edge case bug, poor reliability
🟢 LOW      — naming, style, minor readability improvement

Rules:
- If the code is clean, say so confidently — don't invent issues
- Group related issues together
- Always show BEFORE and AFTER code for fixes
- Be direct and professional, not preachy
"""

def build_review_prompt(filename: str, patch: str, pr_info: dict) -> str:
    ext = filename.split(".")[-1].lower()

    # Language-aware hints
    lang_hints = {
        "py":   "Focus on: exception handling, type hints, SQL injection, input validation",
        "js":   "Focus on: async/await errors, XSS, prototype pollution, null checks",
        "ts":   "Focus on: type safety, null checks, async errors, interface misuse",
        "sql":  "Focus on: injection risks, missing indexes, N+1 queries, transactions",
        "jsx":  "Focus on: XSS via dangerouslySetInnerHTML, prop validation, re-renders",
        "tsx":  "Focus on: type safety, prop validation, XSS, unnecessary re-renders",
        "dart": "Focus on: null safety, async gaps, widget rebuilds, exception handling",
    }
    hint = lang_hints.get(ext, "Focus on: logic errors, security, error handling")

    return f"""Review this code change carefully.

PR: {pr_info['title']}
Description: {pr_info['description']}
File: {filename}
Language hint: {hint}

Diff (+ = added, - = removed):

```
{patch[:3000]}
```

Respond in this EXACT structure:

SUMMARY:
[One sentence: what does this change do?]

ISSUES:
[List issues OR write "✅ No issues found"]

Each issue format:
- [SEVERITY] **Title**
  Problem: [specific description with line reference]
  Fix:

```
[corrected code]
```

VERDICT: [APPROVE ✅ | REQUEST CHANGES ❌ | NEEDS REVIEW 👀]
SCORE: [X/10]
"""

def build_summary_prompt(all_reviews: list, pr_info: dict) -> str:
    reviews_text = "\n\n---\n\n".join(all_reviews)
    return f"""You have reviewed all files in this Pull Request. Write a final summary.

PR: {pr_info['title']}
Author: {pr_info['author']}
Files changed: {pr_info['changed_files']}
+{pr_info['additions']} additions / -{pr_info['deletions']} deletions

File reviews:
{reviews_text}

Write the GitHub PR comment in this EXACT format:

## 🤖 AI Code Review

### What this PR does
[2 sentences max]

### Risk Level
🔴 HIGH / 🟠 MEDIUM / 🟢 LOW — [one line reason]

### Issues Found
| Severity | File | Issue |
|----------|------|-------|
[table rows, or write "No issues found"]

### File Verdicts
| File | Score | Verdict |
|------|-------|---------|
[table rows]

### Overall Verdict
**[APPROVE ✅ / REQUEST CHANGES ❌ / NEEDS REVIEW 👀]**

> 🤖 Reviewed by AI Code Review Agent
"""