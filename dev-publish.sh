#!/usr/bin/env bash
# Local development and dev-push script

echo "============================================="
echo "        Mealie - Local Dev Launcher          "
echo "============================================="

# 1. Verify Docker Daemon is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Error: Docker daemon is not running. Please start Docker first."
    exit 1
fi

# 2. Git Branch & Changes Check
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    CURRENT_BRANCH=$(git branch --show-current)
    
    # Warn if not on dev branch
    if [ "$CURRENT_BRANCH" != "dev" ]; then
        echo "ℹ️ Note: You are currently on branch '$CURRENT_BRANCH'."
        echo "Pushing changes will update the remote 'dev' branch."
        read -p "Would you like to switch to your local 'dev' branch first? (y/N): " -r branch_choice
        if [[ "$branch_choice" =~ ^[Yy]$ ]]; then
            git checkout dev
            CURRENT_BRANCH="dev"
        fi
    fi

    # Check for uncommitted changes
    status_output=$(git status --porcelain)
    if [ -n "$status_output" ]; then
        echo "⚠️ You have uncommitted changes in your workspace."
        read -p "Would you like to commit and push them to the remote dev branch? (y/N): " -r push_choice
        if [[ "$push_choice" =~ ^[Yy]$ ]]; then
            read -p "Enter commit message: " -r commit_msg
            if [ -z "$commit_msg" ]; then
                commit_msg="dev: update local progress"
            fi
            
            echo "Staging and committing changes..."
            git add -A
            git commit -m "$commit_msg"
            
            echo "Pushing HEAD to remote 'dev' branch..."
            git push origin HEAD:dev
        else
            echo "Skipping commit/push. Local changes will be used only locally."
        fi
    else
        echo "✅ Working tree is clean."
        # If on dev, check if local is ahead of origin
        if [ "$CURRENT_BRANCH" = "dev" ] && [ -n "$(git log origin/dev..HEAD 2>/dev/null)" ]; then
            read -p "Your local dev branch is ahead of origin/dev. Push to GitHub? (y/N): " -r push_ahead
            if [[ "$push_ahead" =~ ^[Yy]$ ]]; then
                git push origin dev
            fi
        fi
    fi
fi

# 3. Local Docker Build & Start (Development build from workspace)
echo "Starting local docker-compose environment..."
docker compose -f docker/docker-compose.yml down
docker compose -f docker/docker-compose.yml up --build -d

echo "============================================="
echo "🚀 Local Dev Environment is UP!"
echo "Web app URL: http://localhost:9091"
echo "To view logs: docker compose -f docker/docker-compose.yml logs -f"
echo "To stop app:  docker compose -f docker/docker-compose.yml stop"
echo "============================================="
