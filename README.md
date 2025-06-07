# Colony Dynamics Simulator

This guide provides instructions on how to build and run the Colony Dynamics Simulator application on both Windows and macOS.

## 1. Architecture

The application consists of two main components:

* **Server Application (`server_app`):** A backend API built with FastAPI that manages the simulation logic using fine-tuned AI models.
* **Client Application (`client_app`):** A Unity application that visualizes the simulation and communicates with the server. The client is built via Python scripts.

Both components must be running for the simulation to work correctly.

## 2. Prerequisites

Before you begin, ensure you have the following:

* **Unity Editor:** Ensure the Unity version specified in `client_app/Template/ProjectSettings/ProjectVersion.txt` is installed.
* **Python:** Python 3.9 or higher.
* **OpenAI Account:** An OpenAI account and API key are required for model fine-tuning.
* **Fine-tuning data files:** `fine-tuning-llm1.jsonl` and `fine-tuning-llm2.jsonl`.

## 3. AI Model Fine-Tuning

To function, the server requires two fine-tuned AI models. You must train these models using your OpenAI account.

### Model 1: `FINE_TUNED_MODEL_NAME`

* **Dataset:** Use the `fine-tuning-llm1.jsonl` file.
* **Training Parameters:**
    * `EPOCHS`: 3
    * `BATCH_SIZE`: 1
    * `LEARNING_RATE_MULTIPLIER`: 0.1
    * `Seed`: 1586160321
* **Approximate Training Cost:** $0.3777 USD

### Model 2: `2ND_FINE_TUNED_MODEL_NAME`

* **Dataset:** Use the `fine-tuning-llm2.jsonl` file.
* **Training Parameters:**
    * `EPOCHS`: 3
    * `BATCH_SIZE`: 1
    * `LEARNING_RATE_MULTIPLIER`: 0.1
    * `Seed`: 1263028636
* **Approximate Training Cost:** $0.2533 USD

After initiating the fine-tuning jobs via the OpenAI API or platform, you will receive unique model identifiers for each. You will use these identifiers in the server's environment file.

## 4. Environment Setup (.env files)

A crucial step for running the application is creating two separate environment files: one for the server and one for the client.

### 4.1. Server Environment (`server_app/.env`)

This file contains the credentials for the AI models.

1.  **Create the file:** In the `/server_app` directory, create a new file named `.env`.
2.  **Populate the file:** Add the following content to your `.env` file, filling in the values you obtained:

    ```env
    OPENAI_API_KEY=YOUR_API_KEY_HERE
    FINE_TUNED_MODEL_NAME=YOUR_FIRST_MODEL_ID_HERE
    2ND_FINE_TUNED_MODEL_NAME=YOUR_SECOND_MODEL_ID_HERE
    ```

### 4.2. Client Environment (`client_app/.env`)

This file contains the local paths needed to build the Unity application.

1.  **Create the file:** In the `/client_app` directory, create a new file named `.env`.
2.  **Populate the file:** Add the following content to your `.env` file:

    ```env
    UNITY_EXECUTABLE_PATH=
    UNITY_PROJECTS_PATH=
    ```

3.  **Fill in the required values:** You **must** provide the absolute paths for the following variables:
    * `UNITY_EXECUTABLE_PATH`: The path to the Unity Editor executable.
        * **Example on Windows:** `C:/Program Files/Unity/Hub/Editor/2022.3.20f1/Editor/Unity.exe`
        * **Example on macOS:** `/Applications/Unity/Hub/Editor/2022.3.20f1/Unity.app/Contents/MacOS/Unity`
    * `UNITY_PROJECTS_PATH`: The path to the Unity project directory to be built (`Template`).
        * **Example:** `/full/path/to/ColonyDynamicsSimulator/client_app/Template`

## 5. Server Setup

With the server's `.env` file configured, you can start the server.

1.  **Navigate to the server directory:**
    ```bash
    cd server_app
    ```
2.  **Run the setup and execution script:**
    This script will create a virtual environment, install dependencies, and start the `uvicorn` server.
    ```bash
    ./setup_and_run.sh
    ```
3.  The server will now be active and listening at `http://127.0.0.1:8000`. Keep this terminal open.

## 6. Client Setup and Build

Once the server is running and the client's `.env` file is set up, you can build the client application.

#### On Windows

1.  **Execute Build Script:** Open PowerShell, navigate to the `/client_app` directory, and run the `Windows_build.ps1` script:
    ```powershell
    .\Windows_build.ps1
    ```
2.  **Run Application:** After a successful build, the application will be at `./Windows_dist/ColonyDynamicsSimulator.exe`.

#### On macOS

1.  **Execute Build Script:** Open Terminal, navigate to the `/client_app` directory, and run the `Mac_build.sh` script with `sudo`:
    ```bash
    sudo ./Mac_build.sh
    ```
2.  **Run Application:** After the build completes, the `ColonyDynamicsSimulator.app` bundle will be in the `client_app` directory.

## 7. Troubleshooting

* **Server doesn't start:** Check for errors in the server's terminal. Ensure your `server_app/.env` file is correct and the API key has the necessary permissions.
* **Build fails:** Incorrect paths in `client_app/.env` are the most common cause of build failures. Verify they are correct and absolute.
* **Permissions Issues (macOS):** The `Mac_build.sh` script requires `sudo`. Ensure you provide your administrator password when prompted.
* **Unity Build Errors:** If the build scripts run but Unity fails, check the Unity build logs. They can be located at `~/Library/Logs/Unity/Editor.log` on macOS or `C:\Users\your_user\AppData\Local\Unity\Editor\Editor.log` on Windows.
