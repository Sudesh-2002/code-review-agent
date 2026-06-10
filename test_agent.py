from src.agent import CodeReviewAgent

agent = CodeReviewAgent()

# Replace with your repo and PR number
REPO = "your-username/your-repo"   # ← change this
PR_NUMBER = 1                       # ← change this

review = agent.review_pr(REPO, PR_NUMBER)

print("\n" + "="*50)
print("FINAL REVIEW:")
print("="*50)
print(review)