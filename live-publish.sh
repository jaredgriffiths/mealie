#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -e

# Configuration
PROD_BRANCH="mealie-next"
DEV_BRANCH="dev"
REGISTRY_HOST="192.168.50.107:5000"
IMAGE_NAME="mealie"
IMAGE_TAG="latest"

# Help message
show_help() {
  echo "Usage: ./live-publish.sh [OPTIONS]"
  echo ""
  echo "Automates the Live workflow: merges '$DEV_BRANCH' into '$PROD_BRANCH',"
  echo "pushes to origin, builds the Docker image, and publishes it to the LAN registry."
  echo ""
  echo "Options:"
  echo "  -r, --registry REGISTRY   Registry host/port (default: '$REGISTRY_HOST')"
  echo "  -t, --tag TAG             Docker image tag (default: '$IMAGE_TAG')"
  echo "  -h, --help                Show this help message"
}

# Parse options
while [[ $# -gt 0 ]]; do
  case $1 in
    -r|--registry)
      REGISTRY_HOST="$2"
      shift 2
      ;;
    -t|--tag)
      IMAGE_TAG="$2"
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

# 1. Branch Management & Integration
echo "=== Step 1: Merging $DEV_BRANCH into $PROD_BRANCH ==="
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: Not a git repository."
  exit 1
fi

# Ensure dev branch exists
if ! git show-ref --verify --quiet "refs/heads/$DEV_BRANCH"; then
  echo "Error: Branch '$DEV_BRANCH' does not exist. Cannot publish live without a dev branch."
  exit 1
fi

# Checkout production branch
echo "Checking out production branch '$PROD_BRANCH'..."
git checkout "$PROD_BRANCH"
git pull origin "$PROD_BRANCH"

# Merge dev into production branch
echo "Merging '$DEV_BRANCH' into '$PROD_BRANCH'..."
git merge "$DEV_BRANCH" --no-edit

# Push production branch to origin
echo "Pushing '$PROD_BRANCH' to origin..."
git push origin "$PROD_BRANCH"

# 2. Docker Build & Push to LAN Registry
echo "=== Step 2: Building and Publishing to LAN Registry ==="
FULL_IMAGE_NAME="$REGISTRY_HOST/$IMAGE_NAME:$IMAGE_TAG"

echo "Building Docker image '$FULL_IMAGE_NAME' from 'docker/Dockerfile'..."
docker build -f docker/Dockerfile -t "$FULL_IMAGE_NAME" .

echo "Docker build succeeded!"

echo "Pushing '$FULL_IMAGE_NAME' to local LAN registry..."
docker push "$FULL_IMAGE_NAME"

echo "=== Live publish complete! Image is active on your LAN registry: $FULL_IMAGE_NAME ==="
