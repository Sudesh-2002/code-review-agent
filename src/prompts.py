SYSTEM_PROMPT = """You are an expert code reviewer with deep knowledge of:
- Software security vulnerabilities (OWASP Top 10)
- Clean code principles and best practices
- Performance optimization
- Bug detection and edge cases

Your job is to review code diffs and provide structured, actionable feedback.
Be concise, specific, and helpful. Always suggest fixes, not just problems.

Severity levels:
- 🔴 CRITICAL: Security vulnerabilities, data loss risks, crashes
- 🟠 HIGH: Significant bugs, major performance issues
- 🟡 MEDIUM: Code quality, minor bugs, missing error handling
- 🟢 LOW: Style issues, naming, minor improvements
"""

def build_review_prompt(filename: str, patch: str, pr_info: dict) -> str:
    return f"""Review this code change from a Pull Request.

PR Title: {pr_info['title']}
PR Description: {pr_info['description']}
File: {filename}

Code Diff (+ added lines, - removed lines):

{patch}

Provide your review in this EXACT format:

SUMMARY:
[One sentence describing what this file change does]

ISSUES:
[List each issue found, or write "No issues found" if clean]

Format each issue as:
- [SEVERITY EMOJI] [Issue title]
  Problem: [What is wrong]
  Fix: [Exact fix with code example if possible]
  Line: [Approximate line number from the diff]

VERDICT:
[APPROVE / REQUEST CHANGES / NEEDS REVIEW]

SCORE:
[X/10 code quality score]
"""

def build_summary_prompt(all_reviews: list, pr_info: dict) -> str:
    reviews_text = "\n\n".join(all_reviews)
    return f"""You reviewed all files in this Pull Request.

PR: {pr_info['title']}
Author: {pr_info['author']}
Files changed: {pr_info['changed_files']}
Additions: +{pr_info['additions']} Deletions: -{pr_info['deletions']}

Individual file reviews:
{reviews_text}

Write a final PR summary comment for GitHub in this EXACT format:

## 🤖 AI Code Review Summary

### PR Overview
[2-3 sentences about what this PR does overall]

### Risk Level
[🔴 HIGH / 🟠 MEDIUM / 🟢 LOW] — [One line reason]

### Key Findings
[Bullet list of the most important issues across all files]

### Files Reviewed
[List each file with a one-line verdict]

### Final Verdict
[APPROVE ✅ / REQUEST CHANGES ❌ / NEEDS REVIEW 👀]

---
*Reviewed by AI Code Review Agent*
"""