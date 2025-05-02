using UnityEngine;
using UnityEngine.SceneManagement;
using System.Collections;
using System;
using System.Text;
using System.Globalization;

public class Right_GUI : MonoBehaviour
{
    public bool isPaused = true;
    private bool showConfigurationWindow = true;
    private bool showControls = false;
    private int[] fpsLevels = { 60, 144, 500, 1000, -1 };
    private int currentFPSIndex = 0;
    private string initialSceneName;
    private static float LowSpeedMultiplierLimit = 0.6f;
    private static float HighSpeedMultiplierLimit = 2400f;
    private string speedMultiplierInput = "1.00";
    private int baseFontSize = 12;
    private int configFontSizeIncrease = 6;
    private int configTitleFontSizeIncrease = 8;

    private GUIStyle buttonStyle;
    private GUIStyle labelStyle;
    private GUIStyle windowStyle;
    private GUIStyle controlsLabelStyle;
    private GUIStyle configWindowStyle;
    private GUIStyle configLabelStyle;
    private GUIStyle configCenteredLabelStyle;
    private GUIStyle configButtonStyle;
    private GUIStyle configTextFieldStyle;

    private bool stylesInitialized = false;

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

        if (!stylesInitialized && Event.current.type == EventType.Layout)
        {
            InitializeStyles();
            stylesInitialized = true;
        }
        if (!stylesInitialized) return;


        if (showConfigurationWindow)
        {
            ShowConfigurationWindow();
        }
        else
        {
            DrawMainControls();
        }

        if (GUI.Button(new Rect(Screen.width - 120, Screen.height - 40, 100, 30), "Controls", buttonStyle))
        {
            showControls = !showControls;
        }

