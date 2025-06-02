# Unity Simulation API Server 🚀

Runs a Dockerized API server for Unity simulations.

## 📋 Prerequisites

1.  **Docker Installed:** Setup script attempts to install it (Ubuntu/Debian).
2.  **`api.env` File:**
    * Create `api.env` in the `server_app` directory.
    * Add your API keys and model names. Example:
        ```env
        OPENAI_API_KEY=your_openai_key
        FINE_TUNED_MODEL_NAME=your_primary_model
        2ND_FINE_TUNED_MODEL_NAME=your_secondary_model
        API_SERVER_KEY=your_secret_api_server_key
        FLASK_RUN_PORT=5000 # Optional, defaults to 5000
        ```
3.  **Firewall Ports:**
    * Allow **inbound TCP traffic on port `5000`** (or your `FLASK_RUN_PORT`) in your server's firewall (e.g., `ufw`) AND your cloud provider's firewall.
    * For cloud firewall inbound rules: **Source Port** should be "All"/"Any", **Destination Port** should be `5000`.
    * Outbound rules are usually permissive by default.

## 🚀 Setup & Run

1.  Navigate to `server_app` directory.
2.  Make script executable:
    ```bash
    chmod +x setup_and_run.sh
    ```
3.  Run setup script (handles sudo, Docker install, image build, container run):
    ```bash
    sudo ./setup_and_run.sh
    ```
    Access at `http://YOUR_PUBLIC_IP:5000`.

## 🪵 View Logs

```bash
sudo docker logs -f unity_sim_api_server_container
