#!/bin/bash

# --- Function to handle errors and exit ---
# This should be defined early so it's available for all subsequent commands.
handle_error() {
    echo "❌ Error on line $1: $2"
    echo "Script aborted."
    exit 1
}

# Trap errors and call the handler
# This should also be set early.
trap 'handle_error ${LINENO} "${BASH_COMMAND}"' ERR

# --- 1. Ensure script is run with sudo ---
# This is now one of the very first operational checks.
if [ "$EUID" -ne 0 ]; then
  echo "🔒 This script needs to be run with sudo privileges for Docker installation and management."
  echo "   Attempting to re-run with sudo..."
  # Re-execute the script with sudo, passing all original arguments
  sudo "$0" "$@"
  # Exit the current non-sudo script
  exit $?
fi
echo "✅ Script is running with sudo privileges."

# --- Script Configuration ---
IMAGE_NAME="unity_sim_api_server"
DOCKERFILE_PATH="." # Assumes Dockerfile is in the same directory as this script (server_app)
ENV_FILE="./api.env" # Path to your .env file, expected in the same directory

# --- Function to install Docker if not present ---
install_docker_if_needed() {
    if command -v docker &> /dev/null; then
        echo "✅ Docker is already installed."
        docker_version=$(sudo docker --version)
        echo "   Docker version: $docker_version"
        return
    fi

    echo "🛠️ Docker not found. Proceeding with installation (for Ubuntu/Debian-based systems)..."

    # Add Docker's official GPG key:
    echo "   Updating package list..."
    sudo apt-get update -qq
    echo "   Installing prerequisite packages..."
    sudo apt-get install -y -qq ca-certificates curl
    echo "   Creating Docker keyrings directory..."
    sudo install -m 0755 -d /etc/apt/keyrings
    echo "   Downloading Docker GPG key..."
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    echo "   Setting permissions for Docker GPG key..."
    sudo chmod a+r /etc/apt/keyrings/docker.asc

    # Add the repository to Apt sources:
    echo "   Adding Docker repository to APT sources..."
    # Determine the codename, supporting Ubuntu and Debian derivatives
    OS_RELEASE_INFO=$(. /etc/os-release && echo "$ID $VERSION_CODENAME")
    if [[ "$OS_RELEASE_INFO" == *"ubuntu"* ]]; then
        CODENAME=$(. /etc/os-release && echo "$UBUNTU_CODENAME")
    elif [[ "$OS_RELEASE_INFO" == *"debian"* ]]; then
        CODENAME=$(. /etc/os-release && echo "$VERSION_CODENAME")
    else # Fallback for other derivatives, might need adjustment
        CODENAME=$(. /etc/os-release && echo "$VERSION_CODENAME") # General fallback
        if [ -z "$CODENAME" ] && [ -f /etc/lsb-release ]; then # Try lsb-release if available
             CODENAME=$(grep DISTRIB_CODENAME /etc/lsb-release | cut -d'=' -f2)
        fi
    fi
    
    if [ -z "$CODENAME" ]; then
        echo "❌ Error: Could not automatically determine the OS codename for Docker repository."
        echo "   Supported distributions for auto-detection: Ubuntu, Debian."
        echo "   For other distributions, please add the Docker repository manually and re-run the script."
        exit 1
    fi
    echo "   Detected OS codename: $CODENAME"

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
      ${CODENAME} stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    echo "   Updating package list after adding Docker repository..."
    sudo apt-get update -qq
    echo "   Installing Docker packages..."
    sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    if command -v docker &> /dev/null; then
        echo "✅ Docker installed successfully."
        docker_version=$(sudo docker --version)
        echo "   Docker version: $docker_version"
    else
        echo "❌ Error: Docker installation failed. Please check the output above."
        exit 1
    fi
}

echo "🚀 Starting Docker setup and execution script for the API server..."

# --- 2. Install Docker if needed ---
# (The sudo check is now step 1, so this effectively becomes step 2 of operations)
install_docker_if_needed

# --- 3. Check for .env file ---
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

# --- 4. Build Docker Image ---
echo "🛠️ Building Docker image '$IMAGE_NAME' from Dockerfile in '$DOCKERFILE_PATH'..."
# The Dockerfile copies all files from the build context ('.') into the image.
# This ensures api.env is included in the image for api.py to use.
sudo docker build -t "$IMAGE_NAME" "$DOCKERFILE_PATH"
echo "✅ Docker image '$IMAGE_NAME' built successfully."

# --- 5. Run Docker Container ---
# Determine the application port from api.env, default to 5000 if not set
# api.py uses os.getenv("FLASK_RUN_PORT", 5000)
APP_PORT_LINE=$(grep FLASK_RUN_PORT "$ENV_FILE")
APP_PORT=""
if [[ -n "$APP_PORT_LINE" ]]; then
    APP_PORT=$(echo "$APP_PORT_LINE" | cut -d '=' -f2 | tr -d '[:space:]')
fi
APP_PORT=${APP_PORT:-5000} # Default to 5000 if not found or empty

CONTAINER_NAME="${IMAGE_NAME}_container"

# Stop and remove if container with the same name already exists
if [ "$(sudo docker ps -q -f name=^/${CONTAINER_NAME}$)" ]; then
    echo "🔄 Stopping existing container '$CONTAINER_NAME'..."
    sudo docker stop "$CONTAINER_NAME" > /dev/null
fi
if [ "$(sudo docker ps -aq -f status=exited -f name=^/${CONTAINER_NAME}$)" ]; then
    echo "🗑️ Removing existing container '$CONTAINER_NAME'..."
    sudo docker rm "$CONTAINER_NAME" > /dev/null
fi

echo "🏃 Running Docker container '$IMAGE_NAME' as '$CONTAINER_NAME'..."
echo "   Container will run in detached mode (-d)."
echo "   Host port $APP_PORT will be mapped to container port $APP_PORT on all host network interfaces (0.0.0.0)."
echo "   The application inside the container will use configuration from the copied 'api.env'."

# Run in detached mode (-d)
# Use --rm to automatically remove the container when it exits/stops.
# Map the host port to the container port. By default, -p HOST_PORT:CONTAINER_PORT binds to 0.0.0.0:HOST_PORT on the host.
sudo docker run -d --rm \
    -p "${APP_PORT}:${APP_PORT}" \
    --name "$CONTAINER_NAME" \
    "$IMAGE_NAME"

echo "✅ Docker container '$CONTAINER_NAME' is starting."
echo "   Application will be listening on 0.0.0.0:${APP_PORT} on the host."
echo "   This means it should be accessible from other devices on your network using this machine's IP address."
echo "   For example: http://<your_machine_ip>:${APP_PORT}"
echo "   It is also accessible locally at http://localhost:${APP_PORT}"
echo "   🛡️ IMPORTANT: Ensure your firewall (e.g., ufw, firewalld) allows incoming connections to port ${APP_PORT} if accessing from other devices."
echo "   To view logs: sudo docker logs -f ${CONTAINER_NAME}"
echo "   To stop the container: sudo docker stop ${CONTAINER_NAME}"
echo "🎉 Script finished."
