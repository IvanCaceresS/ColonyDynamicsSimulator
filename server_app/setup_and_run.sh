#!/bin/bash

# --- Script Configuration ---
IMAGE_NAME="unity_sim_api_server"
DOCKERFILE_PATH="." # Assumes Dockerfile is in the same directory as this script (server_app)
ENV_FILE="./api.env" # Path to your .env file, expected in the same directory

# --- Function to handle errors and exit ---
handle_error() {
    echo "Error on line $1: $2"
    echo "Script aborted."
    exit 1
}

# Trap errors and call the handler
trap 'handle_error ${LINENO} "${BASH_COMMAND}"' ERR

echo "🚀 Starting Docker setup and execution script for the API server..."

# --- 1. Check for Docker ---
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed or not found in PATH."
    echo "Please install Docker and ensure it's accessible from your terminal."
    exit 1
fi
echo "✅ Docker found."

# --- 2. Check for .env file ---
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ CRITICAL ERROR: '$ENV_FILE' not found in the current directory ($(pwd))."
    echo "This file is required by the application (api.py) to load API keys and other configurations."
    echo "Please create '$ENV_FILE' in the same directory as this script."
    echo "Example content for api.env:"
    echo "------------------------------------"
    echo "OPENAI_API_KEY=your_openai_key_here"
    echo "FINE_TUNED_MODEL_NAME=your_primary_model_name_here"
    echo "2ND_FINE_TUNED_MODEL_NAME=your_secondary_model_name_here"
    echo "API_SERVER_KEY=your_chosen_api_server_key_here"
    echo "FLASK_RUN_PORT=5000"
    echo "------------------------------------"
    exit 1
fi
echo "✅ '$ENV_FILE' found."

# --- 3. Build Docker Image ---
echo "🛠️ Building Docker image '$IMAGE_NAME' from Dockerfile in '$DOCKERFILE_PATH'..."
# The Dockerfile copies all files from the build context ('.') into the image.
# This ensures api.env is included in the image for api.py to use.
docker build -t "$IMAGE_NAME" "$DOCKERFILE_PATH"
echo "✅ Docker image '$IMAGE_NAME' built successfully."

# --- 4. Run Docker Container ---
# Determine the application port from api.env, default to 5000 if not set
# api.py uses os.getenv("FLASK_RUN_PORT", 5000)
APP_PORT=$(grep FLASK_RUN_PORT "$ENV_FILE" | cut -d '=' -f2 | tr -d '[:space:]')
APP_PORT=${APP_PORT:-5000} # Default to 5000 if not found or empty

CONTAINER_NAME="${IMAGE_NAME}_container"

# Stop and remove if container with the same name already exists
if [ "$(docker ps -q -f name=^/${CONTAINER_NAME}$)" ]; then
    echo "🔄 Stopping existing container '$CONTAINER_NAME'..."
    docker stop "$CONTAINER_NAME" > /dev/null
fi
if [ "$(docker ps -aq -f status=exited -f name=^/${CONTAINER_NAME}$)" ]; then
    echo "🗑️ Removing existing container '$CONTAINER_NAME'..."
    docker rm "$CONTAINER_NAME" > /dev/null
fi

echo "🏃 Running Docker container '$IMAGE_NAME' as '$CONTAINER_NAME'..."
echo "   Container will run in detached mode (-d)."
echo "   Host port $APP_PORT will be mapped to container port $APP_PORT."
echo "   The application inside the container will use configuration from the copied 'api.env'."

# Run in detached mode (-d)
# Use --rm to automatically remove the container when it exits/stops.
# Map the host port to the container port.
docker run -d --rm \
    -p "${APP_PORT}:${APP_PORT}" \
    --name "$CONTAINER_NAME" \
    "$IMAGE_NAME"

echo "✅ Docker container '$CONTAINER_NAME' is starting."
echo "   Application should be accessible at http://localhost:${APP_PORT}"
echo "   To view logs: docker logs -f ${CONTAINER_NAME}"
echo "   To stop the container: docker stop ${CONTAINER_NAME}"
echo "🎉 Script finished."