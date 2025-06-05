using UnityEngine;
using Unity.Entities;
using Unity.Mathematics;
using Unity.Transforms;
using Unity.Collections;
using Unity.Physics;
using UnityEngine.UI;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Globalization;
using PhysicsMaterial = Unity.Physics.Material; 

public class CreatePrefabsOnClick : MonoBehaviour
{
    [System.Serializable]
    public class OrganismColonyConfig
    {
        public string prefabName;
        public GameObject prefabGO;
        public Entity bakedPrefabEntity;
        public string countInput;
        public string radiusInput;
        public int currentCount;
        public float currentColonyRadius;

        public OrganismColonyConfig(GameObject go, int defaultCount, float defaultRadius)
        {
            prefabGO = go;
            prefabName = go.name;
            bakedPrefabEntity = Entity.Null;
            countInput = Mathf.Max(0, defaultCount).ToString();
            radiusInput = Mathf.Clamp(defaultRadius, 1f, 900f).ToString("F1", CultureInfo.InvariantCulture);
            currentCount = Mathf.Max(0, defaultCount);
            currentColonyRadius = Mathf.Clamp(defaultRadius, 1f, 900f);
        }
    }

    private enum PlacementState
    {
        Idle, Configuring, WaitingForSpawnerEntities, WaitingForColonyClick, SpawningComplete
    }

    private PlacementState currentPlacementState = PlacementState.Configuring;

    private List<OrganismColonyConfig> organismConfigs = new List<OrganismColonyConfig>();
    private List<GameObject> prefabs;
    private GameObject messageCanvas;
    private Text messageText; 
    private EntityManager entityManager;
    private EntityQuery spawnerQuery;
    private Camera mainCamera;

    [Header("Default Colony Configuration (for all detected prefabs)")]
    public int defaultInitialCountForEachOrganism = 50;
    public float defaultColonyRadiusForEachOrganism = 15f;

    [Header("General Placement Configuration")]
    public float groundLevelY = 0.75f;
    public float maxPlacementDistanceFromOrigin = 900f;

    [Header("Spawning System Configuration")]
    public float spawnerWaitTimeout = 10.0f;
    public float spawnerCheckInterval = 0.5f;

    [Header("Preview Configuration")]
    public int previewCircleSegments = 64;
    [Tooltip("URP Unlit Material for the RED max placement boundary line. Shader: URP/Unlit.")]
    public UnityEngine.Material redUnlitMaterial; 
    [Tooltip("URP Unlit Material for the GREEN colony preview line and fill. Shader: URP/Unlit. IMPORTANT: Set Surface Type to Transparent and Blending to Alpha in Material Inspector for fill transparency.")]
    public UnityEngine.Material greenUnlitMaterial; 
    public Color maxBoundaryPreviewColor = Color.red;
    [Tooltip("Color for the current colony radius preview (line and fill). Alpha affects fill transparency.")]
    public Color colonyRadiusPreviewColor = new Color(0f, 1f, 0f, 0.3f);
    public float previewLineWidth = 2f;
    [Tooltip("Slight Y-offset for previews to prevent Z-fighting with the ground.")]
    public float previewYOffset = 0.05f;

    private bool showConfigurationUI = true;
    private Vector2 scrollPosition = Vector2.zero;
    private GUIStyle textFieldStyle, labelStyle, buttonStyle, windowStyle, headerLabelStyle, subHeaderLabelStyle, warningLabelStyle;
    private bool guiStylesInitialized = false;
    private Texture2D windowBackground;
    private string performanceWarningText = ""; // Renamed for clarity

    private List<OrganismColonyConfig> coloniesToPlace = new List<OrganismColonyConfig>();
    private int currentPlacingColonyIndex = -1;
    private OrganismColonyConfig currentConfigForPlacement;

    private GameObject maxOriginBoundaryPreviewObject;
    private LineRenderer maxOriginBoundaryLineRenderer;
    private GameObject colonyPreviewObject;
    private LineRenderer colonyPreviewLineRenderer;
    private GameObject colonyFillPreviewObject;
    private MeshFilter colonyFillMeshFilter;
    private MeshRenderer colonyFillMeshRenderer;
    private Mesh colonyFillMesh;

    void Start()
    {
        mainCamera = Camera.main;
        if (mainCamera == null) Debug.LogError("CreatePrefabsOnClick: No main camera found.");

        entityManager = World.DefaultGameObjectInjectionWorld.EntityManager;
        CreateMessageUI(); 
        LoadAndConfigurePrefabData();

        if (organismConfigs.Count == 0)
        {
            Debug.LogError("No prefabs found. Cannot spawn colonies.");
            if (messageText != null) messageText.text = "Error: No prefabs found.";
            enabled = false;
            return;
        }
        spawnerQuery = entityManager.CreateEntityQuery(typeof(PrefabEntityComponent));

        SetupPreviewRenderers(); 

        if (messageText != null) messageText.text = "Awaiting Initial Organism Setup...";
        currentPlacementState = PlacementState.Configuring;
        showConfigurationUI = true;
    }

