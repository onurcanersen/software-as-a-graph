#!/usr/bin/env bash
set -eo pipefail

IMAGE_NAME="genieus:1.16.0"
CONTAINER_NAME="genieus"
IMAGE_TAR="genieus_1.16.0.tar"
MAX_WAIT=120

PORTS=(7474 7687 8000 7000)
declare -A PORT_LABELS=(
  [7474]="Neo4j HTTP"
  [7687]="Neo4j Bolt"
  [8000]="FastAPI Backend"
  [7000]="Next.js Frontend"
)

check_port() {
  local port=$1
  if [[ "$port" -eq 7687 ]]; then
    (echo > /dev/tcp/localhost/$port) 2>/dev/null
  else
    curl -sf --max-time 2 "http://localhost:${port}" &>/dev/null
  fi
}

echo "=========================================="
echo " Genieus Start Script"
echo "=========================================="

if ! docker image inspect "$IMAGE_NAME" &>/dev/null; then
  echo "[1/4] Image '$IMAGE_NAME' not found"
  if [[ ! -f "$IMAGE_TAR" ]]; then
    echo "ERROR: Image tar '$IMAGE_TAR' not found. Cannot load image."
    exit 1
  fi
  echo "       Loading image from '$IMAGE_TAR'..."
  docker load -i "$IMAGE_TAR"
  echo "       Image loaded."
else
  echo "[1/4] Image '$IMAGE_NAME' already present."
fi

if ! docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
  echo "[2/4] Container '$CONTAINER_NAME' not found. Creating with host network..."
  docker run -d \
    --name "$CONTAINER_NAME" \
    --network host \
    --restart unless-stopped \
    "$IMAGE_NAME"
  echo "       Container created and started."
else
  if docker ps --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
    echo "[2/4] Container '$CONTAINER_NAME' is already running."
  else
    echo "[2/4] Container '$CONTAINER_NAME' exists but is stopped. Starting..."
    docker start "$CONTAINER_NAME"
    echo "       Container started."
  fi
fi

echo "[3/4] Waiting for services to become healthy..."

all_up=false
elapsed=0
while [[ $elapsed -lt $MAX_WAIT ]]; do
  all_up=true
  for port in "${PORTS[@]}"; do
    if ! check_port "$port"; then
      all_up=false
      break
    fi
  done
  if $all_up; then
    break
  fi
  sleep 3
  elapsed=$((elapsed + 3))
  printf "\r       %ds / %ds — services starting..." "$elapsed" "$MAX_WAIT"
done
echo ""

if $all_up; then
  echo "[4/4] All services are up:"
  for port in "${PORTS[@]}"; do
    if [[ $port -eq 7687 ]]; then
      echo "       ${PORT_LABELS[$port]}: bolt://localhost:$port"
    else
      echo "       ${PORT_LABELS[$port]}: http://localhost:$port"
    fi
  done
  echo ""
  echo "Ready."
else
  echo "ERROR: Not all services came up within ${MAX_WAIT}s."
  echo "Check logs: docker logs $CONTAINER_NAME"
  exit 1
fi
