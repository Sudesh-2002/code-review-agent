from src.github_client import GitHubClient

client = GitHubClient()

# Replace with: "your-github-username/your-repo-name" and a real PR number
REPO = "Sudesh-2002/code-review-agent"   # ← change this
PR_NUMBER = 1                   # ← change this to a real PR number

print("--- PR Info ---")
info = client.get_pr_info(REPO, PR_NUMBER)
for key, value in info.items():
    print(f"{key}: {value}")

print("\n--- Changed Files ---")
files = client.get_pr_diff(REPO, PR_NUMBER)
for file in files:
    print(f"\n📄 {file['filename']} ({file['status']})")
    print(f"   +{file['additions']} additions, -{file['deletions']} deletions")
    print(f"   Diff preview: {file['patch'][:200]}...")