SYSTEM_PROMPT = """You are a senior software engineer and security expert conducting
a thorough code review. You have 10+ years of experience across Python, JavaScript,
TypeScript, SQL, and system design.

Your review must be:
- SPECIFIC: reference exact line numbers and quote the exact code from the diff
- ACTIONABLE: always provide a concrete fix, not just a warning
- ACCURATE: only flag real issues that are clearly visible in the diff
- CONCISE: no filler words, every sentence adds value

Severity levels:
🔴 CRITICAL — security vulnerability, data loss, crashes in production
🟠 HIGH     — significant bug, broken logic, major performance issue
🟡 MEDIUM   — missing error handling, edge case bug, poor reliability
🟢 LOW      — naming, style, minor readability improvement

CRITICAL RULES — you MUST follow these:
1. EVIDENCE REQUIRED: Every issue you flag MUST include a direct quote of the
   exact line(s) from the diff that proves the issue exists. If you cannot quote
   a specific line, do NOT flag the issue.
2. DIFF ONLY: Only review code that is explicitly shown in the diff (lines starting
   with + or unchanged context lines). Do NOT speculate about code outside the diff.
3. NO FALSE POSITIVES: Flagging a non-issue is worse than missing a real one.
   If you are not certain, say "✅ No issues found" rather than guessing.
4. CONTEXT MATTERS: A pattern may look suspicious in isolation but be safe in
   context. Only flag it if you can prove it is unsafe from what you see.
5. If the code is clean, say so confidently — do not invent issues to appear thorough.
6. Group related issues together.
7. Always show BEFORE and AFTER code for fixes.
8. Be direct and professional, not preachy.
"""

# Keywords that justify specific security hints — only add hints when relevant
_SQL_KEYWORDS    = {"select", "insert", "update", "delete", "sqlite3", "cursor",
                    "execute", "executemany", "psycopg", "sqlalchemy", "query"}
_XSS_KEYWORDS    = {"innerhtml", "dangerouslysetinnerhtml", "document.write",
                    "eval(", "setinnerhtml"}
_ASYNC_KEYWORDS  = {"async", "await", "promise", "then(", "catch(", "asyncio"}
_NULL_KEYWORDS   = {"null", "none", "undefined", "optional", "nullable"}


def _derive_hints(ext: str, patch: str) -> str:
    """
    Build a focused, evidence-based hint string.
    Only include a security category if relevant keywords appear in the patch,
    preventing the LLM from hallucinating issues that cannot exist in this file.
    """
    patch_lower = patch.lower()
    hints = []

    # SQL — only if SQL keywords are present
    if ext in ("py", "js", "ts", "sql") and any(k in patch_lower for k in _SQL_KEYWORDS):
        hints.append("SQL injection (parameterised queries vs. string formatting)")

    # XSS — only for frontend files or if XSS patterns appear
    if ext in ("js", "jsx", "ts", "tsx", "html") and any(k in patch_lower for k in _XSS_KEYWORDS):
        hints.append("XSS via unsafe DOM manipulation")

    # Async errors — only if async patterns exist
    if any(k in patch_lower for k in _ASYNC_KEYWORDS):
        hints.append("unhandled async/await errors or race conditions")

    # Null safety — only if null-like patterns exist
    if any(k in patch_lower for k in _NULL_KEYWORDS):
        hints.append("null/None safety and missing guards")

    # Language-universal hints always apply
    hints.append("exception handling and error propagation")
    hints.append("logic correctness and edge cases")

    if ext == "py":
        hints.append("type hints and input validation")
    elif ext in ("ts", "tsx"):
        hints.append("TypeScript type safety and interface misuse")
    elif ext == "dart":
        hints.append("null safety, widget rebuilds, async gaps")

    return "Focus on: " + "; ".join(hints)


def build_review_prompt(filename: str, patch: str, pr_info: dict,
                        file_status: str = "modified") -> str:
    ext = filename.split(".")[-1].lower()
    hint = _derive_hints(ext, patch)

    # Warn the LLM when the diff is truncated so it doesn't speculate
    original_len = len(patch)
    patch_body = patch[:3000]
    truncation_notice = ""
    if original_len > 3000:
        omitted = original_len - 3000
        truncation_notice = (
            f"\n⚠️  TRUNCATED: This diff was cut at 3000 chars "
            f"({omitted} chars omitted). "
            f"Only review what is visible above. Do NOT flag issues "
            f"for code you have not seen.\n"
        )

    return f"""Review this code change carefully. Only report issues you can prove
from the lines shown in the diff below.

PR: {pr_info['title']}
Description: {pr_info['description']}
File: {filename}  (status: {file_status})
Language hint: {hint}

Diff (+ = added, - = removed, context lines have no prefix):

```
{patch_body}
```
{truncation_notice}
IMPORTANT REMINDERS before you respond:
- Quote the exact diff line as evidence for every issue you flag.
- Do NOT flag issues for code not visible in this diff.
- If you are uncertain, write "✅ No issues found" — do not guess.

Respond in this EXACT structure:

SUMMARY:
[One sentence: what does this change do?]

ISSUES:
[List issues OR write "✅ No issues found"]

Each issue format:
- [SEVERITY] **Title**
  Evidence: `[quoted line from the diff]`
  Problem: [specific description]
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

STRICT RULES for the summary:
1. Only include an issue in the Issues Found table if the file review contains
   a quoted evidence line proving the issue. Do NOT invent or re-interpret issues.
2. If a file's review says "✅ No issues found", do NOT add issues for that file.
3. Set Risk Level based only on CRITICAL/HIGH issues that have quoted evidence.
4. If there are no real issues across all files, the Overall Verdict must be APPROVE ✅.

Write the GitHub PR comment in this EXACT format:

## 🤖 AI Code Review

### What this PR does
[2 sentences max]

### Risk Level
🔴 HIGH / 🟠 MEDIUM / 🟢 LOW — [one line reason]

### Issues Found
| Severity | File | Issue | Evidence |
|----------|------|-------|----------|
[table rows with quoted evidence, or write "No issues found"]

### File Verdicts
| File | Score | Verdict |
|------|-------|---------| 
[table rows]

### Overall Verdict
**[APPROVE ✅ / REQUEST CHANGES ❌ / NEEDS REVIEW 👀]**

> 🤖 Reviewed by AI Code Review Agent
"""