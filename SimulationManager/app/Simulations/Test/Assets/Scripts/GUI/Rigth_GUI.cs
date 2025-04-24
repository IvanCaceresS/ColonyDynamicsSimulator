using UnityEngine;
using UnityEngine.SceneManagement;
using System.Collections;
using System;
using System.Text;
using System.Globalization;

public class Right_GUI : MonoBehaviour
{
    // Simulation and GUI parameters
    public bool isPaused = true;
    private bool showConfigurationWindow = true;
    private bool showControls = false;
    private int[] fpsLevels = { 60, 144, 500, 1000, -1 };
    private int currentFPSIndex = 0;
    private string initialSceneName;
    private static float LowSpeedMultiplierLimit = 0.6f;
    private static float HighSpeedMultiplierLimit = 2400f;
    private string speedMultiplierInput = "1.00";

    // --- Style parameters for easy adjustment ---
    private int baseFontSize = 12; // Base font size for standard controls/text
    private int configFontSizeIncrease = 6; // How much larger fonts are in the config window
    private int configTitleFontSizeIncrease = 8; // How much larger the config window title is
    // --- End Style parameters ---

    // --- GUI Styles ---
    // Standard Styles (used outside config window)
    private GUIStyle buttonStyle;
    private GUIStyle labelStyle;
    private GUIStyle windowStyle; // Base style for windows
    private GUIStyle controlsLabelStyle; // Specific style for controls help if needed, or use labelStyle

    // Dedicated Styles for Configuration Window (Larger)
    private GUIStyle configWindowStyle;
    private GUIStyle configLabelStyle;
    private GUIStyle configCenteredLabelStyle;
    private GUIStyle configButtonStyle;
    private GUIStyle configTextFieldStyle; // Style for the text field
    // --- End GUI Styles ---

    private bool stylesInitialized = false; // Flag to ensure styles are set up once needed

    // Flag to control frame advance
    private bool isAdvancingFrame = false;

    void Start()
    {
        GameStateManager.OnSetupComplete += EnableGUI;
        initialSceneName = SceneManager.GetActiveScene().name;
        QualitySettings.vSyncCount = 0;
        Application.targetFrameRate = fpsLevels[currentFPSIndex];
    }

    void OnDestroy()
    {
        GameStateManager.OnSetupComplete -= EnableGUI;
    }

    private void EnableGUI()
    {
        Debug.Log("Right_GUI: Enabling GUI interface.");
        this.enabled = true;
    }

    void OnGUI()
    {
        if (!GameStateManager.IsSetupComplete) return;

        // Initialize styles lazily but safely ONCE before first use in OnGUI
        if (!stylesInitialized && Event.current.type == EventType.Layout) // Initialize on Layout event for safety
        {
            InitializeStyles();
            stylesInitialized = true;
        }
        if (!stylesInitialized) return; // Don't proceed if styles aren't ready


        if (showConfigurationWindow)
        {
            ShowConfigurationWindow();
        }
        else
        {
            // Use standard styles for main controls
            DrawMainControls();
        }

        // Button to show/hide camera controls (uses standard style)
        if (GUI.Button(new Rect(Screen.width - 120, Screen.height - 40, 100, 30), "Controls", buttonStyle))
        {
            showControls = !showControls;
        }

        if (showControls)
        {
            // Use standard styles for controls help
            DisplayControlsGUI();
        }
    }

