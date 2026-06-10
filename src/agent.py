from groq import Groq
from dotenv import load_dotenv
from src.prompts import SYSTEM_PROMPT, build_review_prompt, build_summary_prompt
from src.github_client import GitHubClient
import os

load_dotenv()

class CodeReviewAgent:
    def __init__(self):
        self.llm = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.github = GitHubClient()
        self.model = "llama-3.3-70b-versatile"

    def _ask_ai(self, prompt: str) -> str:
        """Send a prompt to Groq and get response"""
        response = self.llm.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # lower = more consistent reviews
            max_tokens=1500
        )
        return response.choices[0].message.content

    def review_file(self, filename: str, patch: str, pr_info: dict) -> str:
        """Review a single file diff"""
        print(f"  🔍 Reviewing {filename}...")

        # Skip files with no changes
        if not patch:
            return f"**{filename}**: No diff available, skipped."

        # Skip binary or generated files
        skip_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.svg',
                          '.lock', '.min.js', '.map']
        if any(filename.endswith(ext) for ext in skip_extensions):
            return f"**{filename}**: Binary/generated file, skipped."

        prompt = build_review_prompt(filename, patch, pr_info)
        review = self._ask_ai(prompt)
        return review

    def review_pr(self, repo_name: str, pr_number: int) -> str:
        """Full PR review — reviews all files and posts summary to GitHub"""
        print(f"\n🚀 Starting review of PR #{pr_number} in {repo_name}")

        # Fetch PR data
        print("📥 Fetching PR data from GitHub...")
        pr_info = self.github.get_pr_info(repo_name, pr_number)
        files = self.github.get_pr_diff(repo_name, pr_number)

        print(f"📋 PR: {pr_info['title']}")
        print(f"📁 Files to review: {len(files)}")

        # Review each file
        all_reviews = []
        for file in files:
            review = self.review_file(
                filename=file['filename'],
                patch=file['patch'],
                pr_info=pr_info
            )
            all_reviews.append(f"### `{file['filename']}`\n{review}")

        # Generate overall summary
        print("\n📝 Generating PR summary...")
        summary_prompt = build_summary_prompt(all_reviews, pr_info)
        final_summary = self._ask_ai(summary_prompt)

        # Post to GitHub
        print("📤 Posting review to GitHub...")
        self.github.post_pr_comment(repo_name, pr_number, final_summary)

        print("\n✅ Review complete!")
        return final_summary