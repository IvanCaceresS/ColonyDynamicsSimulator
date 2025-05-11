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
    private static float LowSpeedMultiplierLimit = 1.0f;
    private static float HighSpeedMultiplierLimit = 2400f;
    private string speedMultiplierInput = "1.00";

    private int baseFontSize = 18;
    private int configFontSizeIncrease = 8;
    private int configTitleFontSizeIncrease = 10;

    private GUIStyle buttonStyle;
    private GUIStyle labelStyle;
    private GUIStyle windowStyle;
    private GUIStyle controlsLabelStyle;
    private GUIStyle configWindowStyle;
    private GUIStyle configLabelStyle;
    private GUIStyle configCenteredLabelStyle;
    private GUIStyle configButtonStyle;
    private GUIStyle configTextFieldStyle;
    private GUIStyle configSliderStyle;
    private GUIStyle configSliderThumbStyle;
    private GUIStyle presetButtonStyle;


    private bool stylesInitialized = false;
    private bool isAdvancingFrame = false;

    private float referenceWidth = 1920f;
    private float referenceHeight = 1080f;
    private float scaleWidth;
    private float scaleHeight;
    private float generalScale;

    void Start()
    {
        GameStateManager.OnSetupComplete += EnableGUI;
        initialSceneName = SceneManager.GetActiveScene().name;
        QualitySettings.vSyncCount = 0;
        Application.targetFrameRate = fpsLevels[currentFPSIndex];
        CalculateScaleFactors();
    }

    void OnDestroy()
    {
        GameStateManager.OnSetupComplete -= EnableGUI;
    }

    private void EnableGUI()
    {
        this.enabled = true;
    }

    void CalculateScaleFactors()
    {
        scaleWidth = Screen.width / referenceWidth;
        scaleHeight = Screen.height / referenceHeight;
        generalScale = Mathf.Min(scaleWidth, scaleHeight);
    }

    void OnGUI()
    {
        if (!GameStateManager.IsSetupComplete) return;

        CalculateScaleFactors();

        if (!stylesInitialized || Event.current.type == EventType.Layout)
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

        float controlsBtnBaseWidth = 140;
        float controlsBtnBaseHeight = 40;
        float controlsBtnWidth = Mathf.RoundToInt(controlsBtnBaseWidth * scaleWidth);
        float controlsBtnHeight = Mathf.RoundToInt(controlsBtnBaseHeight * scaleHeight);
        float controlsBtnMarginX = Mathf.RoundToInt(20 * scaleWidth);
        float controlsBtnMarginY = Mathf.RoundToInt(20 * scaleHeight);

        controlsBtnWidth = Mathf.Max(controlsBtnWidth, 120);
        controlsBtnHeight = Mathf.Max(controlsBtnHeight, 35);


        if (GUI.Button(new Rect(Screen.width - controlsBtnWidth - controlsBtnMarginX, Screen.height - controlsBtnHeight - controlsBtnMarginY, controlsBtnWidth, controlsBtnHeight), "Controls", buttonStyle))
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
        int scaledBaseFontSize = Mathf.RoundToInt(baseFontSize * scaleHeight);
        int scaledConfigContentFontSize = Mathf.RoundToInt((baseFontSize + configFontSizeIncrease) * scaleHeight);
        int scaledConfigTitleFontSize = Mathf.RoundToInt((baseFontSize + configTitleFontSizeIncrease) * scaleHeight);

        scaledBaseFontSize = Mathf.Max(scaledBaseFontSize, 12);
        scaledConfigContentFontSize = Mathf.Max(scaledConfigContentFontSize, 14);
        scaledConfigTitleFontSize = Mathf.Max(scaledConfigTitleFontSize, 16);


        buttonStyle = new GUIStyle(GUI.skin.button)
        {
            fontSize = scaledBaseFontSize,
            normal = { textColor = Color.white }
        };

        labelStyle = new GUIStyle(GUI.skin.label)
        {
            fontSize = scaledBaseFontSize,
            normal = { textColor = Color.white },
            alignment = TextAnchor.MiddleLeft
        };

        int scaledWindowFontSize = Mathf.RoundToInt((baseFontSize + 2) * scaleHeight);
        scaledWindowFontSize = Mathf.Max(scaledWindowFontSize, 14);

        windowStyle = new GUIStyle(GUI.skin.box)
        {
            fontSize = scaledWindowFontSize,
            fontStyle = FontStyle.Bold,
            alignment = TextAnchor.UpperCenter,
            normal = { textColor = Color.white }
        };


        controlsLabelStyle = new GUIStyle(labelStyle);
        controlsLabelStyle.fontSize = Mathf.Max(Mathf.RoundToInt(baseFontSize * scaleHeight), 12);


        configWindowStyle = new GUIStyle(GUI.skin.box)
        {
            fontSize = scaledConfigTitleFontSize,
            fontStyle = FontStyle.Bold,
            alignment = TextAnchor.UpperCenter,
            normal = { textColor = Color.white }
        };

        configLabelStyle = new GUIStyle(GUI.skin.label)
        {
            fontSize = scaledConfigContentFontSize,
            normal = { textColor = Color.white },
            alignment = TextAnchor.MiddleLeft
        };

        configCenteredLabelStyle = new GUIStyle(configLabelStyle)
        {
            alignment = TextAnchor.MiddleCenter
        };

        configButtonStyle = new GUIStyle(GUI.skin.button)
        {
            fontSize = scaledConfigContentFontSize,
            normal = { textColor = Color.white }
        };
        
        presetButtonStyle = new GUIStyle(configButtonStyle)
        {
            fontSize = Mathf.Max(Mathf.RoundToInt((baseFontSize + configFontSizeIncrease - 4) * scaleHeight), 12) // Un poco más pequeño para los presets
        };


        configTextFieldStyle = new GUIStyle(GUI.skin.textField)
        {
            fontSize = scaledConfigContentFontSize
        };

        configSliderStyle = new GUIStyle(GUI.skin.horizontalSlider)
        {
            fixedHeight = Mathf.Max(Mathf.RoundToInt(20 * scaleHeight), 15),
            margin = new RectOffset(4, 4, Mathf.RoundToInt(8 * scaleHeight), Mathf.RoundToInt(8 * scaleHeight))
        };
        configSliderThumbStyle = new GUIStyle(GUI.skin.horizontalSliderThumb)
        {
            fixedWidth = Mathf.Max(Mathf.RoundToInt(20 * scaleWidth), 15),
            fixedHeight = Mathf.Max(Mathf.RoundToInt(30 * scaleHeight), 20)
        };
    }

    private void DrawMainControls()
    {
        int buttonWidth = Mathf.RoundToInt(110 * scaleWidth);
        int buttonHeight = Mathf.RoundToInt(40 * scaleHeight);
        int margin = Mathf.RoundToInt(10 * generalScale);

        buttonWidth = Mathf.Max(buttonWidth, 90);
        buttonHeight = Mathf.Max(buttonHeight, 30);

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
        float windowWidthFraction = 0.3f;
        float windowHeightFraction = 0.4f; 

        float minWindowWidth = 500 * scaleWidth; 
        float minWindowHeight = 400 * scaleHeight; 

        int windowWidth = Mathf.RoundToInt(Mathf.Max(Screen.width * windowWidthFraction, minWindowWidth));
        int windowHeight = Mathf.RoundToInt(Mathf.Max(Screen.height * windowHeightFraction, minWindowHeight));

        Rect windowRect = new Rect((Screen.width - windowWidth) / 2, (Screen.height - windowHeight) / 2, windowWidth, windowHeight);

        GUI.Window(0, windowRect, ConfigurationWindowContent, "Simulation Configuration", configWindowStyle);
    }

    private void ConfigurationWindowContent(int windowID)
    {
        GUILayout.BeginVertical();
        GUILayout.Space(Mathf.RoundToInt(30 * scaleHeight));

        GUILayout.BeginHorizontal();
        GUILayout.FlexibleSpace();
        GUILayout.Label($"Select Simulation Speed ({LowSpeedMultiplierLimit:F1}x - {HighSpeedMultiplierLimit:F0}x):", configLabelStyle, GUILayout.Width(Mathf.RoundToInt(500 * scaleWidth)));
        GUILayout.FlexibleSpace();
        GUILayout.EndHorizontal();

        GUILayout.Space(Mathf.RoundToInt(15 * scaleHeight));

        GUILayout.BeginHorizontal();
        GUILayout.FlexibleSpace();

        GUILayout.Label("Speed:", configLabelStyle, GUILayout.Width(Mathf.RoundToInt(100 * scaleWidth)));
        speedMultiplierInput = GUILayout.TextField(speedMultiplierInput, configTextFieldStyle, GUILayout.Width(Mathf.RoundToInt(100 * scaleWidth)));

        float parsedSpeedMultiplier;
        if (!float.TryParse(speedMultiplierInput, NumberStyles.Float, CultureInfo.InvariantCulture, out parsedSpeedMultiplier)) { parsedSpeedMultiplier = 1.0f; }
        parsedSpeedMultiplier = Mathf.Clamp(parsedSpeedMultiplier, LowSpeedMultiplierLimit, HighSpeedMultiplierLimit);

        parsedSpeedMultiplier = GUILayout.HorizontalSlider(parsedSpeedMultiplier, LowSpeedMultiplierLimit, HighSpeedMultiplierLimit, configSliderStyle, configSliderThumbStyle, GUILayout.MinWidth(Mathf.RoundToInt(220 * scaleWidth)));
        speedMultiplierInput = parsedSpeedMultiplier.ToString("F2", CultureInfo.InvariantCulture);

        GUILayout.FlexibleSpace();
        GUILayout.EndHorizontal();

        GUILayout.Space(Mathf.RoundToInt(15 * scaleHeight));

        GUILayout.BeginHorizontal();
        GUILayout.FlexibleSpace();
        float presetButtonWidth = Mathf.RoundToInt(110 * scaleWidth);
        float presetButtonHeight = Mathf.RoundToInt(40 * scaleHeight);

        if (GUILayout.Button("300x", presetButtonStyle, GUILayout.Width(presetButtonWidth), GUILayout.Height(presetButtonHeight))) { speedMultiplierInput = "300.00"; }
        GUILayout.FlexibleSpace();
        if (GUILayout.Button("600x", presetButtonStyle, GUILayout.Width(presetButtonWidth), GUILayout.Height(presetButtonHeight))) { speedMultiplierInput = "600.00"; }
        GUILayout.FlexibleSpace();
        if (GUILayout.Button("1200x", presetButtonStyle, GUILayout.Width(presetButtonWidth), GUILayout.Height(presetButtonHeight))) { speedMultiplierInput = "1200.00"; }
        GUILayout.FlexibleSpace();
        if (GUILayout.Button("2400x", presetButtonStyle, GUILayout.Width(presetButtonWidth), GUILayout.Height(presetButtonHeight))) { speedMultiplierInput = "2400.00"; }
        GUILayout.FlexibleSpace();
        GUILayout.EndHorizontal();


        GUILayout.Space(Mathf.RoundToInt(25 * scaleHeight));
        GUILayout.BeginHorizontal();
        GUILayout.FlexibleSpace();
        GUILayout.Label(GetTimeRelationshipText(parsedSpeedMultiplier), configCenteredLabelStyle, GUILayout.Width(Mathf.RoundToInt(520 * scaleWidth)));
        GUILayout.FlexibleSpace();
        GUILayout.EndHorizontal();

        GUILayout.FlexibleSpace();

        GUILayout.BeginHorizontal();
        GUILayout.FlexibleSpace();
        if (GUILayout.Button("Start Simulation", configButtonStyle, GUILayout.Width(Mathf.RoundToInt(500 * scaleWidth)), GUILayout.Height(Mathf.RoundToInt(50 * scaleHeight))))
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
        GUILayout.Space(Mathf.RoundToInt(25 * scaleHeight));
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
        return $"Real Time -> Simulated Time\n1 second -> {timeString.ToString().Trim()}\nat 60 FPS";
    }

    private void DisplayControlsGUI()
    {
        float boxBaseWidth = 240;
        float boxBaseHeight = 250;

        float boxWidth = Mathf.RoundToInt(boxBaseWidth * scaleWidth);
        float boxHeight = Mathf.RoundToInt(boxBaseHeight * scaleHeight);
        float boxMarginX = Mathf.RoundToInt(20 * scaleWidth);
        float boxMarginY = Mathf.RoundToInt(20 * scaleHeight) + Mathf.RoundToInt(40 * scaleHeight) + Mathf.RoundToInt(10 * scaleHeight) ;

        boxWidth = Mathf.Max(boxWidth, 200);
        boxHeight = Mathf.Max(boxHeight, 180);


        Rect boxRect = new Rect(Screen.width - boxWidth - boxMarginX, Screen.height - boxHeight - boxMarginY, boxWidth, boxHeight);
        GUI.Box(boxRect, "Camera Controls", windowStyle);

        float areaPaddingX = Mathf.RoundToInt(10 * scaleWidth);
        float areaPaddingY = Mathf.RoundToInt(windowStyle.fontSize + 10 * scaleHeight) ;

        Rect areaRect = new Rect(
            boxRect.x + areaPaddingX,
            boxRect.y + areaPaddingY,
            boxRect.width - (2 * areaPaddingX),
            boxRect.height - areaPaddingY - (areaPaddingX / 2)
        );

        GUILayout.BeginArea(areaRect);
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
    private void RestartSimulation() { isPaused = true; Time.timeScale = 1; GameStateManager.SetPauseState(isPaused); GameStateManager.ResetGameState(); CreatePrefabsOnClick spawner = FindFirstObjectByType<CreatePrefabsOnClick>(); if (spawner != null) spawner.ResetSimulation(); Left_GUI leftGUI = FindFirstObjectByType<Left_GUI>(); if (leftGUI != null) leftGUI.ResetSimulation(); showConfigurationWindow = true; }
    private void ExitSimulation()
    {
#if UNITY_EDITOR
        UnityEditor.EditorApplication.isPlaying = false;
#else
        Application.Quit();
#endif
    }
    private void AdvanceOneFrame() { if (isPaused && !isAdvancingFrame) { StartCoroutine(AdvanceOneFrameCoroutine()); } }
    private IEnumerator AdvanceOneFrameCoroutine() { isAdvancingFrame = true; isPaused = false; GameStateManager.SetPauseState(false); Time.timeScale = 1; yield return new WaitForFixedUpdate(); Time.timeScale = 0; isPaused = true; GameStateManager.SetPauseState(true); isAdvancingFrame = false; }
}
