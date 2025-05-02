using UnityEngine;
using System;
using System.Collections.Generic;
using Unity.Entities;
using System.Reflection;
using System.Linq;

public class Left_GUI : MonoBehaviour
{
    private const int GUIFontSize = 20;
    private const int GUIWidth = 400;
    private const int GUIHeight = 24;
    private const int GUIXPosition = 10;
    private const int GUIYPosition = 0;

    private float simulationStartTime = 0f;
    private float accumulatedRealTime = 0f;
    public float cachedRealTime = 0f;
    public float cachedSimulatedTime = 0f;
    public float cachedFPS = 0f;
    public int cachedFrameCount = 0;
    private bool hasStartedSimulation = false;


    public Dictionary<string, int> entityCounts = new Dictionary<string, int>();
    public List<Type> validComponentTypes = new List<Type>();
    private Dictionary<Type, EntityQuery> entityQueries = new Dictionary<Type, EntityQuery>();

    private GUIStyle labelStyle;

    public IEnumerable<string> OrganismNames
    {
        get
        {
            List<string> names = validComponentTypes
                .Select(t => t.Name.Replace("Component", ""))
                .ToList();
            names.Sort();
            names.Add("Organism count");
            return names;
        }
    }

    void Start()
    {
        GameStateManager.OnSetupComplete += EnableGUI;
        this.enabled = false;
        CacheValidComponentTypes();
        ResetCachedValues();
    }

    void OnDestroy()
    {
        GameStateManager.OnSetupComplete -= EnableGUI;
        foreach(var query in entityQueries.Values)
        {
            query.Dispose();
        }
        entityQueries.Clear();
    }

    private void EnableGUI()
    {
        Debug.Log("Left_GUI: Activating GUI interface.");
        this.enabled = true;
        ResetCachedValues();
    }

    void Update()
    {
        if (Time.unscaledDeltaTime > Mathf.Epsilon)
        {
            cachedFPS = 1f / Time.unscaledDeltaTime;
        }
        else
        {
            cachedFPS = 0f;
        }

        if (hasStartedSimulation)
        {
            if (!GameStateManager.IsPaused)
            {
                accumulatedRealTime += Time.deltaTime;
                cachedRealTime = accumulatedRealTime;
                cachedFrameCount++;
                cachedSimulatedTime = cachedFrameCount * GameStateManager.DeltaTime;
                UpdateEntityCounts();
            }
        }
        else
        {
            cachedRealTime = 0f;
            cachedSimulatedTime = 0f;
            cachedFrameCount = 0;
        }
    }

    public void StartSimulation()
    {
        hasStartedSimulation = true;
        simulationStartTime = Time.realtimeSinceStartup;
        accumulatedRealTime = 0f;
        cachedFrameCount = 0;
        cachedSimulatedTime = 0f;
        entityCounts.Clear();
        UpdateEntityCounts();
    }

    public void ResetSimulation()
    {
        hasStartedSimulation = false;
        ResetCachedValues();
    }

    private void ResetCachedValues()
    {
        simulationStartTime = 0f;
        accumulatedRealTime = 0f;
        cachedRealTime = 0f;
        cachedSimulatedTime = 0f;
        cachedFPS = 0f;
        cachedFrameCount = 0;
        entityCounts.Clear();
    }

    private void UpdateEntityCounts()
    {
        if (World.DefaultGameObjectInjectionWorld == null || !World.DefaultGameObjectInjectionWorld.IsCreated)
        {
             entityCounts.Clear();
             entityCounts["Organism count"] = 0;
             return;
        }
        var entityManager = World.DefaultGameObjectInjectionWorld.EntityManager;
        if (entityManager == null) return;

        var currentCounts = new Dictionary<string, int>();
        int totalEntities = 0;

        foreach (var kvp in entityQueries)
        {
            try
            {
                int count = kvp.Value.CalculateEntityCount();
                string name = kvp.Key.Name.Replace("Component", "");
                currentCounts[name] = count;
                totalEntities += count;
            }
            catch (InvalidOperationException ex)
            {
                 Debug.LogError($"Left_GUI: Error calculating entity count for {kvp.Key.Name}: {ex.Message}");
            }
             catch (Exception ex)
             {
                 Debug.LogError($"Left_GUI: Unexpected error calculating entity count for {kvp.Key.Name}: {ex.Message}\n{ex.StackTrace}");
             }
        }
        currentCounts["Organism count"] = totalEntities;
        entityCounts = currentCounts;
    }