    // Helper method to initialize ALL GUI styles
    private void InitializeStyles()
    {
        // --- Standard Styles ---
        buttonStyle = new GUIStyle(GUI.skin.button)
        {
            fontSize = baseFontSize,
            normal = { textColor = Color.white }
        };

        labelStyle = new GUIStyle(GUI.skin.label)
        {
            fontSize = baseFontSize,
            normal = { textColor = Color.white },
            alignment = TextAnchor.MiddleLeft
        };

        // Base window style (used for controls help box title)
        windowStyle = new GUIStyle(GUI.skin.box)
        {
            fontSize = baseFontSize + 2, // Slightly larger title for standard windows
            fontStyle = FontStyle.Bold,
            alignment = TextAnchor.UpperCenter,
            normal = { textColor = Color.white }
        };

        // Style for controls help text (can just be standard labelStyle)
        controlsLabelStyle = new GUIStyle(labelStyle);


        // --- Dedicated Config Window Styles (Larger) ---
        int configContentFontSize = baseFontSize + configFontSizeIncrease;
        int configTitleFontSize = baseFontSize + configTitleFontSizeIncrease;

        configWindowStyle = new GUIStyle(GUI.skin.box) // Inherit from box for background
        {
            fontSize = configTitleFontSize, // Larger title font size
            fontStyle = FontStyle.Bold,
            alignment = TextAnchor.UpperCenter,
            normal = { textColor = Color.white }
        };

        configLabelStyle = new GUIStyle(GUI.skin.label)
        {
            fontSize = configContentFontSize, // Larger content font size
            normal = { textColor = Color.white },
            alignment = TextAnchor.MiddleLeft // Default left alignment
        };

        configCenteredLabelStyle = new GUIStyle(configLabelStyle) // Inherit from configLabelStyle
        {
            alignment = TextAnchor.MiddleCenter // Override to center
        };

        configButtonStyle = new GUIStyle(GUI.skin.button)
        {
            fontSize = configContentFontSize, // Larger button font size
            normal = { textColor = Color.white }
            // Consider adding padding if text feels cramped: padding = new RectOffset(10, 10, 5, 5)
        };

        configTextFieldStyle = new GUIStyle(GUI.skin.textField)
        {
             fontSize = configContentFontSize // Larger text field font size
             // You might need to adjust height/padding depending on the base skin
             // alignment = TextAnchor.MiddleLeft, // Optional: ensure text aligns left
             // fixedHeight = configContentFontSize + 10 // Optional: Force height based on font
        };

        Debug.Log("GUI Styles Initialized");
    }


    // Draws the main control buttons (Uses standard buttonStyle)
    private void DrawMainControls()
    {
        int buttonWidth = 80;
        int buttonHeight = 30;
        int margin = 10;
        int startX = Screen.width - buttonWidth - margin;
        int startY = margin;
        int buttonIndex = 0;

        string fpsText = fpsLevels[currentFPSIndex] == -1 ? "Uncapped" : fpsLevels[currentFPSIndex].ToString();
        // Uses standard buttonStyle
        if (GUI.Button(new Rect(startX, startY + buttonIndex * (buttonHeight + margin), buttonWidth, buttonHeight), $"FPS: {fpsText}", buttonStyle)) { ToggleFPSLimit(); } buttonIndex++;
        if (GUI.Button(new Rect(startX, startY + buttonIndex * (buttonHeight + margin), buttonWidth, buttonHeight), isPaused ? "Resume" : "Pause", buttonStyle)) { TogglePause(); } buttonIndex++;
        if (GUI.Button(new Rect(startX, startY + buttonIndex * (buttonHeight + margin), buttonWidth, buttonHeight), "Restart", buttonStyle)) { RestartSimulation(); } buttonIndex++;
        if (GUI.Button(new Rect(startX, startY + buttonIndex * (buttonHeight + margin), buttonWidth, buttonHeight), "Exit", buttonStyle)) { ExitSimulation(); } buttonIndex++;
        if (isPaused) { if (GUI.Button(new Rect(startX, startY + buttonIndex * (buttonHeight + margin), buttonWidth, buttonHeight), "+1 Frame", buttonStyle)) { AdvanceOneFrame(); } buttonIndex++; }
    }


    private void ShowConfigurationWindow()
    {
        // Keep the larger dimensions
        int windowWidth = 525;
        int windowHeight = 270;
        Rect windowRect = new Rect((Screen.width - windowWidth) / 2, (Screen.height - windowHeight) / 2, windowWidth, windowHeight);

        // Draw the window using the dedicated configWindowStyle (already has large title font)
        GUI.Window(0, windowRect, ConfigurationWindowContent, "Simulation Configuration", configWindowStyle);
    }