    void Update()
    {
        if (currentPlacementState == PlacementState.WaitingForColonyClick)
        {
            HandleColonyPreviewUpdate();

            if (Input.GetMouseButtonDown(0))
            {
                if (mainCamera == null)
                {
                    Debug.LogError("Main camera not found, cannot process click.");
                    return;
                }
                UnityEngine.Ray ray = mainCamera.ScreenPointToRay(Input.mousePosition);
                if (UnityEngine.Physics.Raycast(ray, out UnityEngine.RaycastHit hit))
                {
                    Vector3 clickedPosition = hit.point;
                    clickedPosition.y = groundLevelY;
                    
                    SpawnOrganismColony(currentConfigForPlacement.prefabGO,
                                        currentConfigForPlacement.bakedPrefabEntity,
                                        currentConfigForPlacement.currentCount,
                                        clickedPosition,
                                        currentConfigForPlacement.currentColonyRadius);
                    currentPlacingColonyIndex++;
                    RequestNextColonyPlacement();
                }
                else
                {
                    if (messageText != null) messageText.text = $"Click on the ground to place {currentConfigForPlacement.prefabName}.";
                }
            }
        }
    }

    private void SetupPreviewRenderers()
    {
        maxOriginBoundaryPreviewObject = new GameObject("MaxOriginBoundaryPreview_Line");
        maxOriginBoundaryPreviewObject.transform.SetParent(transform);
        maxOriginBoundaryLineRenderer = maxOriginBoundaryPreviewObject.AddComponent<LineRenderer>();
        ConfigureLineRenderer(maxOriginBoundaryLineRenderer, redUnlitMaterial, maxBoundaryPreviewColor, "MaxOriginBoundary");
        DrawCircleLine(maxOriginBoundaryLineRenderer, new Vector3(0, groundLevelY + previewYOffset, 0), maxPlacementDistanceFromOrigin, previewCircleSegments, false); 
        maxOriginBoundaryPreviewObject.SetActive(false);

        colonyPreviewObject = new GameObject("ColonyRadiusPreview_Line");
        colonyPreviewObject.transform.SetParent(transform);
        colonyPreviewLineRenderer = colonyPreviewObject.AddComponent<LineRenderer>();
        ConfigureLineRenderer(colonyPreviewLineRenderer, greenUnlitMaterial, colonyRadiusPreviewColor, "ColonyRadiusLine");
        colonyPreviewObject.SetActive(false);

        colonyFillPreviewObject = new GameObject("ColonyFillPreview_Mesh");
        colonyFillPreviewObject.transform.SetParent(transform);
        colonyFillMeshFilter = colonyFillPreviewObject.AddComponent<MeshFilter>();
        colonyFillMeshRenderer = colonyFillPreviewObject.AddComponent<MeshRenderer>();
        colonyFillMesh = new Mesh { name = "ColonyFillCircleMesh" };
        colonyFillMesh.MarkDynamic(); 
        colonyFillMeshFilter.mesh = colonyFillMesh;

        if (greenUnlitMaterial != null)
        {
            colonyFillMeshRenderer.material = greenUnlitMaterial; 
            colonyFillMeshRenderer.material.SetColor("_BaseColor", colonyRadiusPreviewColor);
            if (colonyRadiusPreviewColor.a < 1.0f)
            {
                colonyFillMeshRenderer.material.SetFloat("_Surface", 1.0f); 
                colonyFillMeshRenderer.material.SetFloat("_Blend", 0.0f);   
            }
        }
        else
        {
            Debug.LogWarning("ColonyFillPreview: greenUnlitMaterial not assigned. Using fallback.");
            UnityEngine.Material fallbackFillMat = new UnityEngine.Material(Shader.Find("Universal Render Pipeline/Unlit"));
            if (fallbackFillMat != null && fallbackFillMat.shader != null && fallbackFillMat.shader.name != "Hidden/InternalErrorShader")
            {
                fallbackFillMat.SetColor("_BaseColor", colonyRadiusPreviewColor);
                if (colonyRadiusPreviewColor.a < 1.0f) {
                    fallbackFillMat.SetFloat("_Surface", 1.0f); 
                    fallbackFillMat.SetFloat("_Blend", 0.0f); 
                }
                colonyFillMeshRenderer.material = fallbackFillMat;
            } else {
                 Debug.LogError("ColonyFillPreview: FALLBACK URP/Unlit shader not found or invalid.");
                 colonyFillMeshRenderer.material = new UnityEngine.Material(Shader.Find("Hidden/InternalErrorShader"));
            }
        }
        colonyFillPreviewObject.SetActive(false);
    }