        if (showControls)
        {
            DisplayControlsGUI();
        }
    }

    private void InitializeStyles()
    {
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

        windowStyle = new GUIStyle(GUI.skin.box)
        {
            fontSize = baseFontSize + 2,
            fontStyle = FontStyle.Bold,
            alignment = TextAnchor.UpperCenter,
            normal = { textColor = Color.white }
        };

        controlsLabelStyle = new GUIStyle(labelStyle);

        int configContentFontSize = baseFontSize + configFontSizeIncrease;
        int configTitleFontSize = baseFontSize + configTitleFontSizeIncrease;

        configWindowStyle = new GUIStyle(GUI.skin.box)
        {
            fontSize = configTitleFontSize,
            fontStyle = FontStyle.Bold,
            alignment = TextAnchor.UpperCenter,
            normal = { textColor = Color.white }
        };

        configLabelStyle = new GUIStyle(GUI.skin.label)
        {
            fontSize = configContentFontSize,
            normal = { textColor = Color.white },
            alignment = TextAnchor.MiddleLeft
        };

        configCenteredLabelStyle = new GUIStyle(configLabelStyle)
        {
            alignment = TextAnchor.MiddleCenter
        };

        configButtonStyle = new GUIStyle(GUI.skin.button)
        {
            fontSize = configContentFontSize,
            normal = { textColor = Color.white }
        };

        configTextFieldStyle = new GUIStyle(GUI.skin.textField)
        {
             fontSize = configContentFontSize 
        };

        Debug.Log("GUI Styles Initialized");
    }

    private void DrawMainControls()
    {
        int buttonWidth = 80;
        int buttonHeight = 30;
        int margin = 10;
        int startX = Screen.width - buttonWidth - margin;
        int startY = margin;
        int buttonIndex = 0;

        string fpsText = fpsLevels[currentFPSIndex] == -1 ? "∞" : fpsLevels[currentFPSIndex].ToString();
        if (GUI.Button(new Rect(startX, startY + buttonIndex * (buttonHeight + margin), buttonWidth, buttonHeight), $"FPS: {fpsText}", buttonStyle)) { ToggleFPSLimit(); } buttonIndex++;
        if (GUI.Button(new Rect(startX, startY + buttonIndex * (buttonHeight + margin), buttonWidth, buttonHeight), isPaused ? "Resume" : "Pause", buttonStyle)) { TogglePause(); } buttonIndex++;
        if (GUI.Button(new Rect(startX, startY + buttonIndex * (buttonHeight + margin), buttonWidth, buttonHeight), "Restart", buttonStyle)) { RestartSimulation(); } buttonIndex++;
        if (GUI.Button(new Rect(startX, startY + buttonIndex * (buttonHeight + margin), buttonWidth, buttonHeight), "Exit", buttonStyle)) { ExitSimulation(); } buttonIndex++;
        if (isPaused) { if (GUI.Button(new Rect(startX, startY + buttonIndex * (buttonHeight + margin), buttonWidth, buttonHeight), "+1 Frame", buttonStyle)) { AdvanceOneFrame(); } buttonIndex++; }
    }


    private void ShowConfigurationWindow()
    {
        int windowWidth = 525;
        int windowHeight = 270;
        Rect windowRect = new Rect((Screen.width - windowWidth) / 2, (Screen.height - windowHeight) / 2, windowWidth, windowHeight);

        GUI.Window(0, windowRect, ConfigurationWindowContent, "Simulation Configuration", configWindowStyle);
    }

    private void ConfigurationWindowContent(int windowID)
    {
        GUILayout.BeginVertical();
        GUILayout.Space(30);

        GUILayout.BeginHorizontal();
        GUILayout.FlexibleSpace();
        GUILayout.Label($"Select Simulation Speed ({LowSpeedMultiplierLimit:F1}x - {HighSpeedMultiplierLimit:F0}x):", configLabelStyle, GUILayout.Width(500));
        GUILayout.FlexibleSpace();
        GUILayout.EndHorizontal();

        GUILayout.Space(10);

        GUILayout.BeginHorizontal();
        GUILayout.FlexibleSpace();

        GUILayout.Label("Speed:", configLabelStyle, GUILayout.Width(85));

        speedMultiplierInput = GUILayout.TextField(speedMultiplierInput, configTextFieldStyle, GUILayout.Width(85));

        float parsedSpeedMultiplier;
        if (!float.TryParse(speedMultiplierInput, NumberStyles.Float, CultureInfo.InvariantCulture, out parsedSpeedMultiplier)) { parsedSpeedMultiplier = 1.0f; }
        parsedSpeedMultiplier = Mathf.Clamp(parsedSpeedMultiplier, LowSpeedMultiplierLimit, HighSpeedMultiplierLimit);
        parsedSpeedMultiplier = GUILayout.HorizontalSlider(parsedSpeedMultiplier, LowSpeedMultiplierLimit, HighSpeedMultiplierLimit, GUILayout.Width(280)); 
        speedMultiplierInput = parsedSpeedMultiplier.ToString("F2", CultureInfo.InvariantCulture);

        GUILayout.FlexibleSpace();
        GUILayout.EndHorizontal();

        GUILayout.Space(20);
        GUILayout.BeginHorizontal();
        GUILayout.FlexibleSpace();
        GUILayout.Label(GetTimeRelationshipText(parsedSpeedMultiplier), configCenteredLabelStyle, GUILayout.Width(500));
        GUILayout.FlexibleSpace();
        GUILayout.EndHorizontal();
        GUILayout.FlexibleSpace();
        GUILayout.BeginHorizontal();
        GUILayout.FlexibleSpace();
        if (GUILayout.Button("Start Simulation", configButtonStyle, GUILayout.Width(480), GUILayout.Height(45)))
        {
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
        GUILayout.Space(20);
        GUILayout.EndVertical();
    }

    private string GetTimeRelationshipText(float speedMultiplier)
    {
        TimeSpan simulatedTimeSpan = TimeSpan.FromSeconds(speedMultiplier);
        StringBuilder timeString = new StringBuilder();
        if (simulatedTimeSpan.TotalHours >= 1) { timeString.AppendFormat("{0} hour{1} ", (int)simulatedTimeSpan.TotalHours, (int)simulatedTimeSpan.TotalHours == 1 ? "" : "s"); }
        if (simulatedTimeSpan.Minutes > 0 || timeString.Length > 0) { timeString.AppendFormat("{0} minute{1} ", simulatedTimeSpan.Minutes, simulatedTimeSpan.Minutes == 1 ? "" : "s"); }
        if (timeString.Length == 0 || simulatedTimeSpan.Seconds > 0 || (simulatedTimeSpan.Minutes == 0 && simulatedTimeSpan.TotalHours < 1))
        {
             timeString.AppendFormat("{0} second{1}", simulatedTimeSpan.Seconds, simulatedTimeSpan.Seconds == 1 ? "" : "s");
        }
         if (timeString.Length == 0 && speedMultiplier == 0) { timeString.Append("0 seconds"); }
        return $"Real Time -> Simulated Time\n1 second -> {timeString.ToString()}";
    }

    private void DisplayControlsGUI()
    {
        Rect rect = new Rect(Screen.width - 200, Screen.height - 240, 180, 190);
        GUI.Box(rect, "Camera Controls", windowStyle);

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