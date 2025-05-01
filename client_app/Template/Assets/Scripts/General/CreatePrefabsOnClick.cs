using UnityEngine;
using Unity.Entities;
using Unity.Mathematics;
using Unity.Transforms;
using Unity.Rendering;
using Unity.Collections;
using Unity.Physics;
using Unity.Physics.Authoring;
using UnityEngine.UI;
using System.Collections;
using System.Collections.Generic;

using Material = Unity.Physics.Material;

public class CreatePrefabsOnClick : MonoBehaviour
{
    private Camera mainCamera;
    private List<GameObject> prefabs;
    private int currentPrefabIndex = 0;
    private bool isWaitingForClick = false;
    private GameObject messageCanvas;
    private Text messageText;
    private EntityManager entityManager;
    private EntityQuery spawnerQuery;

    void Start()
    {
        mainCamera = Camera.main;
        if (mainCamera == null)
        {
            Debug.LogError("CreatePrefabsOnClick: No main camera found.");
            return;
        }

        entityManager = World.DefaultGameObjectInjectionWorld.EntityManager;
        CrearMensajeUI();
        CargarPrefabs();

        if (prefabs.Count == 0)
        {
            Debug.LogError("No prefabs found in Resources/Prefabs.");
            return;
        }

        Debug.Log($"Found {prefabs.Count} prefabs.");

        spawnerQuery = entityManager.CreateEntityQuery(typeof(PrefabEntityComponent));

        SolicitarColocacion();
    }

    void Update()
    {
        if (isWaitingForClick && Input.GetMouseButtonDown(0))
        {
            UnityEngine.Ray ray = mainCamera.ScreenPointToRay(Input.mousePosition);
            if (UnityEngine.Physics.Raycast(ray, out UnityEngine.RaycastHit hit))
            {
                Vector3 spawnPosition = hit.point;
                CrearEntidad(spawnPosition);
                currentPrefabIndex++;
                if (currentPrefabIndex < prefabs.Count)
                {
                    SolicitarColocacion();
                }
                else
                {
                    OnAllPrefabsPlaced();
                }
            }
        }
    }

    private void CargarPrefabs(){prefabs = new List<GameObject>(Resources.LoadAll<GameObject>("Prefabs"));}

    private void SolicitarColocacion()
    {
        if (currentPrefabIndex >= prefabs.Count) return;

        string prefabName = prefabs[currentPrefabIndex].name;
        messageText.text = $"Please click to place '{prefabName}'.";
        isWaitingForClick = true;
    }

    private void OnAllPrefabsPlaced()
    {
        Debug.Log("All prefabs have been placed.");
        messageText.text = "All prefabs have been placed.";
        isWaitingForClick = false;
        StartCoroutine(ShowFinalMessageAndCompleteSetup());
    }

    private IEnumerator ShowFinalMessageAndCompleteSetup()
    {
        yield return new WaitForSeconds(0.5f);
        messageCanvas.SetActive(false);

        GameStateManager.CompleteSetup();
    }

    private void CrearMensajeUI()
    {
        messageCanvas = new GameObject("MessageCanvas");
        Canvas canvas = messageCanvas.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        messageCanvas.AddComponent<CanvasScaler>().uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        messageCanvas.AddComponent<GraphicRaycaster>();

        GameObject textObject = new GameObject("MessageText");
        textObject.transform.SetParent(messageCanvas.transform);
        messageText = textObject.AddComponent<Text>();
        messageText.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        messageText.alignment = TextAnchor.MiddleCenter;
        messageText.fontSize = 16;
        messageText.color = Color.black;
        messageText.fontStyle = FontStyle.BoldAndItalic;

        RectTransform textTransform = messageText.GetComponent<RectTransform>();
        textTransform.sizeDelta = new Vector2(1000, 100);
        textTransform.anchoredPosition = new Vector2(0, 200);
        messageCanvas.SetActive(true);
    }

    public void ResetSimulation()
    {
        var queryDesc = new EntityQueryDesc
        {
            All = new[] { ComponentType.ReadOnly<SceneSection>() },
            None = new[]
            {
                ComponentType.ReadOnly<PrefabEntityComponent>(),
                ComponentType.ReadOnly<PlaneComponent>()
            }
        };

        var subsceneQuery = entityManager.CreateEntityQuery(queryDesc);
        var toDestroy = subsceneQuery.ToEntityArray(Allocator.Temp);

        entityManager.DestroyEntity(toDestroy);
        toDestroy.Dispose();

        Debug.Log("Entities have been deleted except for spawners and plane.");

        currentPrefabIndex = 0;
        isWaitingForClick = false;
        messageCanvas.SetActive(true);

        SolicitarColocacion();
    }
}
