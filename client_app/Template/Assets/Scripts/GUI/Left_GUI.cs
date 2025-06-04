using UnityEngine;
using System;
using System.Collections.Generic;
using Unity.Entities;
using System.Reflection;
using System.Linq;

public class Left_GUI : MonoBehaviour
{
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
    private GUIStyle backgroundBoxStyle;
    private bool stylesInitialized = false;

    private int baseFontSize = 18;

    private float referenceWidth = 1920f;
    private float referenceHeight = 1080f;
    private float scaleWidth;
    private float scaleHeight;
    private float generalScale;

    private List<KeyValuePair<string, int>> sortedSpecificOrganisms;
    private List<GUIContent> statLabelsContent;


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
        sortedSpecificOrganisms = new List<KeyValuePair<string, int>>();
        statLabelsContent = new List<GUIContent>();
        CacheValidComponentTypes();
        ResetCachedValues();
        CalculateScaleFactors();
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
        this.enabled = true;
        ResetCachedValues();
    }

    void CalculateScaleFactors()
    {
        scaleWidth = Screen.width / referenceWidth;
        scaleHeight = Screen.height / referenceHeight;
        generalScale = Mathf.Min(scaleWidth, scaleHeight);
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
        sortedSpecificOrganisms.Clear();
    }

    private void UpdateEntityCounts()
    {
        if (World.DefaultGameObjectInjectionWorld == null || !World.DefaultGameObjectInjectionWorld.IsCreated)
        {
            entityCounts.Clear();
            if (entityCounts.ContainsKey("Organism count"))
                 entityCounts["Organism count"] = 0;
            else
                entityCounts.Add("Organism count", 0);
            sortedSpecificOrganisms.Clear();
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
            catch (ObjectDisposedException) { }
            catch (InvalidOperationException) { }
            catch (Exception) { }
        }
        currentCounts["Organism count"] = totalEntities;
        entityCounts = currentCounts;

        sortedSpecificOrganisms.Clear();
        foreach (var pair in entityCounts)
        {
            if (pair.Key != "Organism count" && pair.Value > 0) 
            {
                sortedSpecificOrganisms.Add(pair);
            }
        }
        sortedSpecificOrganisms.Sort((pair1, pair2) => pair1.Key.CompareTo(pair2.Key));
    }

    private void CacheValidComponentTypes()
    {
        if (World.DefaultGameObjectInjectionWorld == null || !World.DefaultGameObjectInjectionWorld.IsCreated)
        {
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
                    if (typeName.EndsWith("Component") && typeName != "PrefabEntityComponent" && typeName != "PlaneComponent" && typeName != "Disabled" && typeName != "SceneSection")
                    {
                        validComponentTypes.Add(type);
                        var query = entityManager.CreateEntityQuery(ComponentType.ReadOnly(type));
                        entityQueries.Add(type, query);
                    }
                }
            }
        }
        catch (Exception) { }
    }
    
    private Texture2D MakeTex(int width, int height, Color col)
    {
        Color[] pix = new Color[width * height];
        for (int i = 0; i < pix.Length; ++i)
        {
            pix[i] = col;
        }
        Texture2D result = new Texture2D(width, height);
        result.SetPixels(pix);
        result.Apply();
        return result;
    }

    private void InitializeStyles()
    {
        int scaledFontSize = Mathf.RoundToInt(baseFontSize * scaleHeight);
        scaledFontSize = Mathf.Max(scaledFontSize, 10);

        labelStyle = new GUIStyle(GUI.skin.label)
        {
            fontSize = scaledFontSize,
            normal = { textColor = Color.white },
            alignment = TextAnchor.MiddleLeft
        };

        backgroundBoxStyle = new GUIStyle(GUI.skin.box);
        backgroundBoxStyle.normal.background = MakeTex(1, 1, new Color(0.05f, 0.05f, 0.05f, 0.75f));
        backgroundBoxStyle.padding = new RectOffset(Mathf.RoundToInt(8 * scaleWidth), Mathf.RoundToInt(8 * scaleWidth), Mathf.RoundToInt(8 * scaleHeight), Mathf.RoundToInt(8 * scaleHeight));


        stylesInitialized = true;
    }

    void OnGUI()
    {
        CalculateScaleFactors();

        if (!stylesInitialized || Event.current.type == EventType.Layout)
        {
            InitializeStyles();
        }
        
        if (labelStyle == null || backgroundBoxStyle == null) return;


        if (!GameStateManager.IsSetupComplete) return;

        DisplaySimulationStats();
    }

    private void DisplaySimulationStats()
    {
        float scaledXPosition = Mathf.RoundToInt(10 * scaleWidth);
        float scaledYPositionBase = Mathf.RoundToInt(10 * scaleHeight);
        float scaledLineHeight = Mathf.RoundToInt( (baseFontSize + 8) * scaleHeight);
        scaledLineHeight = Mathf.Max(scaledLineHeight, 20);

        statLabelsContent.Clear();
        statLabelsContent.Add(new GUIContent($"FPS: {cachedFPS:F2}"));
        statLabelsContent.Add(new GUIContent($"Simulated Time: {FormatTime(cachedSimulatedTime)}"));
        float timeMultiplier = GameStateManager.DeltaTime * 60f;
        string multiplierText = hasStartedSimulation ? $"{timeMultiplier:F2}x" : "N/A";
        statLabelsContent.Add(new GUIContent($"Time Multiplier: {multiplierText}"));
        statLabelsContent.Add(new GUIContent("--- Entities ---"));

        foreach (var entry in sortedSpecificOrganisms)
        {
            statLabelsContent.Add(new GUIContent($"{entry.Key}: {entry.Value}"));
        }
        if (entityCounts.TryGetValue("Organism count", out int totalCount))
        {
            statLabelsContent.Add(new GUIContent($"Organism count: {totalCount}"));
        }

        float calculatedMaxWidthFromText = 0f;
        float textWidthBuffer = 10f; 

        if (labelStyle != null) {
            foreach (var content in statLabelsContent)
            {
                Vector2 size = labelStyle.CalcSize(content);
                if (size.x > calculatedMaxWidthFromText)
                {
                    calculatedMaxWidthFromText = size.x;
                }
            }
        }
        calculatedMaxWidthFromText += textWidthBuffer; 
        
        float boxMinimumWidth = Mathf.RoundToInt(250 * scaleWidth);
        float effectiveContentWidth = Mathf.Max(calculatedMaxWidthFromText, boxMinimumWidth);


        int numLines = statLabelsContent.Count;
        float sectionSpacing = Mathf.RoundToInt(6 * scaleHeight);
        float totalContentHeight = (numLines * scaledLineHeight) + sectionSpacing + backgroundBoxStyle.padding.top + backgroundBoxStyle.padding.bottom;
        
        Rect backgroundRect = new Rect(
            scaledXPosition, 
            scaledYPositionBase, 
            effectiveContentWidth + backgroundBoxStyle.padding.left + backgroundBoxStyle.padding.right, 
            totalContentHeight
        );
        GUI.Box(backgroundRect, GUIContent.none, backgroundBoxStyle);

        int y = Mathf.RoundToInt(scaledYPositionBase + backgroundBoxStyle.padding.top);
        float currentX = scaledXPosition + backgroundBoxStyle.padding.left;

        for(int i = 0; i < statLabelsContent.Count; i++)
        {
            GUI.Label(new Rect(currentX, y, effectiveContentWidth, scaledLineHeight), statLabelsContent[i], labelStyle);
            y += Mathf.RoundToInt(scaledLineHeight);
            if (statLabelsContent[i].text == "--- Entities ---")
            {
                y += Mathf.RoundToInt(sectionSpacing / 2);
            }
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
