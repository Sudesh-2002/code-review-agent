from groq import Groq
from dotenv import load_dotenv
from src.prompts import SYSTEM_PROMPT, build_review_prompt, build_summary_prompt
from src.github_client import GitHubClient
from src.cache import get_cached_review, save_review_to_cache
from src.retry import call_with_retry
from src.logger import get_logger
import os

load_dotenv()
logger = get_logger("agent")

SKIP_EXTENSIONS = [
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".lock", ".min.js", ".map", ".pdf", ".zip",
    ".woff", ".woff2", ".ttf", ".eot"
]

class CodeReviewAgent:
    def __init__(self):
        self.llm = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.github = GitHubClient()
        self.model = "llama-3.3-70b-versatile"
        logger.info("CodeReviewAgent initialized")

    def _ask_ai(self, prompt: str) -> str:
        """Call Groq with retry logic"""
        def _call():
            response = self.llm.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2500
            )
            return response.choices[0].message.content

        return call_with_retry(_call, retries=4, base_delay=5)

    def review_file(self, filename: str, patch: str, pr_info: dict,
                       file_status: str = "modified") -> str:
        """Review a single file with caching"""

        # Skip empty diffs
        if not patch or not patch.strip():
            logger.info(f"Skipping {filename} — no diff")
            return f"**{filename}**: No changes detected, skipped."

        # Skip binary/generated files
        if any(filename.endswith(ext) for ext in SKIP_EXTENSIONS):
            logger.info(f"Skipping {filename} — binary/generated file")
            return f"**{filename}**: Binary or generated file, skipped."

        # Check cache first
        cached = get_cached_review(filename, patch)
        if cached:
            return cached

        # Call AI
        logger.info(f"Reviewing {filename}...")
        prompt = build_review_prompt(filename, patch, pr_info, file_status)
        review = self._ask_ai(prompt)

        # Save to cache
        save_review_to_cache(filename, patch, review)

        return review

    def review_pr(self, repo_name: str, pr_number: int) -> str:
        """Full PR review pipeline"""
        logger.info(f"Starting review — {repo_name} PR #{pr_number}")

        # Fetch PR data
        pr_info = self.github.get_pr_info(repo_name, pr_number)
        files   = self.github.get_pr_diff(repo_name, pr_number)

        logger.info(f"PR: {pr_info['title']} | Files: {len(files)}")

        # Review each file
        all_reviews = []
        for file in files:
            review = self.review_file(
                filename=file["filename"],
                patch=file["patch"],
                pr_info=pr_info,
                file_status=file.get("status", "modified")
            )
            all_reviews.append(f"### `{file['filename']}`\n{review}")
            logger.debug(f"Done: {file['filename']}")

        # Generate final summary
        logger.info("Generating PR summary...")
        summary_prompt  = build_summary_prompt(all_reviews, pr_info)
        final_summary   = self._ask_ai(summary_prompt)

        # Post to GitHub
        logger.info("Posting review to GitHub...")
        self.github.post_pr_comment(repo_name, pr_number, final_summary)

        logger.info(f"Review complete for PR #{pr_number}")
        return final_summary