    // Contains the content for the configuration window (Uses dedicated config* styles)
    private void ConfigurationWindowContent(int windowID)
    {
        // Use Vertical layout group
        GUILayout.BeginVertical();
        GUILayout.Space(30); // Space below title

        // Explanatory text (use configLabelStyle, increased width)
        GUILayout.BeginHorizontal();
        GUILayout.FlexibleSpace();
        GUILayout.Label($"Select Simulation Speed ({LowSpeedMultiplierLimit:F1}x - {HighSpeedMultiplierLimit:F0}x):", configLabelStyle, GUILayout.Width(500)); // Increased width further
        GUILayout.FlexibleSpace();
        GUILayout.EndHorizontal();

        GUILayout.Space(10); // Adjusted space

        // --- Speed Multiplier Input and Slider ---
        GUILayout.BeginHorizontal();
        GUILayout.FlexibleSpace();

        // Speed Label (use configLabelStyle, adjusted width)
        GUILayout.Label("Speed:", configLabelStyle, GUILayout.Width(85)); // Increased width

        // Text Field (use configTextFieldStyle, adjusted width)
        speedMultiplierInput = GUILayout.TextField(speedMultiplierInput, configTextFieldStyle, GUILayout.Width(85)); // Increased width, use specific style

        // Slider (adjust width)
        float parsedSpeedMultiplier;
        if (!float.TryParse(speedMultiplierInput, NumberStyles.Float, CultureInfo.InvariantCulture, out parsedSpeedMultiplier)) { parsedSpeedMultiplier = 1.0f; }
        parsedSpeedMultiplier = Mathf.Clamp(parsedSpeedMultiplier, LowSpeedMultiplierLimit, HighSpeedMultiplierLimit);
        // Give slider enough space
        parsedSpeedMultiplier = GUILayout.HorizontalSlider(parsedSpeedMultiplier, LowSpeedMultiplierLimit, HighSpeedMultiplierLimit, GUILayout.Width(280)); // Increased width
        speedMultiplierInput = parsedSpeedMultiplier.ToString("F2", CultureInfo.InvariantCulture);

        GUILayout.FlexibleSpace();
        GUILayout.EndHorizontal();

        GUILayout.Space(20); // Adjusted space

        // --- Dynamic Real Time vs Simulated Time Explanation ---
        GUILayout.BeginHorizontal();
        GUILayout.FlexibleSpace();
        // Use configCenteredLabelStyle, increased width
        GUILayout.Label(GetTimeRelationshipText(parsedSpeedMultiplier), configCenteredLabelStyle, GUILayout.Width(500)); // Increased width
        GUILayout.FlexibleSpace();
        GUILayout.EndHorizontal();

        GUILayout.FlexibleSpace(); // Pushes button to bottom

        // Start Simulation Button (use configButtonStyle, adjusted size)
        GUILayout.BeginHorizontal();
        GUILayout.FlexibleSpace();
        // Use configButtonStyle, ensure sufficient width/height for larger text
        if (GUILayout.Button("Start Simulation", configButtonStyle, GUILayout.Width(480), GUILayout.Height(45))) // Increased width/height slightly
        {
            // ... (Start Simulation Logic - no changes needed here) ...
            float finalMultiplier;
            if (!float.TryParse(speedMultiplierInput, NumberStyles.Float, CultureInfo.InvariantCulture, out finalMultiplier)) finalMultiplier = 1.0f;
            finalMultiplier = Mathf.Clamp(finalMultiplier, LowSpeedMultiplierLimit, HighSpeedMultiplierLimit);
            float deltaTime = finalMultiplier / 60.0f;
            float minDeltaTime = LowSpeedMultiplierLimit / 60.0f;
            float maxDeltaTime = HighSpeedMultiplierLimit / 60.0f;
            deltaTime = Mathf.Clamp(deltaTime, minDeltaTime, maxDeltaTime);
            GameStateManager.SetDeltaTime(deltaTime);
            showConfigurationWindow = false; isPaused = false; Time.timeScale = 1; GameStateManager.SetPauseState(isPaused);
            Left_GUI leftGUI = FindFirstObjectByType<Left_GUI>(); if (leftGUI != null) leftGUI.StartSimulation();
        }
        GUILayout.FlexibleSpace();
        GUILayout.EndHorizontal();

        GUILayout.Space(20); // Adjusted padding at the bottom
        GUILayout.EndVertical();

        // No need to restore styles as we used dedicated ones
        // GUI.DragWindow(...); // Optional
    }

