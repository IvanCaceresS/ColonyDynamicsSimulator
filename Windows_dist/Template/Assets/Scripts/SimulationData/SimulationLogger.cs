using UnityEngine;
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Globalization;
using System.Linq;

public class SimulationLogger : MonoBehaviour
{
    private const string LogTag = "[SimulationLogger]";
    private const string LogSubfolder = "SimulationLoggerData";
    private const string CsvSeparator = ";";
    private const string CsvFileName = "SimulationStats.csv";
    private const int MaxBufferSize = 100;
    private const float BatchWriteInterval = 1.0f;

    [Tooltip("Base name for the simulation if not loaded from 'simulation_loaded.txt'.")]
    [SerializeField]
    private string simulationName = "DefaultSimulation";
    private string logFilePath;
    private string simulationFolderPath;
    private bool isLogging = false;
    private Left_GUI leftGui;
    private List<string> logBuffer = new List<string>();
    private float lastBatchWriteTime = 0f;
    private string currentPersistentPath;
    private bool headerWritten = false;
    private List<string> cachedOrganismNamesForHeader;
    private bool wasSetupCompletedLastFrame = false;
    private GUIStyle editorButtonStyle;

    private void Awake()
    {
        currentPersistentPath = Application.persistentDataPath;
    }

    private void Start()
    {
        ReadSimulationNameFromFile();
        leftGui = FindFirstObjectByType<Left_GUI>();
        if (leftGui == null)
        {
            enabled = false; return;
        }
        if (!SetupLogFilePath())
        {
            enabled = false; return;
        }

        wasSetupCompletedLastFrame = GameStateManager.IsSetupComplete;

        if (Application.isEditor)
        {
            InitializeEditorButtonStyle();
        }

        if (!Application.isEditor && GameStateManager.IsSetupComplete)
        {
            StartCoroutine(WaitForOrganismNamesAndStartLogging());
        }
        else if (!GameStateManager.IsSetupComplete)
        {
            HandleSetupBecameFalse();
        }
    }
    
    private void InitializeEditorButtonStyle()
    {
        editorButtonStyle = new GUIStyle(GUI.skin.button);
        float referenceHeight = 1080f;
        float scaleHeight = Screen.height / referenceHeight;
        int baseEditorButtonFontSize = 16;
        editorButtonStyle.fontSize = Mathf.Max(Mathf.RoundToInt(baseEditorButtonFontSize * scaleHeight), 12);
    }


    private void Update()
    {
        bool isSetupNow = GameStateManager.IsSetupComplete;

        if (!isSetupNow && wasSetupCompletedLastFrame)
        {
            if (isLogging)
            {
                StopLogging();
            }
            HandleSetupBecameFalse();
        }
        else if (isSetupNow && !wasSetupCompletedLastFrame && !Application.isEditor)
        {
            StartCoroutine(WaitForOrganismNamesAndStartLogging());
        }


        if (!isLogging || !isSetupNow || GameStateManager.IsPaused)
        {
            wasSetupCompletedLastFrame = isSetupNow;
            return;
        }

        try
        {
            string logLine = GenerateLogLine();
            if (!string.IsNullOrEmpty(logLine))
            {
                logBuffer.Add(logLine);
            }

            if (logBuffer.Count >= MaxBufferSize || (Time.time - lastBatchWriteTime >= BatchWriteInterval && logBuffer.Count > 0) )
            {
                WriteBufferToFile();
            }
        }
        catch (Exception ex)
        {
            Debug.LogError($"{LogTag} Update: Unexpected error: {ex.ToString()}");
        }
        wasSetupCompletedLastFrame = isSetupNow;
    }

    private void OnGUI()
    {
        if (Application.isEditor && GameStateManager.IsSetupComplete)
        {
            if (editorButtonStyle == null) 
            {
                InitializeEditorButtonStyle();
            }

            Rect buttonRect = new Rect(10, Screen.height - 60, 280, 50);
            string buttonText = isLogging ? "Stop Logging" : "Start Logging";
            
            if (GUI.Button(buttonRect, buttonText, editorButtonStyle))
            {
                if (isLogging) { StopLogging(); }
                else {
                    bool guiReady = leftGui != null && leftGui.enabled;
                    bool namesReady = leftGui?.OrganismNames != null && leftGui.OrganismNames.Any();
                    if (guiReady && namesReady) { StartLogging(); }
                    else { Debug.LogWarning($"{LogTag} OnGUI: Cannot start. Left_GUI not ready (Enabled: {guiReady}, Names Loaded: {namesReady})."); }
                }
            }
        }
    }
    
    private void HandleSetupBecameFalse()
    {
        if (!string.IsNullOrEmpty(logFilePath) && File.Exists(logFilePath))
        {
            try
            {
                File.Delete(logFilePath);
            }
            catch (Exception ex)
            {
                Debug.LogError($"{LogTag} {nameof(HandleSetupBecameFalse)}: Error deleting log file '{logFilePath}': {ex.ToString()}");
            }
        }
        headerWritten = false;
    }


    private void OnApplicationQuit()
    {
        if (isLogging && logBuffer.Count > 0)
        {
            WriteBufferToFile();
        }
        isLogging = false;
    }

    private void OnDestroy()
    {
        if (isLogging && logBuffer.Count > 0)
        {
            WriteBufferToFile();
        }
        isLogging = false;
    }