    private void ConfigureLineRenderer(LineRenderer lr, UnityEngine.Material lineMatAsset, Color lineColor, string previewName)
    {
        if (lineMatAsset != null)
        {
            lr.material = lineMatAsset;
        }
        else
        {
            Debug.LogWarning($"{previewName} LineRenderer: Material not assigned. Attempting URP/Unlit fallback.");
            UnityEngine.Material fallbackLineMat = new UnityEngine.Material(Shader.Find("Universal Render Pipeline/Unlit"));
             if (fallbackLineMat == null || fallbackLineMat.shader == null || fallbackLineMat.shader.name == "Hidden/InternalErrorShader") {
                Debug.LogError($"{previewName} LineRenderer: FALLBACK URP/Unlit shader not found. Attempting Legacy fallback.");
                fallbackLineMat = new UnityEngine.Material(Shader.Find("Legacy Shaders/Particles/Alpha Blended Premultiply"));
                 if (fallbackLineMat == null || fallbackLineMat.shader == null || fallbackLineMat.shader.name == "Hidden/InternalErrorShader"){
                     Debug.LogError($"{previewName} LineRenderer: Legacy FALLBACK shader also not found. Line will likely be magenta or invisible.");
                 }
            }
            lr.material = fallbackLineMat;
        }
        
        lr.startColor = new Color(lineColor.r, lineColor.g, lineColor.b, 1f); 
        lr.endColor = new Color(lineColor.r, lineColor.g, lineColor.b, 1f);   
        lr.startWidth = previewLineWidth;
        lr.endWidth = previewLineWidth;
        lr.loop = true; 
        lr.useWorldSpace = true;
        lr.positionCount = 0;
    }

    private void DrawCircleLine(LineRenderer lineRenderer, Vector3 centerWithYOffset, float radius, int segments, bool applyGlobalClampToIndividualPoints)
    {
        if (lineRenderer == null) return;
        if (segments < 3 || radius <= 0.001f) {
            lineRenderer.positionCount = 0;
            return;
        }
        
        lineRenderer.positionCount = segments +1;

        float deltaTheta = (2f * Mathf.PI) / segments;
        float theta = 0f;

        for (int i = 0; i <= segments; i++)
        {
            float x = radius * Mathf.Cos(theta);
            float z = radius * Mathf.Sin(theta);
            Vector3 pointOnCircle = new Vector3(x + centerWithYOffset.x, centerWithYOffset.y, z + centerWithYOffset.z);
            
            Vector3 finalPoint = pointOnCircle;
            if (applyGlobalClampToIndividualPoints) 
            {
                Vector2 pointFromOriginXZ = new Vector2(pointOnCircle.x, pointOnCircle.z);
                if (pointFromOriginXZ.magnitude > maxPlacementDistanceFromOrigin)
                {
                    pointFromOriginXZ = pointFromOriginXZ.normalized * maxPlacementDistanceFromOrigin;
                    finalPoint = new Vector3(pointFromOriginXZ.x, centerWithYOffset.y, pointFromOriginXZ.y);
                }
            }
            lineRenderer.SetPosition(i, finalPoint);
            theta += deltaTheta;
        }
    }

    private void GenerateCircleFillMesh(Mesh mesh, float radius, int segments)
    {
        if (mesh == null) { Debug.LogError("GenerateCircleFillMesh: Mesh is null!"); return; }
        mesh.Clear(); 

        if (radius <= 0.001f || segments < 3)
        {
            return; 
        }

        Vector3[] vertices = new Vector3[segments + 1];
        int[] triangles = new int[segments * 3];
        Vector2[] uvs = new Vector2[vertices.Length]; 

        vertices[0] = Vector3.zero; 
        uvs[0] = new Vector2(0.5f, 0.5f); 

        float angleStep = 360.0f / segments;

        for (int i = 0; i < segments; i++)
        {
            float currentAngle = i * angleStep * Mathf.Deg2Rad;
            vertices[i + 1] = new Vector3(Mathf.Cos(currentAngle) * radius, 0, Mathf.Sin(currentAngle) * radius);
            uvs[i + 1] = new Vector2(Mathf.Cos(currentAngle) * 0.5f + 0.5f, Mathf.Sin(currentAngle) * 0.5f + 0.5f);
        }

        for (int i = 0; i < segments; i++)
        {
            triangles[i * 3] = 0; 
            triangles[i * 3 + 1] = i + 1; 
            triangles[i * 3 + 2] = (i + 1) % segments + 1; 
        }
        
        mesh.vertices = vertices;
        mesh.triangles = triangles;
        mesh.uv = uvs; 
        mesh.RecalculateNormals(); 
        mesh.RecalculateBounds(); 
    }
    
