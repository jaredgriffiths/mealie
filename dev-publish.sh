#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -e

# Configuration
BRANCH_NAME="dev"
IMAGE_NAME="mealie"
IMAGE_TAG="dev"

# Help message
show_help() {
  echo "Usage: ./dev-publish.sh [OPTIONS]"
  echo ""
  echo "Automates the Dev workflow: checks out/creates the '$BRANCH_NAME' branch,"
  echo "commits changes, pushes to origin, and builds the Docker image locally."
  echo ""
  echo "Options:"
  echo "  -t, --tag TAG             Docker image tag (default: '$IMAGE_TAG')"
  echo "  -m, --message MESSAGE     Commit message (if not provided, git status will be checked and committed)"
  echo "  -h, --help                Show this help message"
}

# Parse options
COMMIT_MESSAGE=""

while [[ $# -gt 0 ]]; do
  case $1 in
    -t|--tag)
      IMAGE_TAG="$2"
      shift 2
      ;;
    -m|--message)
      COMMIT_MESSAGE="$2"
      shift 2
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      show_help
      exit 1
      ;;
  esac
done

# 1. Branch Management
echo "=== Step 1: Checking branch state ==="
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: Not a git repository."
  exit 1
fi

# Switch/create dev branch
if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
  echo "Switching to existing branch '$BRANCH_NAME'..."
  git checkout "$BRANCH_NAME"
else
  echo "Creating and switching to new branch '$BRANCH_NAME'..."
  git checkout -b "$BRANCH_NAME"
fi

# Stage changes
echo "Staging files..."
git add -A

# Check for changes
if git diff-index --quiet HEAD --; then
  echo "No changes detected to commit."
else
  if [ -z "$COMMIT_MESSAGE" ]; then
    COMMIT_MESSAGE="chore: dev updates [$(date +'%Y-%m-%dT%H:%M:%S%z')]"
  fi
  echo "Committing changes with message: '$COMMIT_MESSAGE'..."
  git commit -m "$COMMIT_MESSAGE"
fi

# Push to origin
echo "Pushing changes to origin/$BRANCH_NAME..."
git push -u origin "$BRANCH_NAME"

# 2. Docker Build (Local Host Daemon)
echo "=== Step 2: Building Docker Image (Localhost) ==="
FULL_IMAGE_NAME="$IMAGE_NAME:$IMAGE_TAG"

echo "Building Docker image '$FULL_IMAGE_NAME' from 'docker/Dockerfile'..."
docker build -f docker/Dockerfile -t "$FULL_IMAGE_NAME" .

echo "=== Dev build succeeded and is available locally on localhost Docker daemon! ==="
