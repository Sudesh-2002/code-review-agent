from src.agent import CodeReviewAgent

agent = CodeReviewAgent()

# Replace with your repo and PR number
REPO = "Sudesh-2002/code-review-agent"   # ← change this
PR_NUMBER = 2                       # ← change this

review = agent.review_pr(REPO, PR_NUMBER)

print("\n" + "="*50)
print("FINAL REVIEW:")
print("="*50)
print(review)