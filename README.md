# Colony Dynamics Simulator

This guide provides instructions on how to build and run the Colony Dynamics Simulator application on both Windows and macOS.

## 1. Architecture

The application consists of two main components:

* **Server Application (`server_app`):** A backend API built with FastAPI that manages the simulation logic using fine-tuned AI models. It is protected by an API key.
* **Client Application (`client_app`):** A Unity application that visualizes the simulation and communicates with the server, providing the API key to authorize requests.

Both components must be running for the simulation to work correctly.

## 2. Prerequisites

Before you begin, ensure you have the following:

* **Unity Editor:** Ensure the Unity version is 6000.0.32f1.
* **Python:** Python 3.9.11.
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

After initiating the fine-tuning jobs, you will receive unique model identifiers for each. You will use these identifiers in the server's environment file.

## 4. Environment Setup (.env files)

A crucial step for running the application is creating two separate environment files: one for the server and one for the client.

### 4.1. Server Environment (`server_app/.env`)

This file contains the credentials for the AI models and the key for securing the API.

1.  **Create the file:** In the `/server_app` directory, create a new file named `.env`.
2.  **Populate the file:** Add the following content, filling in your specific values.

    ```env
    OPENAI_API_KEY=YOUR_OPENAI_API_KEY_HERE
    FINE_TUNED_MODEL_NAME=YOUR_FIRST_MODEL_ID_HERE
    2ND_FINE_TUNED_MODEL_NAME=YOUR_SECOND_MODEL_ID_HERE
    API_SERVER_KEY=YOUR_SHARED_SECRET_KEY_HERE
    ```

### 4.2. Client Environment (`client_app/.env`)

This file contains the local paths to build the Unity application and the API key to communicate with the server.

1.  **Create the file:** In the `/client_app` directory, create a new file named `.env`.
2.  **Populate the file:** Add the following content:

    ```env
    UNITY_EXECUTABLE_PATH=
    UNITY_PROJECTS_PATH=
    API_KEY=YOUR_SHARED_SECRET_KEY_HERE
    ```

3.  **Fill in the required values:**
    * `UNITY_EXECUTABLE_PATH`: The absolute path to the Unity Editor executable.
        * **Example (Windows):** `C:/Program Files/Unity/Hub/Editor/6000.0.32f1/Editor/Unity.exe`
        * **Example (macOS):** `/Applications/Unity/Hub/Editor/6000.0.32f1/Unity.app/Contents/MacOS/Unity`
    * `UNITY_PROJECTS_PATH`: The absolute path to your personal Unity project directory.
    * `API_KEY`: The shared secret key to access the server.

> **Important:** The value for `API_KEY` in the client's `.env` file **must be exactly the same** as the value for `API_SERVER_KEY` in the server's `.env` file. This acts as a shared password between the two applications.

## 5. Server Setup

With the server's `.env` file configured, you can start the server.

1.  **Navigate to the server directory:** `cd server_app`
2.  **Run the setup script:** `./setup_and_run.sh`
3.  The server will be active at `http://127.0.0.1:8000`. Keep this terminal open.

## 6. Client Setup and Build

Once your `.env` file is correctly set up with your OpenAI API key and fine-tuned model names, you can proceed to build the application.

### On Windows

1.  **Python Version:** Ensure you have Python version 3.9.11 installed.
2.  **Python in PATH:** Add your Python 3.9.11 installation directory to your system's PATH environment variable.
3.  **Execute Build Script:** Open PowerShell, navigate to the `/app` directory, and run the `Windows_build.ps1` script:
    ```powershell
    .\Windows_build.ps1
    ```
4.  **Run Application:** After a successful build, the application will be located at `./Windows_dist/ColonyDynamicsSimulator.exe`. You can run this executable.

### On macOS

1.  **Environment File:** Ensure your `.env` file in the `/app` directory is correctly configured as described in Section 2.
2.  **Execute Build Script:** Open Terminal, navigate to the `/app` directory, and run the `Mac_build.sh` script with `sudo` permissions. The script will handle the installation of the required Python version automatically.
    ```bash
    sudo ./Mac_build.sh
    ```
3.  **Run Application:** After the build process completes, the application bundle will be named `ColonyDynamicsSimulator.app`. The executable is located inside this bundle at `ColonyDynamicsSimulator.app/Contents/MacOS/ColonyDynamicsSimulator`. To run it, navigate to this path in the Terminal and execute it:
    ```bash
    ./ColonyDynamicsSimulator.app/Contents/MacOS/ColonyDynamicsSimulator
    ```
    Alternatively, you might be able to run it by double-clicking the `ColonyDynamicsSimulator.app` bundle in Finder, but running from the terminal as shown above is recommended if you encounter issues or need to see console output.

## 7. Troubleshooting

* **Connection/Authentication Errors:** If the client cannot connect to the server, first ensure the server is running. Then, verify that the `API_KEY` in `client_app/.env` and `API_SERVER_KEY` in `server_app/.env` are identical.
* **Server doesn't start:** Check for errors in the server's terminal. Ensure your `server_app/.env` file is correct and the `OPENAI_API_KEY` has permissions.
* **Build fails:** Incorrect paths in `client_app/.env` are the most common cause of build failures.
* **Unity Build Errors:** Check Unity logs at `~/Library/Logs/Unity/Editor.log` (macOS) or `C:\Users\your_user\AppData\Local\Unity\Editor\Editor.log` (Windows).