    private void UpdateColonyPreview(Vector3 centerOnGround, float radius)
    {
        if (colonyPreviewLineRenderer == null || colonyFillMeshRenderer == null || colonyFillMesh == null)
        {
             Debug.LogError("UpdateColonyPreview: One or more preview renderers/mesh is null!");
             return;
        }

        Vector3 previewDrawCenter = centerOnGround + Vector3.up * previewYOffset;
        
        if (colonyPreviewObject.activeSelf)
        {
            DrawCircleLine(colonyPreviewLineRenderer, previewDrawCenter, radius, previewCircleSegments, true);
        }

        if (colonyFillPreviewObject.activeSelf)
        {
            colonyFillPreviewObject.transform.position = previewDrawCenter;
            GenerateCircleFillMesh(colonyFillMesh, radius, previewCircleSegments);

            if (colonyFillMeshRenderer.sharedMaterial != null)
            {
                 colonyFillMeshRenderer.material.SetColor("_BaseColor", colonyRadiusPreviewColor);
            }
        }
    }

    private void HandleColonyPreviewUpdate()
    {
        if (mainCamera != null && currentConfigForPlacement != null)
        {
            UnityEngine.Ray ray = mainCamera.ScreenPointToRay(Input.mousePosition);

            if (UnityEngine.Physics.Raycast(ray, out UnityEngine.RaycastHit hit))
            {
                Vector3 groundHitPoint = hit.point;
                groundHitPoint.y = groundLevelY; 
                
                Vector2 groundHitXZ = new Vector2(groundHitPoint.x, groundHitPoint.z);
                if (groundHitXZ.magnitude > maxPlacementDistanceFromOrigin)
                {
                    groundHitXZ = groundHitXZ.normalized * maxPlacementDistanceFromOrigin;
                    groundHitPoint = new Vector3(groundHitXZ.x, groundLevelY, groundHitXZ.y);
                }

                if (!colonyPreviewObject.activeSelf) colonyPreviewObject.SetActive(true);
                if (!colonyFillPreviewObject.activeSelf) colonyFillPreviewObject.SetActive(true);
                
                UpdateColonyPreview(groundHitPoint, currentConfigForPlacement.currentColonyRadius);
            }
            else
            {
                 if (colonyPreviewObject.activeSelf) colonyPreviewObject.SetActive(false);
                 if (colonyFillPreviewObject.activeSelf) colonyFillPreviewObject.SetActive(false);
            }
        }
    }

    private void TogglePlacementPreviews(bool active)
    {
        if (maxOriginBoundaryPreviewObject != null)
        {
            maxOriginBoundaryPreviewObject.SetActive(active);
        }
        
        if (!active) 
        {
            if (colonyPreviewObject != null && colonyPreviewObject.activeSelf) colonyPreviewObject.SetActive(false);
            if (colonyFillPreviewObject != null && colonyFillPreviewObject.activeSelf) colonyFillPreviewObject.SetActive(false);
        }
    }

    void InitializeGUIStyles()
    {
        if (guiStylesInitialized) return;

        windowBackground = new Texture2D(1, 1);
        windowBackground.SetPixel(0, 0, new Color(0.1f, 0.1f, 0.12f, 0.92f)); 
        windowBackground.Apply();

        Color lightTextColor = new Color(0.85f, 0.85f, 0.85f); 

        labelStyle = new GUIStyle(GUI.skin.label)
        {
            fontSize = 15, 
            alignment = TextAnchor.MiddleLeft,
            normal = { textColor = lightTextColor },
            padding = new RectOffset(5, 5, 2, 2) 
        };

        headerLabelStyle = new GUIStyle(GUI.skin.label)
        {
            fontSize = 18, 
            fontStyle = FontStyle.Bold,
            alignment = TextAnchor.MiddleCenter, 
            normal = { textColor = Color.white }, 
            margin = new RectOffset(0, 0, 5, 10) 
        };
        
        subHeaderLabelStyle = new GUIStyle(GUI.skin.label) 
        {
            fontSize = 16,
            fontStyle = FontStyle.Bold,
            alignment = TextAnchor.MiddleLeft,
            normal = { textColor = new Color(0.7f, 0.85f, 1f) }, 
            margin = new RectOffset(0,0,0,5)
        };

        textFieldStyle = new GUIStyle(GUI.skin.textField)
        {
            fontSize = 15,
            normal = { textColor = Color.white, background = GUI.skin.textField.normal.background }, 
            focused = { textColor = Color.white, background = GUI.skin.textField.focused.background },
            alignment = TextAnchor.MiddleLeft,
            padding = new RectOffset(8, 8, 5, 5), 
            margin = new RectOffset(5, 5, 3, 3)
        };

        buttonStyle = new GUIStyle(GUI.skin.button)
        {
            fontSize = 17, 
            fontStyle = FontStyle.Bold,
            normal = { textColor = Color.white },
            hover = { textColor = new Color(0.9f, 0.9f, 1f) }, 
            active = { textColor = new Color(0.8f, 0.8f, 1f) },
            padding = new RectOffset(12, 12, 10, 10), 
            margin = new RectOffset(5,5,10,5) 
        };

        windowStyle = new GUIStyle(GUI.skin.window)
        {
            fontSize = 20, 
            fontStyle = FontStyle.Bold,
            alignment = TextAnchor.UpperCenter,
            normal = { textColor = Color.white, background = windowBackground },
            onNormal = { background = windowBackground } 
        };
        windowStyle.padding = new RectOffset(20, 20, 30, 20); 

        warningLabelStyle = new GUIStyle(GUI.skin.label)
        {
            fontSize = 14,
            alignment = TextAnchor.MiddleCenter,
            normal = { textColor = new Color(1f, 0.8f, 0.3f) }, 
            fontStyle = FontStyle.Bold,
            wordWrap = true,
            margin = new RectOffset(5,5,5,10)
        };

        guiStylesInitialized = true;
    }

