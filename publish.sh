#!/usr/bin/env bash
# Local development and LAN publishing script

echo "============================================="
echo "        Mealie - Local LAN Publisher         "
echo "============================================="

# 1. Verify Docker Daemon is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Error: Docker daemon is not running. Please start Docker first."
    exit 1
fi

# 2. Git Branch & Changes Check
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    CURRENT_BRANCH=$(git branch --show-current)
    
    # Warn if not on main branch
    if [ "$CURRENT_BRANCH" != "main" ]; then
        echo "ℹ️ Note: You are currently on branch '$CURRENT_BRANCH'."
        echo "Pushing changes will update the remote 'main' branch."
        read -p "Would you like to switch to your local 'main' branch first? (y/N): " -r branch_choice
        if [[ "$branch_choice" =~ ^[Yy]$ ]]; then
            git checkout main
            CURRENT_BRANCH="main"
        fi
    fi

    # Check for uncommitted changes
    status_output=$(git status --porcelain)
    if [ -n "$status_output" ]; then
        echo "⚠️ You have uncommitted changes in your workspace."
        read -p "Would you like to commit and push them to the remote main branch? (y/N): " -r push_choice
        if [[ "$push_choice" =~ ^[Yy]$ ]]; then
            read -p "Enter commit message: " -r commit_msg
            if [ -z "$commit_msg" ]; then
                commit_msg="chore: update local progress"
            fi
            
            echo "Staging and committing changes..."
            git add -A
            git commit -m "$commit_msg"
            
            echo "Pushing HEAD to remote 'main' branch..."
            git push origin HEAD:main
        else
            echo "Skipping commit/push. Local changes will be used only locally."
        fi
    else
        echo "✅ Working tree is clean."
        # If on main, check if local is ahead of origin
        if [ "$CURRENT_BRANCH" = "main" ] && [ -n "$(git log origin/main..HEAD 2>/dev/null)" ]; then
            read -p "Your local main branch is ahead of origin/main. Push to GitHub? (y/N): " -r push_ahead
            if [[ "$push_ahead" =~ ^[Yy]$ ]]; then
                git push origin main
            fi
        fi
    fi
fi

# 3. Docker Build & Push to GHCR
echo "Building Docker image locally..."
docker compose -f docker/docker-compose.yml build mealie

echo "Pushing Docker image to GitHub Container Registry (ghcr.io)..."
docker push ghcr.io/jaredgriffiths/mealie:latest

echo "============================================="
echo "✅ Image successfully built and pushed to GHCR!"
echo "Image: ghcr.io/jaredgriffiths/mealie:latest"
echo ""
echo "Next step: Pull the updated image and restart the containers"
echo "on your server (192.168.50.107):"
echo "  docker compose pull && docker compose up -d"
echo "============================================="