    // Generates the text explaining the time relationship (no changes needed here)
    private string GetTimeRelationshipText(float speedMultiplier)
    {
        TimeSpan simulatedTimeSpan = TimeSpan.FromSeconds(speedMultiplier);
        StringBuilder timeString = new StringBuilder();
        if (simulatedTimeSpan.TotalHours >= 1) { timeString.AppendFormat("{0} hour{1} ", (int)simulatedTimeSpan.TotalHours, (int)simulatedTimeSpan.TotalHours == 1 ? "" : "s"); }
        if (simulatedTimeSpan.Minutes > 0 || timeString.Length > 0) { timeString.AppendFormat("{0} minute{1} ", simulatedTimeSpan.Minutes, simulatedTimeSpan.Minutes == 1 ? "" : "s"); }
        // Ensure seconds always show if it's the only unit or needed for precision
        if (timeString.Length == 0 || simulatedTimeSpan.Seconds > 0 || (simulatedTimeSpan.Minutes == 0 && simulatedTimeSpan.TotalHours < 1))
        {
             timeString.AppendFormat("{0} second{1}", simulatedTimeSpan.Seconds, simulatedTimeSpan.Seconds == 1 ? "" : "s");
        }
         if (timeString.Length == 0 && speedMultiplier == 0) { timeString.Append("0 seconds"); } // Handle exactly zero case
        return $"Real Time -> Simulated Time\n1 second -> {timeString.ToString()}";
    }


    // Displays the camera control help box (Uses standard styles)
    private void DisplayControlsGUI()
    {
        Rect rect = new Rect(Screen.width - 200, Screen.height - 240, 180, 190);
        // Use standard windowStyle for this box
        GUI.Box(rect, "Camera Controls", windowStyle);

        // Use standard controlsLabelStyle (or just labelStyle) for text
        GUILayout.BeginArea(new Rect(Screen.width - 190, Screen.height - 215, 170, 180));
        GUILayout.Label("WASD: Move", controlsLabelStyle);
        GUILayout.Label("Space: Ascend", controlsLabelStyle);
        GUILayout.Label("Ctrl: Descend", controlsLabelStyle);
        GUILayout.Label("Right Click: Rotate", controlsLabelStyle);
        GUILayout.Label("Mouse Wheel: Zoom", controlsLabelStyle);
        GUILayout.Label("C: Toggle Top-Down View", controlsLabelStyle);
        GUILayout.Label("FPS Button: Toggle Limit", controlsLabelStyle);
        GUILayout.EndArea();
    }

    // --- Other Methods (TogglePause, ToggleFPSLimit, RestartSimulation, ExitSimulation, AdvanceOneFrame, AdvanceOneFrameCoroutine) ---
    // --- No changes needed in these methods ---
     private void TogglePause() { isPaused = !isPaused; Time.timeScale = isPaused ? 0 : 1; GameStateManager.SetPauseState(isPaused); }
     private void ToggleFPSLimit() { currentFPSIndex = (currentFPSIndex + 1) % fpsLevels.Length; QualitySettings.vSyncCount = 0; Application.targetFrameRate = fpsLevels[currentFPSIndex]; }
     private void RestartSimulation() { isPaused = true; Time.timeScale = 1; GameStateManager.SetPauseState(isPaused); GameStateManager.ResetGameState(); CreatePrefabsOnClick spawner = FindFirstObjectByType<CreatePrefabsOnClick>(); if (spawner != null) spawner.ResetSimulation(); else Debug.LogWarning("Right_GUI: CreatePrefabsOnClick spawner not found in the scene."); Left_GUI leftGUI = FindFirstObjectByType<Left_GUI>(); if (leftGUI != null) leftGUI.ResetSimulation(); showConfigurationWindow = true; }
     private void ExitSimulation() {
 #if UNITY_EDITOR
         UnityEditor.EditorApplication.isPlaying = false;
 #else
         Application.Quit();
 #endif
     }
     private void AdvanceOneFrame() { if (isPaused && !isAdvancingFrame) { StartCoroutine(AdvanceOneFrameCoroutine()); } }
     private IEnumerator AdvanceOneFrameCoroutine() { isAdvancingFrame = true; isPaused = false; GameStateManager.SetPauseState(false); Time.timeScale = 1; yield return new WaitForFixedUpdate(); Time.timeScale = 0; isPaused = true; GameStateManager.SetPauseState(true); isAdvancingFrame = false; }

}