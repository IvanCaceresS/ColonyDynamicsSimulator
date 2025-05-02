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

    #region Unity Lifecycle Methods

    private void Awake()
    {
        currentPersistentPath = Application.persistentDataPath;
        Debug.Log($"{LogTag} Awake: Script initializing. persistentDataPath = '{currentPersistentPath}'");
    }

    private void Start()
    {
        Debug.Log($"{LogTag} Start: Starting setup...");
        ReadSimulationNameFromFile();
        leftGui = FindFirstObjectByType<Left_GUI>();
        if (leftGui == null)
        {
            Debug.LogError($"{LogTag} Start: {nameof(Left_GUI)} not found. Logger disabled.");
            enabled = false; return;
        }
        Debug.Log($"{LogTag} Start: {nameof(Left_GUI)} found.");
        if (!SetupLogFilePath())
        {
             enabled = false; return;
        }

        if (!Application.isEditor)
        {
            Debug.Log($"{LogTag} Start: In Build mode, starting coroutine to wait for {nameof(Left_GUI)}...");
            StartCoroutine(WaitForOrganismNamesAndStartLogging());
        }
        else
        {
            Debug.Log($"{LogTag} Start: In Editor mode.");
        }
        Debug.Log($"{LogTag} Start: Setup completed.");
    }

    private void Update()
    {
        if (!isLogging) return;

        try
        {
             bool isPaused = GameStateManager.IsPaused;
             if (!isPaused)
             {
                 string logLine = GenerateLogLine();
                 if (!string.IsNullOrEmpty(logLine))
                 {
                     logBuffer.Add(logLine);
                 }
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
    }

    private void OnGUI()
    {
        if (Application.isEditor)
        {
            Rect buttonRect = new Rect(10, Screen.height - 50, 250, 40);
            string buttonText = isLogging ? "Stop Logging (Batch)" : "Start Logging (Batch)";
            if (GUI.Button(buttonRect, buttonText))
            {
                if (isLogging) { StopLogging(); }
                else {
                    bool guiReady = leftGui != null && leftGui.enabled;
                    bool namesReady = leftGui?.OrganismNames != null && leftGui.OrganismNames.Any();
                    if (guiReady && namesReady) { StartLogging(); }
                    else { Debug.LogWarning($"{LogTag} OnGUI: Cannot start. {nameof(Left_GUI)} is not ready (Enabled: {guiReady}, Names Loaded: {namesReady})."); }
                }
            }
        }
    }

    private void OnApplicationQuit()
    {
        Debug.Log($"{LogTag} OnApplicationQuit: Application closing.");
        if (isLogging && logBuffer.Count > 0)
        {
            Debug.Log($"{LogTag} OnApplicationQuit: Writing remaining buffer ({logBuffer.Count} lines)...");
            WriteBufferToFile();
        }
        isLogging = false;
    }

     private void OnDestroy()
     {
         Debug.Log($"{LogTag} OnDestroy: Logger object destroyed.");
         if (isLogging && logBuffer.Count > 0)
         {
             Debug.LogWarning($"{LogTag} OnDestroy: Destroyed while logging with pending buffer. Final save...");
             WriteBufferToFile();
         }
         isLogging = false;
     }

    #endregion

    #region Logging Control Methods

    private IEnumerator WaitForOrganismNamesAndStartLogging()
    {
        Debug.Log($"{LogTag} {nameof(WaitForOrganismNamesAndStartLogging)}: Started. Waiting for conditions...");
        while (true)
        {
             bool guiExists = leftGui != null;
             bool guiEnabled = guiExists && leftGui.enabled;
             bool namesAvailable = guiEnabled && leftGui?.OrganismNames != null && leftGui.OrganismNames.Any();

             if (guiExists && guiEnabled && namesAvailable)
             {
                 Debug.Log($"{LogTag} {nameof(WaitForOrganismNamesAndStartLogging)}: Conditions met! Starting logging.");
                 StartLogging();
                 yield break;
             }
             yield return new WaitForSeconds(0.2f);
        }
    }

    public void StartLogging()
    {
        Debug.Log($"{LogTag} {nameof(StartLogging)}: Attempting to start logging...");
        if (isLogging) { Debug.LogWarning($"{LogTag} {nameof(StartLogging)}: Already active."); return; }

        if (leftGui == null || !leftGui.enabled) { Debug.LogError($"{LogTag} {nameof(StartLogging)}: Failed - {nameof(Left_GUI)} not available."); return; }
        if (leftGui.OrganismNames == null || !leftGui.OrganismNames.Any()) { Debug.LogError($"{LogTag} {nameof(StartLogging)}: Failed - {nameof(Left_GUI)} has no organism names."); return; }
        if (string.IsNullOrEmpty(logFilePath)) { Debug.LogError($"{LogTag} {nameof(StartLogging)}: Failed - File path not configured."); return; }

        if (File.Exists(logFilePath))
        {
            Debug.Log($"{LogTag} {nameof(StartLogging)}: Previous file exists at '{logFilePath}'. Attempting to delete...");
            try { File.Delete(logFilePath); Debug.Log($"{LogTag} {nameof(StartLogging)}: Previous file deleted."); }
            catch (Exception ex) { Debug.LogError($"{LogTag} {nameof(StartLogging)}: Error deleting '{logFilePath}': {ex.ToString()}. Aborting start."); return; }
        } else {
            Debug.Log($"{LogTag} {nameof(StartLogging)}: No previous file exists at '{logFilePath}'.");
        }

        isLogging = true;
        logBuffer.Clear();
        lastBatchWriteTime = Time.time;
        headerWritten = false;

        Debug.Log($"{LogTag} {nameof(StartLogging)}: *** Logging started ***. Saving to: {logFilePath}. Header will be written with the first data batch.");
    }

    public void StopLogging()
    {
       Debug.Log($"{LogTag} {nameof(StopLogging)}: Attempting to stop logging...");
       if (!isLogging) { Debug.LogWarning($"{LogTag} {nameof(StopLogging)}: Already stopped."); return; }

       isLogging = false;
       WriteBufferToFile();
       Debug.Log($"{LogTag} {nameof(StopLogging)}: *** Logging finished ***. File: {logFilePath}");
    }

    #endregion

    #region Data Handling and File IO

    private void ReadSimulationNameFromFile()
    {
        string simulationLoadedFile = Path.Combine(Application.streamingAssetsPath, "simulation_loaded.txt");
        Debug.Log($"{LogTag} {nameof(ReadSimulationNameFromFile)}: Looking for name in '{simulationLoadedFile}'");
        try {
             if (File.Exists(simulationLoadedFile)) {
                 string loadedName = File.ReadAllText(simulationLoadedFile).Trim();
                 if (!string.IsNullOrEmpty(loadedName)) {
                     simulationName = loadedName;
                     Debug.Log($"{LogTag} {nameof(ReadSimulationNameFromFile)}: Name loaded: '{simulationName}'");
                 } else {
                     Debug.LogWarning($"{LogTag} {nameof(ReadSimulationNameFromFile)}: File empty. Using '{simulationName}'.");
                 }
             } else {
                 Debug.LogWarning($"{LogTag} {nameof(ReadSimulationNameFromFile)}: File not found. Using '{simulationName}'.");
             }
        } catch (Exception ex) {
             Debug.LogError($"{LogTag} {nameof(ReadSimulationNameFromFile)}: Error reading: {ex.ToString()}. Using '{simulationName}'.");
             simulationName = "DefaultSimulation";
        }
    }

    private bool SetupLogFilePath()
    {
        Debug.Log($"{LogTag} {nameof(SetupLogFilePath)}: Configuring paths...");
        try {
            if (string.IsNullOrEmpty(currentPersistentPath)) {
                 Debug.LogError($"{LogTag} {nameof(SetupLogFilePath)}: persistentDataPath is null."); return false;
            }
            Debug.Log($"{LogTag} {nameof(SetupLogFilePath)}: Using base: '{currentPersistentPath}'");
            simulationFolderPath = Path.Combine(currentPersistentPath, LogSubfolder, simulationName);
            Debug.Log($"{LogTag} {nameof(SetupLogFilePath)}: Log folder path: '{simulationFolderPath}'");
            if (!Directory.Exists(simulationFolderPath)) {
                Debug.Log($"{LogTag} {nameof(SetupLogFilePath)}: Creating directory...");
                try { Directory.CreateDirectory(simulationFolderPath); Debug.Log($"{LogTag} {nameof(SetupLogFilePath)}: Directory created."); }
                catch (Exception dex) { Debug.LogError($"{LogTag} {nameof(SetupLogFilePath)}: ERROR creating directory '{simulationFolderPath}': {dex.ToString()}"); return false; }
            } else { Debug.Log($"{LogTag} {nameof(SetupLogFilePath)}: Directory already exists."); }
            logFilePath = Path.Combine(simulationFolderPath, CsvFileName);
            Debug.Log($"{LogTag} {nameof(SetupLogFilePath)}: CSV file path: '{logFilePath}'");
            return true;
        } catch (Exception ex) {
            Debug.LogError($"{LogTag} {nameof(SetupLogFilePath)}: Critical error configuring paths: {ex.ToString()}");
            logFilePath = null; simulationFolderPath = null;
            return false;
        }
    }

    private string GenerateLogLine()
    {
        if (leftGui == null || leftGui.OrganismNames == null) return null;

        try {
             StringBuilder csvLine = new StringBuilder();
             string timestamp = DateTime.Now.ToString("dd-MM-yyyy HH:mm:ss", CultureInfo.InvariantCulture);
             csvLine.Append(timestamp);
             csvLine.Append(CsvSeparator).Append(leftGui.cachedFPS.ToString("F2", CultureInfo.InvariantCulture));
             csvLine.Append(CsvSeparator).Append(leftGui.cachedRealTime.ToString("F2", CultureInfo.InvariantCulture));
             csvLine.Append(CsvSeparator).Append(leftGui.cachedSimulatedTime.ToString("F2", CultureInfo.InvariantCulture));
             csvLine.Append(CsvSeparator).Append(GameStateManager.DeltaTime.ToString("F4", CultureInfo.InvariantCulture));
             csvLine.Append(CsvSeparator).Append(leftGui.cachedFrameCount.ToString(CultureInfo.InvariantCulture));
             csvLine.Append(CsvSeparator).Append(GameStateManager.IsPaused ? "Yes" : "No");

             if (leftGui.OrganismNames.Any() && leftGui.entityCounts != null) {
                 foreach (var orgName in leftGui.OrganismNames) {
                     leftGui.entityCounts.TryGetValue(orgName, out int count);
                     csvLine.Append(CsvSeparator).Append(count.ToString(CultureInfo.InvariantCulture));
                 }
             }

             return csvLine.ToString();
        } catch (Exception ex) {
             Debug.LogError($"{LogTag} {nameof(GenerateLogLine)}: Error generating line: {ex.ToString()}");
             return null;
        }
    }

    private void WriteBufferToFile()
    {
        if (!headerWritten)
        {
            Debug.Log($"{LogTag} {nameof(WriteBufferToFile)}: Header not yet written. Attempting to write header...");
            if (WriteCSVHeader())
            {
                headerWritten = true;
                Debug.Log($"{LogTag} {nameof(WriteBufferToFile)}: Header written successfully.");
            }
            else
            {
                Debug.LogError($"{LogTag} {nameof(WriteBufferToFile)}: Header write failed. Buffer data will not be written to prevent corruption.");
                return;
            }
        }

        if (logBuffer == null || logBuffer.Count == 0) {
             return;
        }
        if (string.IsNullOrEmpty(logFilePath)) {
             Debug.LogError($"{LogTag} {nameof(WriteBufferToFile)}: Attempted to write buffer but file path is invalid.");
             logBuffer.Clear();
             return;
         }

        List<string> bufferToWrite = new List<string>(logBuffer);
        logBuffer.Clear();

        try
        {
            string batchContent = string.Join(Environment.NewLine, bufferToWrite) + Environment.NewLine;
            File.AppendAllText(logFilePath, batchContent, System.Text.Encoding.UTF8);
            lastBatchWriteTime = Time.time;
        }
        catch (Exception ex)
        {
            Debug.LogError($"{LogTag} {nameof(WriteBufferToFile)}: Error writing buffer to '{logFilePath}': {ex.ToString()}");
        }
    }

    private bool WriteCSVHeader()
    {
        Debug.Log($"{LogTag} {nameof(WriteCSVHeader)}: Building and writing header...");
        if (leftGui == null) { Debug.LogError($"{LogTag} {nameof(WriteCSVHeader)}: Failed - {nameof(Left_GUI)} is null."); return false; }
        if (leftGui.OrganismNames == null || !leftGui.OrganismNames.Any()) {
            Debug.LogError($"{LogTag} {nameof(WriteCSVHeader)}: Failed - {nameof(Left_GUI)}.OrganismNames is null or empty at this time. Cannot write complete header.");
            return false;
        }
        if (string.IsNullOrEmpty(logFilePath)) { Debug.LogError($"{LogTag} {nameof(WriteCSVHeader)}: Failed - File path not configured."); return false; }

        List<string> headers = new List<string> { "Timestamp", "FPS", "RealTime", "SimulatedTime", "DeltaTime", "FrameCount", "Paused" }; // Changed from Spanish
        headers.AddRange(leftGui.OrganismNames);
        string headerLine = string.Join(CsvSeparator, headers) + Environment.NewLine;
        Debug.Log($"{LogTag} {nameof(WriteCSVHeader)}: Header to write: {headerLine.Trim()}");

        try
        {
            File.WriteAllText(logFilePath, headerLine, System.Text.Encoding.UTF8);
            Debug.Log($"{LogTag} {nameof(WriteCSVHeader)}: Header written successfully to '{logFilePath}'.");
            return true;
        }
        catch (Exception ex)
        {
            Debug.LogError($"{LogTag} {nameof(WriteCSVHeader)}: ERROR writing header to '{logFilePath}'!: {ex.ToString()}");
            return false;
        }
    }

    #endregion
}