from github import Github
from dotenv import load_dotenv
import os

load_dotenv()

class GitHubClient:
    def __init__(self):
        self.client = Github(os.getenv("GITHUB_TOKEN"))

    def get_pr(self, repo_name: str, pr_number: int):
        """Get PR object from GitHub"""
        repo = self.client.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        return pr

    def get_pr_diff(self, repo_name: str, pr_number: int):
        """Get all changed files and their diffs from a PR"""
        pr = self.get_pr(repo_name, pr_number)

        files_data = []

        for file in pr.get_files():
            files_data.append({
                "filename": file.filename,
                "status": file.status,        # added, modified, removed
                "additions": file.additions,
                "deletions": file.deletions,
                "patch": file.patch or ""     # the actual diff/changes
            })

        return files_data

    def get_pr_info(self, repo_name: str, pr_number: int):
        """Get basic PR metadata"""
        pr = self.get_pr(repo_name, pr_number)

        return {
            "title": pr.title,
            "description": pr.body or "No description provided",
            "author": pr.user.login,
            "base_branch": pr.base.ref,
            "head_branch": pr.head.ref,
            "changed_files": pr.changed_files,
            "additions": pr.additions,
            "deletions": pr.deletions
        }

    def post_pr_comment(self, repo_name: str, pr_number: int, comment: str):
        """Post a general comment on the PR"""
        pr = self.get_pr(repo_name, pr_number)
        pr.create_issue_comment(comment)
        print(f"✅ Comment posted on PR #{pr_number}")

    def post_inline_comment(self, repo_name: str, pr_number: int,
                             filename: str, line: int, comment: str):
        """Post an inline comment on a specific line"""
        pr = self.get_pr(repo_name, pr_number)
        commit = pr.get_commits().reversed[0]  # latest commit

        pr.create_review_comment(
            body=comment,
            commit=commit,
            path=filename,
            line=line
        )
        print(f"✅ Inline comment posted on {filename}:{line}")