    void OnGUI()
    {
        InitializeGUIStyles(); 
        if (showConfigurationUI && currentPlacementState == PlacementState.Configuring)
        {
            if(messageCanvas != null && messageCanvas.activeSelf) messageCanvas.SetActive(false);
            
            float windowWidth = Mathf.Min(Screen.width * 0.85f, 750f);
            float maxWindowHeight = Screen.height * 0.5f;

            Rect windowRect = new Rect(
                (Screen.width - windowWidth) / 2, 
                (Screen.height - maxWindowHeight) / 2, 
                windowWidth, 
                maxWindowHeight
            );
                
            GUILayout.Window(0, windowRect, DrawConfigurationWindow, "Initial Organism Setup", windowStyle);
        }
        else
        {
            if(messageCanvas != null && !messageCanvas.activeSelf && currentPlacementState != PlacementState.Configuring && currentPlacementState != PlacementState.SpawningComplete && !GameStateManager.IsSetupComplete) 
                messageCanvas.SetActive(true);
        }
    }

    void DrawConfigurationWindow(int windowID)
    {
        float fieldWidth = 90f;
        float labelWidth = 250f;
        float spacing = 8f;
        float organismGroupSpacing = 15f;
        float buttonHeight = 45f;

        GUILayout.BeginVertical();
        GUILayout.Space(10);

        scrollPosition = GUILayout.BeginScrollView(
            scrollPosition,
            false,
            true,
            GUILayout.ExpandHeight(true)
        );

        if (organismConfigs != null && organismConfigs.Count > 0)
        {
            foreach (var config in organismConfigs)
            {
                GUILayout.Label($"{config.prefabName} Configuration", subHeaderLabelStyle);
                GUILayout.BeginHorizontal();
                GUILayout.Label("Initial Count:", labelStyle, GUILayout.Width(labelWidth));
                config.countInput = GUILayout.TextField(config.countInput, textFieldStyle, GUILayout.Width(fieldWidth), GUILayout.ExpandWidth(false));
                GUILayout.FlexibleSpace();
                GUILayout.EndHorizontal();
                GUILayout.Space(spacing / 2);
                GUILayout.BeginHorizontal();
                GUILayout.Label($"Colony Radius (1-900 µm):", labelStyle, GUILayout.Width(labelWidth));
                config.radiusInput = GUILayout.TextField(config.radiusInput, textFieldStyle, GUILayout.Width(fieldWidth), GUILayout.ExpandWidth(false));
                GUILayout.FlexibleSpace();
                GUILayout.EndHorizontal();
                GUILayout.Space(organismGroupSpacing);
            }
        }
        else
        {
            GUILayout.Label("No organism configurations loaded.", labelStyle);
        }
        GUILayout.EndScrollView();

        long totalOrganismsForWarning = 0;
        string localPerformanceWarningText = "";
        string zeroCountBlockerText = "";

        if (organismConfigs != null)
        {
            foreach (var config in organismConfigs)
            {
                if (int.TryParse(config.countInput, out int count))
                {
                    totalOrganismsForWarning += Mathf.Max(0, count);
                }
            }
        }

        bool enableStartButton = true;
        if (totalOrganismsForWarning == 0 && (organismConfigs != null && organismConfigs.Count > 0))
        {
            zeroCountBlockerText = "CANNOT START: Total organism count is zero. Please enter counts for organisms.";
            enableStartButton = false;
        }
        else if (organismConfigs == null || organismConfigs.Count == 0)
        {
            zeroCountBlockerText = "CANNOT START: No organism configurations loaded.";
            enableStartButton = false;
        }
        else if (totalOrganismsForWarning > 100000)
        {
            localPerformanceWarningText = $"Warning: High organism count ({totalOrganismsForWarning:N0}) may impact performance.";
        }

        if (!string.IsNullOrEmpty(zeroCountBlockerText))
        {
            GUILayout.Label(zeroCountBlockerText, warningLabelStyle, GUILayout.ExpandWidth(true));
        }
        else if (!string.IsNullOrEmpty(localPerformanceWarningText))
        {
            GUILayout.Label(localPerformanceWarningText, warningLabelStyle, GUILayout.ExpandWidth(true));
        }
        else
        {
            if (warningLabelStyle != null && warningLabelStyle.fontSize > 0)
            {
                GUILayout.Space(warningLabelStyle.lineHeight > 0 ? warningLabelStyle.lineHeight : warningLabelStyle.fontSize + (warningLabelStyle.margin != null ? warningLabelStyle.margin.vertical : 4));
            } else {
                GUILayout.Space(GUI.skin.label.lineHeight > 0 ? GUI.skin.label.lineHeight : GUI.skin.label.fontSize + 4);
            }
        }
        
        GUI.enabled = enableStartButton;
        if (GUILayout.Button("Start Simulation", buttonStyle, GUILayout.Height(buttonHeight), GUILayout.ExpandWidth(true)))
        {
            bool allParseSuccess = true;
            long totalFinalOrganismCount = 0;
            if (organismConfigs != null)
            {
                foreach (var config in organismConfigs)
                {
                    if (!int.TryParse(config.countInput, out config.currentCount))
                    {
                        config.currentCount = defaultInitialCountForEachOrganism;
                        allParseSuccess = false;
                        Debug.LogError($"Invalid count for {config.prefabName}: '{config.countInput}' - reset to default {config.currentCount}.");
                    }
                    config.currentCount = Mathf.Max(0, config.currentCount);

                    if (!float.TryParse(config.radiusInput, NumberStyles.Any, CultureInfo.InvariantCulture, out float parsedRadius))
                    {
                        parsedRadius = defaultColonyRadiusForEachOrganism;
                        allParseSuccess = false;
                        Debug.LogError($"Invalid radius for {config.prefabName}: '{config.radiusInput}' - reset to default {parsedRadius}.");
                    }
                    config.currentColonyRadius = Mathf.Clamp(parsedRadius, 1f, 900f);
                    config.radiusInput = config.currentColonyRadius.ToString("F1", CultureInfo.InvariantCulture);
                    totalFinalOrganismCount += config.currentCount;
                }
            }

            if (allParseSuccess) Debug.Log("Configuration accepted.");
            else Debug.LogWarning("One or more invalid config values were reset to defaults. Check console.");
            Debug.Log($"Total organisms to be spawned: {totalFinalOrganismCount}");
            if (totalFinalOrganismCount > 100000 && string.IsNullOrEmpty(localPerformanceWarningText))
            {
                Debug.LogWarning($"PERFORMANCE WARNING (from final parsed count): Total organism count ({totalFinalOrganismCount}) is high and may impact performance.");
            }

            showConfigurationUI = false;
            currentPlacementState = PlacementState.WaitingForSpawnerEntities;
            if (messageCanvas != null) messageCanvas.SetActive(true);
            StartCoroutine(HandleColonyPlacementWorkflow());
        }
        GUI.enabled = true;

        GUILayout.Space(10);
        GUILayout.EndVertical();
        GUI.DragWindow();
    }