    private IEnumerator WaitForOrganismNamesAndStartLogging()
    {
        while (true)
        {
            if (!GameStateManager.IsSetupComplete)
            {
                yield return new WaitForSeconds(0.2f); 
                continue;
            }

            bool guiExists = leftGui != null;
            bool guiEnabled = guiExists && leftGui.enabled;
            bool namesAvailable = guiEnabled && leftGui?.OrganismNames != null && leftGui.OrganismNames.Any();

            if (guiExists && guiEnabled && namesAvailable)
            {
                StartLogging();
                yield break;
            }
            yield return new WaitForSeconds(0.2f);
        }
    }

    public void StartLogging()
    {
        if (isLogging || !GameStateManager.IsSetupComplete) { return; }

        if (leftGui == null || !leftGui.enabled) { return; }
        
        IEnumerable<string> organismNames = leftGui.OrganismNames;
        if (organismNames == null || !organismNames.Any()) { return; }
        
        this.cachedOrganismNamesForHeader = organismNames.ToList();

        if (string.IsNullOrEmpty(logFilePath)) { return; }

        isLogging = true;
        logBuffer.Clear();
        lastBatchWriteTime = Time.time;
    }

    public void StopLogging()
    {
        if (!isLogging) { return; }
        WriteBufferToFile();
        isLogging = false; 
    }

    private void ReadSimulationNameFromFile()
    {
        string simulationLoadedFile = Path.Combine(Application.streamingAssetsPath, "simulation_loaded.txt");
        try {
            if (File.Exists(simulationLoadedFile)) {
                string loadedName = File.ReadAllText(simulationLoadedFile).Trim();
                if (!string.IsNullOrEmpty(loadedName)) {
                    simulationName = loadedName;
                }
            }
        } catch (Exception) {
            simulationName = "DefaultSimulation";
        }
    }

    private bool SetupLogFilePath()
    {
        try {
            if (string.IsNullOrEmpty(currentPersistentPath)) { return false; }
            simulationFolderPath = Path.Combine(currentPersistentPath, LogSubfolder, simulationName);
            if (!Directory.Exists(simulationFolderPath)) {
                Directory.CreateDirectory(simulationFolderPath);
            }
            logFilePath = Path.Combine(simulationFolderPath, CsvFileName);
            return true;
        } catch (Exception) {
            logFilePath = null; simulationFolderPath = null;
            return false;
        }
    }

    private string GenerateLogLine()
    {
        if (leftGui == null || this.cachedOrganismNamesForHeader == null) return null;

        try {
            StringBuilder csvLine = new StringBuilder(256);
            string timestamp = DateTime.Now.ToString("dd-MM-yyyy HH:mm:ss", CultureInfo.InvariantCulture);
            csvLine.Append(timestamp);
            csvLine.Append(CsvSeparator).Append(leftGui.cachedFPS.ToString("F2", CultureInfo.InvariantCulture));
            csvLine.Append(CsvSeparator).Append(leftGui.cachedRealTime.ToString("F2", CultureInfo.InvariantCulture));
            csvLine.Append(CsvSeparator).Append(leftGui.cachedSimulatedTime.ToString("F2", CultureInfo.InvariantCulture));
            csvLine.Append(CsvSeparator).Append(GameStateManager.DeltaTime.ToString("F4", CultureInfo.InvariantCulture));
            csvLine.Append(CsvSeparator).Append(leftGui.cachedFrameCount.ToString(CultureInfo.InvariantCulture));
            csvLine.Append(CsvSeparator).Append(GameStateManager.IsPaused ? "Yes" : "No");

            if (leftGui.entityCounts != null) {
                foreach (var orgName in this.cachedOrganismNamesForHeader) {
                    leftGui.entityCounts.TryGetValue(orgName, out int count);
                    csvLine.Append(CsvSeparator).Append(count.ToString(CultureInfo.InvariantCulture));
                }
            }
            return csvLine.ToString();
        } catch (Exception ex) {
            Debug.LogError($"{LogTag} {nameof(GenerateLogLine)}: Error: {ex.Message}");
            return null;
        }
    }

    private void WriteBufferToFile()
    {
        if (!headerWritten)
        {
            if (!WriteCSVHeader()) 
            {
                return; 
            }
            headerWritten = true;
        }

        if (logBuffer == null || logBuffer.Count == 0) return;
        if (string.IsNullOrEmpty(logFilePath)) {
            logBuffer.Clear();
            return;
        }

        List<string> bufferToWrite = new List<string>(logBuffer);
        logBuffer.Clear();

        try
        {
            using (StreamWriter sw = new StreamWriter(logFilePath, true, System.Text.Encoding.UTF8))
            {
                foreach (string line in bufferToWrite)
                {
                    sw.WriteLine(line);
                }
            }
            lastBatchWriteTime = Time.time;
        }
        catch (Exception ex)
        {
            Debug.LogError($"{LogTag} {nameof(WriteBufferToFile)}: Error: {ex.Message}");
        }
    }

    private bool WriteCSVHeader()
    {
        if (leftGui == null) { return false; }
        if (this.cachedOrganismNamesForHeader == null || !this.cachedOrganismNamesForHeader.Any()) {
             return false;
        }
        if (string.IsNullOrEmpty(logFilePath)) { return false; }

        List<string> headers = new List<string> { "Timestamp", "FPS", "RealTime", "SimulatedTime", "DeltaTime", "FrameCount", "Paused" };
        headers.AddRange(this.cachedOrganismNamesForHeader);
        string headerLineContent = string.Join(CsvSeparator, headers);

        try
        {
            using (StreamWriter sw = new StreamWriter(logFilePath, false, System.Text.Encoding.UTF8)) 
            {
                sw.WriteLine(headerLineContent);
            }
            return true;
        }
        catch (Exception ex)
        {
            Debug.LogError($"{LogTag} {nameof(WriteCSVHeader)}: Error: {ex.Message}");
            return false;
        }
    }
}