    private void CacheValidComponentTypes()
    {
        if (World.DefaultGameObjectInjectionWorld == null || !World.DefaultGameObjectInjectionWorld.IsCreated)
        {
             Debug.LogWarning("Left_GUI: World not ready for caching component types.");
             return;
        }
        var entityManager = World.DefaultGameObjectInjectionWorld.EntityManager;
        if (entityManager == null) return;

        foreach(var query in entityQueries.Values)
        {
            query.Dispose();
        }
        entityQueries.Clear();
        validComponentTypes.Clear();

        try
        {
            foreach (Type type in Assembly.GetExecutingAssembly().GetTypes())
            {
                if (type.IsValueType && !type.IsAbstract && !type.IsGenericTypeDefinition && typeof(IComponentData).IsAssignableFrom(type))
                {
                    string typeName = type.Name;
                    if (typeName.EndsWith("Component") && typeName != "PrefabEntityComponent" && typeName != "PlaneComponent")
                    {
                        validComponentTypes.Add(type);
                        var query = entityManager.CreateEntityQuery(ComponentType.ReadOnly(type));
                        entityQueries.Add(type, query);
                    }
                }
            }
        }
        catch (Exception ex)
        {
             Debug.LogError($"Left_GUI: Error during component type caching: {ex.Message}\n{ex.StackTrace}");
        }
         Debug.Log($"Left_GUI: Finished caching component types. Found {validComponentTypes.Count} valid types.");
    }

    void OnGUI()
    {
        if (labelStyle == null)
        {
            labelStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = GUIFontSize,
                normal = { textColor = Color.white },
                alignment = TextAnchor.MiddleLeft
            };
        }

        if (!GameStateManager.IsSetupComplete) return;

        DisplaySimulationStats();
    }

    private void DisplaySimulationStats()
{
    int y = GUIYPosition + 5;

    GUI.Label(new Rect(GUIXPosition, y, GUIWidth, GUIHeight), $"FPS: {cachedFPS:F2}", labelStyle); y += GUIHeight;
    //GUI.Label(new Rect(GUIXPosition, y, GUIWidth, GUIHeight), $"Real Time: {FormatTime(cachedRealTime)}", labelStyle); y += GUIHeight;
    GUI.Label(new Rect(GUIXPosition, y, GUIWidth, GUIHeight), $"Simulated Time: {FormatTime(cachedSimulatedTime)}", labelStyle); y += GUIHeight;

    float timeMultiplier = GameStateManager.DeltaTime * 60f;
    string multiplierText = hasStartedSimulation ? $"{timeMultiplier:F2}x" : "N/A";

    GUI.Label(new Rect(GUIXPosition, y, GUIWidth, GUIHeight), $"Time Multiplier: {multiplierText}", labelStyle); y += GUIHeight; // Considerar usar GameStateManager.TimeMultiplier si existe
    //GUI.Label(new Rect(GUIXPosition, y, GUIWidth, GUIHeight), $"DeltaTime: {GameStateManager.DeltaTime:F4}", labelStyle); y += GUIHeight;
    //GUI.Label(new Rect(GUIXPosition, y, GUIWidth, GUIHeight), $"Elapsed Frames: {cachedFrameCount}", labelStyle); y += GUIHeight;
    //GUI.Label(new Rect(GUIXPosition, y, GUIWidth, GUIHeight), $"Paused: {(GameStateManager.IsPaused ? "Yes" : "No")}", labelStyle); y += GUIHeight;

    y += 5;
    GUI.Label(new Rect(GUIXPosition, y, GUIWidth, GUIHeight), "--- Entities ---", labelStyle); y += GUIHeight;


    KeyValuePair<string, int> organismCountEntry = default;
    bool hasOrganismCount = false;
    if (entityCounts.TryGetValue("Organism count", out int totalCount))
    {
        organismCountEntry = new KeyValuePair<string, int>("Organism count", totalCount);
        hasOrganismCount = true;
    }

    List<KeyValuePair<string, int>> specificOrganisms = entityCounts
        .Where(pair => pair.Key != "Organism count")
        .ToList();

    specificOrganisms.Sort((pair1, pair2) => pair1.Key.CompareTo(pair2.Key));

    foreach (var entry in specificOrganisms)
    {
        GUI.Label(new Rect(GUIXPosition, y, GUIWidth, GUIHeight), $"{entry.Key}: {entry.Value}", labelStyle);
        y += GUIHeight;
    }

    if (hasOrganismCount)
    {
        GUI.Label(new Rect(GUIXPosition, y, GUIWidth, GUIHeight), $"{organismCountEntry.Key}: {organismCountEntry.Value}", labelStyle);
        y += GUIHeight;
    }
}

    private string FormatTime(float timeInSeconds)
    {
        TimeSpan t = TimeSpan.FromSeconds(timeInSeconds);
        string formatted = "";
        if (t.Days > 0) formatted += $"{t.Days}d ";
        if (t.Hours > 0 || !string.IsNullOrEmpty(formatted)) formatted += $"{t.Hours:D2}h ";
        if (t.Minutes > 0 || !string.IsNullOrEmpty(formatted)) formatted += $"{t.Minutes:D2}m ";
        formatted += $"{t.Seconds:D2}s";
        if (string.IsNullOrEmpty(formatted)) formatted = "0s";
        return formatted;
    }
}