    private IEnumerator HandleColonyPlacementWorkflow()
    {
        if (messageText != null) messageText.text = "Waiting for spawner entities...";
        currentPlacementState = PlacementState.WaitingForSpawnerEntities;
        float elapsedTime = 0f; bool spawnersFound = false; int expectedSpawnerCount = prefabs.Count;
        
        while (elapsedTime < spawnerWaitTimeout)
        {
            int spawnerCount = spawnerQuery.CalculateEntityCount();
            if (spawnerCount > 0 && spawnerCount >= expectedSpawnerCount) { spawnersFound = true; break; }
            yield return new WaitForSeconds(spawnerCheckInterval); elapsedTime += spawnerCheckInterval;
        }

        if (spawnersFound)
        {
            NativeArray<Entity> spawnerEntities = spawnerQuery.ToEntityArray(Allocator.TempJob);
            try
            {
                foreach (var config in organismConfigs) 
                { 
                    if (config.prefabGO != null)
                    {
                        int prefabIndexInLoadedList = prefabs.IndexOf(config.prefabGO); 
                        if (prefabIndexInLoadedList != -1 && prefabIndexInLoadedList < spawnerEntities.Length)
                        {
                            Entity spawnerEntity = spawnerEntities[prefabIndexInLoadedList];
                            if (entityManager.HasComponent<PrefabEntityComponent>(spawnerEntity))
                            {
                                config.bakedPrefabEntity = entityManager.GetComponentData<PrefabEntityComponent>(spawnerEntity).prefab;
                                if(config.bakedPrefabEntity == Entity.Null) Debug.LogWarning($"Baked entity for {config.prefabName} is Null in PrefabEntityComponent.");
                            } else {
                                Debug.LogError($"Spawner entity for {config.prefabName} (index {prefabIndexInLoadedList}) does not have PrefabEntityComponent.");
                            }
                        } else {
                            Debug.LogError($"Could not find a matching spawner entity for '{config.prefabName}'. Index: {prefabIndexInLoadedList}, Prefabs: {prefabs.Count}, Spawners: {spawnerEntities.Length}.");
                        }
                    }
                }
            }
            finally
            {
                spawnerEntities.Dispose();
            }

            coloniesToPlace.Clear();
            foreach(var config in organismConfigs) 
            { 
                if(config.currentCount > 0 && config.prefabGO != null && config.bakedPrefabEntity != Entity.Null) 
                {
                    coloniesToPlace.Add(config); 
                }
            }

            if (coloniesToPlace.Count > 0)
            {
                TogglePlacementPreviews(true); 
                currentPlacingColonyIndex = 0;
                RequestNextColonyPlacement();
            }
            else 
            { 
                Debug.Log("No colonies configured for placement.");
                OnAllPrefabsPlaced(); 
            }
        }
        else
        {
            Debug.LogError("Timed out waiting for spawner entities.");
            if (messageText != null) messageText.text = "Error: Spawners not found. Check console.";
            showConfigurationUI = true; 
            currentPlacementState = PlacementState.Configuring;
            if(messageCanvas != null) messageCanvas.SetActive(false); 
        }
    }

