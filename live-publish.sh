#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -e

# Configuration
PROD_BRANCH="mealie-next"
DEV_BRANCH="dev"

TIMESTAMP=$(date +%Y%m%d%H%M%S)
BACKUP_BRANCH="backup-${PROD_BRANCH}-${TIMESTAMP}"

echo "============================================="
echo "        Mealie - Production Deployer         "
echo "============================================="

# Ensure we are inside a Git repo
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "❌ Error: Not a git repository."
    exit 1
fi

ORIGINAL_BRANCH=$(git branch --show-current)
has_changes=$(git status --porcelain)

# 1. Fetch remote references
echo "Fetching latest changes from remote..."
git fetch origin

# 2. Stash changes if working directory is dirty
stashed=false
if [ -n "$has_changes" ]; then
    echo "⚠️ Working directory is not clean. Stashing changes..."
    git stash push -m "deploy_prod auto-stash: $TIMESTAMP"
    stashed=true
fi

# 3. Create safety backup branch of production
echo "Creating safety backup branch '$BACKUP_BRANCH' from origin/$PROD_BRANCH..."
git branch "$BACKUP_BRANCH" "origin/$PROD_BRANCH"

# 4. Perform checkout, pull, merge & push
echo "Switching to production branch: $PROD_BRANCH..."
git checkout "$PROD_BRANCH"

echo "Pulling latest production changes..."
git pull origin "$PROD_BRANCH"

echo "Merging '$DEV_BRANCH' into '$PROD_BRANCH'..."
if git merge "$DEV_BRANCH" --no-edit; then
    echo "Pushing merged production branch to GitHub..."
    if git push origin "$PROD_BRANCH"; then
        echo "✅ Git push successful! Production CI/CD build is triggered in GitHub Actions."
        echo "Safety backup branch '$BACKUP_BRANCH' was created."
        echo "If you need to roll back, run: git reset --hard $BACKUP_BRANCH && git push origin $PROD_BRANCH --force-with-lease"
    else
        echo "❌ Error: Failed to push to remote server."
        echo "Resetting local branch to origin/$PROD_BRANCH..."
        git reset --hard "origin/$PROD_BRANCH"
    fi
else
    echo "❌ Error: Merge conflict detected! Aborting deploy."
    echo "Resetting merge state..."
    git merge --abort
fi

# 5. Clean up and return to original branch
echo "Switching back to original branch: $ORIGINAL_BRANCH..."
git checkout "$ORIGINAL_BRANCH"

if [ "$stashed" = true ]; then
    echo "Restoring stashed changes..."
    git stash pop
fi

echo "============================================="
echo "Done!"
echo "============================================="
