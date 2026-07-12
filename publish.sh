#!/usr/bin/env bash
# Publish code to GitHub to trigger automatic image building and publishing

echo "============================================="
echo "        Mealie - Code & Image Publisher       "
echo "============================================="

# 1. Verify Git Repository
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "❌ Error: Not a git repository."
    exit 1
fi

CURRENT_BRANCH=$(git branch --show-current)

# 2. Check Branch
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "ℹ️ Note: You are currently on branch '$CURRENT_BRANCH'."
    read -p "Would you like to switch to 'main' first? (y/N): " -r branch_choice
    if [[ "$branch_choice" =~ ^[Yy]$ ]]; then
        git checkout main
        CURRENT_BRANCH="main"
    fi
fi

# 3. Handle Uncommitted Changes
status_output=$(git status --porcelain)
if [ -n "$status_output" ]; then
    echo "⚠️ You have uncommitted changes in your workspace."
    read -p "Would you like to commit and push them to GitHub? (y/N): " -r push_choice
    if [[ "$push_choice" =~ ^[Yy]$ ]]; then
        read -p "Enter commit message: " -r commit_msg
        if [ -z "$commit_msg" ]; then
            commit_msg="chore: update Mealie code"
        fi
        
        echo "Staging and committing changes..."
        git add -A
        git commit -m "$commit_msg"
        
        echo "Pushing changes to GitHub 'main' branch..."
        git push origin main
    else
        echo "Skipping push. No changes sent to GitHub."
        exit 0
    fi
else
    echo "✅ Working tree is clean."
    # Check if local is ahead of origin
    if [ -n "$(git log origin/main..HEAD 2>/dev/null)" ]; then
        read -p "Your local main branch is ahead of origin/main. Push commits to GitHub? (y/N): " -r push_ahead
        if [[ "$push_ahead" =~ ^[Yy]$ ]]; then
            git push origin main
        fi
    fi
fi

echo "============================================="
echo "🚀 Code successfully pushed to GitHub main!"
echo "GitHub Actions is now automatically building and publishing"
echo "your updated production image to ghcr.io."
echo ""
echo "Once the GitHub Actions build is complete (approx. 2-3 mins),"
echo "you can update Mealie on your LAN server (192.168.50.107) by running:"
echo "  docker compose pull && docker compose up -d"
echo "============================================="