    private void RequestNextColonyPlacement()
    {
        if (currentPlacingColonyIndex < coloniesToPlace.Count)
        {
            currentConfigForPlacement = coloniesToPlace[currentPlacingColonyIndex];
            if (messageText != null)
            {
                messageText.text = $"Click to place center of '{currentConfigForPlacement.prefabName}' colony (Radius: {currentConfigForPlacement.currentColonyRadius}µm).";
                if (messageCanvas !=null && !messageCanvas.activeSelf) messageCanvas.SetActive(true);
            }
            currentPlacementState = PlacementState.WaitingForColonyClick;
        }
        else
        {
            OnAllPrefabsPlaced();
        }
    }

    private void LoadAndConfigurePrefabData()
    {
        defaultColonyRadiusForEachOrganism = Mathf.Clamp(defaultColonyRadiusForEachOrganism, 1f, 900f);
        defaultInitialCountForEachOrganism = Mathf.Max(0, defaultInitialCountForEachOrganism);

        prefabs = new List<GameObject>(Resources.LoadAll<GameObject>("Prefabs")); 
        organismConfigs.Clear();
        foreach (var go in prefabs) 
        { 
            if (go == null) continue; 
            organismConfigs.Add(new OrganismColonyConfig(go, defaultInitialCountForEachOrganism, defaultColonyRadiusForEachOrganism)); 
        }
        organismConfigs = organismConfigs.OrderBy(c => c.prefabName).ToList();
    }

    private void SpawnOrganismColony(GameObject sourcePrefabGO, Entity bakedPrefabEntity, int count, Vector3 colonyCenter, float dispersionRadius)
    {
        if (bakedPrefabEntity == Entity.Null) { Debug.LogError($"Baked entity for {sourcePrefabGO.name} is Null. Cannot spawn colony."); return; }
        
        float originalScale = 1f;
        if (entityManager.HasComponent<LocalTransform>(bakedPrefabEntity)) originalScale = entityManager.GetComponentData<LocalTransform>(bakedPrefabEntity).Scale;
        else if(entityManager.HasComponent<LocalToWorld>(bakedPrefabEntity))
        {
            Debug.LogWarning($"Baked entity {sourcePrefabGO.name} does not have LocalTransform, using scale 1. Add LocalTransform for correct scaling.");
        }

        float effectiveRadiusForOffsetGeneration = Mathf.Min(dispersionRadius, maxPlacementDistanceFromOrigin);

        for (int i = 0; i < count; i++)
        {
            Vector2 offsetInColony = UnityEngine.Random.insideUnitCircle * effectiveRadiusForOffsetGeneration;
            Vector3 spawnPos = new Vector3(colonyCenter.x + offsetInColony.x, colonyCenter.y, colonyCenter.z + offsetInColony.y);
            
            Vector2 spawnPosXZ = new Vector2(spawnPos.x, spawnPos.z);
            if (spawnPosXZ.magnitude > maxPlacementDistanceFromOrigin)
            {
                spawnPosXZ = spawnPosXZ.normalized * maxPlacementDistanceFromOrigin;
                spawnPos = new Vector3(spawnPosXZ.x, spawnPos.y, spawnPosXZ.y); 
            }
            
            float randomYaw = UnityEngine.Random.Range(0f, 360f) * Mathf.Deg2Rad;
            float randomPitch = 0f;
            float randomRoll = UnityEngine.Random.Range(-30f, 30f) * Mathf.Deg2Rad;

            quaternion randomRotation = quaternion.Euler(randomPitch, randomYaw, randomRoll);

            CreateSingleEntity(sourcePrefabGO.name, bakedPrefabEntity, spawnPos, randomRotation, originalScale);}}

