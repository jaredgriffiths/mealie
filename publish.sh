#!/usr/bin/env bash
# Publish code to GitHub to trigger automatic image building and publishing

set -e

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
    else
        echo "❌ Aborting: publishing must be performed from the 'main' branch."
        exit 1
    fi
fi

# 3. Check Remote Synchronization
echo "🔍 Checking remote status from GitHub..."
git fetch origin main --quiet || true

BEHIND_COUNT=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo 0)
if [ "$BEHIND_COUNT" -gt 0 ]; then
    echo "⚠️ Your local branch is behind origin/main by $BEHIND_COUNT commit(s)."
    read -p "Would you like to rebase from origin/main now? (Y/n): " -r rebase_choice
    if [[ ! "$rebase_choice" =~ ^[Nn]$ ]]; then
        echo "Rebasing onto origin/main..."
        git pull origin main --rebase
    else
        echo "❌ Aborting to avoid non-fast-forward push rejection."
        exit 1
    fi
fi

PUSHED=false

# 4. Handle Uncommitted Changes
status_output=$(git status --porcelain)
if [ -n "$status_output" ]; then
    echo "⚠️ You have uncommitted changes in your workspace:"
    git status --short
    echo ""
    read -p "Would you like to commit and push them to GitHub? (y/N): " -r push_choice
    if [[ "$push_choice" =~ ^[Yy]$ ]]; then
        read -p "Enter commit message (or press enter for default): " -r commit_msg
        if [ -z "$commit_msg" ]; then
            commit_msg="chore: update Mealie code"
        fi

        echo "Staging and committing changes..."
        git add -A
        git commit -m "$commit_msg"

        echo "Pushing changes to GitHub 'main' branch..."
        git push origin main
        PUSHED=true
    else
        echo "Skipping commit & push. No changes sent to GitHub."
        exit 0
    fi
else
    echo "✅ Working tree is clean."
    # Check if local is ahead of origin
    AHEAD_COUNT=$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)
    if [ "$AHEAD_COUNT" -gt 0 ]; then
        echo "ℹ️ Your local main branch is ahead of origin/main by $AHEAD_COUNT commit(s)."
        read -p "Push these commits to GitHub? (y/N): " -r push_ahead
        if [[ "$push_ahead" =~ ^[Yy]$ ]]; then
            git push origin main
            PUSHED=true
        fi
    else
        echo "ℹ️ Local is already in sync with origin/main."
        read -p "Trigger a rebuild on GitHub Actions anyway? (y/N): " -r rebuild_choice
        if [[ "$rebuild_choice" =~ ^[Yy]$ ]]; then
            echo "Creating empty trigger commit..."
            git commit --allow-empty -m "ci: manually trigger live-publish rebuild"
            git push origin main
            PUSHED=true
        fi
    fi
fi

echo "============================================="
if [ "$PUSHED" = true ]; then
    echo "🚀 Code successfully pushed to GitHub main!"
    echo "GitHub Actions is building your production image directly on ghcr.io."
    echo "Build tracker: https://github.com/jaredgriffiths/mealie/actions"
    echo ""
    echo "Once the GitHub Actions build finishes (~1-2 mins):"
    echo "  1. Open Portainer: http://192.168.50.107:9000"
    echo "  2. Go to 'Stacks' -> 'mealie' -> 'Editor'"
    echo "  3. Ensure 'Re-pull image' is ENABLED and click 'Update the stack'"
    echo "     (Or under Containers -> 'mealie' -> 'Recreate' with 'Re-pull image' ON)"
    echo "  4. Access your updated Mealie instance at:"
    echo "     http://192.168.50.107:9925"
else
    echo "ℹ️ No changes were pushed to GitHub."
fi
echo "============================================="