    //CODE START
    
    //CODE END

    private void OnAllPrefabsPlaced() 
    {
        if (messageText != null) messageText.text = "All configured colonies placed. Setup complete.";
        currentPlacementState = PlacementState.SpawningComplete;
        TogglePlacementPreviews(false);
        StartCoroutine(ShowFinalMessageAndCompleteSetup());
    }

    private IEnumerator ShowFinalMessageAndCompleteSetup()
    {
        yield return new WaitForSeconds(2.5f); 
        if (messageCanvas != null) messageCanvas.SetActive(false);
        GameStateManager.CompleteSetup(); 
    }

    private void CreateMessageUI()
    {
        messageCanvas = new GameObject("MessageCanvas_ColonySpawner"); 
        Canvas canvas = messageCanvas.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        CanvasScaler scaler = messageCanvas.AddComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1920, 1080); 
        messageCanvas.AddComponent<GraphicRaycaster>();
        
        GameObject textObject = new GameObject("MessageText_ColonySpawner");
        textObject.transform.SetParent(messageCanvas.transform);
        messageText = textObject.AddComponent<Text>(); 
        messageText.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf"); 
        messageText.alignment = TextAnchor.MiddleCenter;
        messageText.fontSize = 30; 
        messageText.color = new Color(0f, 0f, 0f, 1f); 
        messageText.fontStyle = FontStyle.Bold;

        Shadow shadow = textObject.AddComponent<Shadow>();
        shadow.effectColor = new Color(0.1f, 0.1f, 0.1f, 0.7f);
        shadow.effectDistance = new Vector2(2, -2);

        RectTransform textTransform = messageText.GetComponent<RectTransform>();
        textTransform.sizeDelta = new Vector2(Screen.width * 0.8f, 150); 
        textTransform.anchoredPosition = new Vector2(0, Screen.height * 0.35f); 
        
        messageCanvas.SetActive(false); 
    }

    public void ResetSimulation()
    {
        var queryDesc = new EntityQueryDesc
        {
            All = new[] { ComponentType.ReadOnly<SceneSection>() }, 
            None = new[] { ComponentType.ReadOnly<PrefabEntityComponent>(), ComponentType.ReadOnly<PlaneComponent>() }
        };
        EntityQuery entitiesToDestroyQuery = entityManager.CreateEntityQuery(queryDesc);
        NativeArray<Entity> entitiesToDestroy = entitiesToDestroyQuery.ToEntityArray(Allocator.TempJob);
        if (entitiesToDestroy.Length > 0)
        {
            entityManager.DestroyEntity(entitiesToDestroy);
        }
        entitiesToDestroy.Dispose();

        StopAllCoroutines(); 
        TogglePlacementPreviews(false);
        
        foreach(var config in organismConfigs)
        {
            config.countInput = Mathf.Max(0, defaultInitialCountForEachOrganism).ToString();
            config.radiusInput = Mathf.Clamp(defaultColonyRadiusForEachOrganism, 1f, 900f).ToString("F1", CultureInfo.InvariantCulture);
            config.currentCount = Mathf.Max(0, defaultInitialCountForEachOrganism);
            config.currentColonyRadius = Mathf.Clamp(defaultColonyRadiusForEachOrganism, 1f, 900f);
        }

        coloniesToPlace.Clear();
        currentPlacingColonyIndex = -1;
        currentConfigForPlacement = null;
        performanceWarningText = ""; 

        if (messageText != null) messageText.text = "Awaiting Initial Organism Setup...";
        currentPlacementState = PlacementState.Configuring;
        showConfigurationUI = true; 
        if(messageCanvas != null) messageCanvas.SetActive(false); 
        
        GameStateManager.ResetGameState();
    }

    void OnDestroy()
    {
        if (maxOriginBoundaryPreviewObject != null) Destroy(maxOriginBoundaryPreviewObject);
        if (colonyPreviewObject != null) Destroy(colonyPreviewObject);
        if (colonyFillPreviewObject != null) 
        {
            if (colonyFillMesh != null) Destroy(colonyFillMesh); 
            Destroy(colonyFillPreviewObject);
        }
        if (windowBackground != null) Destroy(windowBackground); 
    }
}
