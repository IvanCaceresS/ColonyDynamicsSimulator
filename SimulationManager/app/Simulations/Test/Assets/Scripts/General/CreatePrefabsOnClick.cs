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

private void CrearEntidad(Vector3 p)
{
    if(currentPrefabIndex>=prefabs.Count)return;
    var sQ=spawnerQuery.ToEntityArray(Allocator.Temp);
    if(currentPrefabIndex>=sQ.Length)
    {
        Debug.LogError($"No se encontró spawner en índice {currentPrefabIndex}");
        sQ.Dispose();
        return;
    }
    Entity s=sQ[currentPrefabIndex];
    sQ.Dispose();
    Entity pe=entityManager.GetComponentData<PrefabEntityComponent>(s).prefab;
    Entity e=entityManager.Instantiate(pe);
    float os=entityManager.GetComponentData<LocalTransform>(pe).Scale;
    quaternion or=entityManager.GetComponentData<LocalTransform>(pe).Rotation;
    float ry=UnityEngine.Random.Range(0f,360f);
    quaternion nr=math.mul(or,quaternion.RotateY(math.radians(ry)));
    float h=os*.5f;
    float3 ap=new float3(p.x,math.max(p.y+h,h),p.z);
    entityManager.SetComponentData(e,new LocalTransform
    {
        Position=ap,Rotation=nr,Scale=os
    }
    );
    string n=prefabs[currentPrefabIndex].name;
    switch(n)
    {
        case "EColi":entityManager.AddComponentData(e,new EColiComponent
        {
            TimeReference=1200f,SeparationThreshold=0.65f,MaxScale=1f,GrowthTime=0f,GrowthDuration=1200f*0.65f,TimeSinceLastDivision=0f,DivisionInterval=1200f*0.65f,HasGeneratedChild=false,Parent=Entity.Null,IsInitialCell=true,SeparationSign=0
        }
        );
        entityManager.AddComponent(e,typeof(NonUniformScale));
        entityManager.SetComponentData(e,new NonUniformScale
        {
            Value=new float3(.5f,1f,.5f)
        }
        );
        break;
        case "SCerevisiae":entityManager.AddComponentData(e,new SCerevisiaeComponent
        {
            TimeReference=5400f,SeparationThreshold=0.75f,MaxScale=5f,GrowthTime=0f,GrowthDuration=5400f*0.75f,TimeSinceLastDivision=0f,DivisionInterval=5400f*0.75f,HasGeneratedChild=false,Parent=Entity.Null,IsInitialCell=true,SeparationSign=0
        }
        );
        break;
        default:Debug.LogWarning($"No hay componente ECS para '{n}'");
        break;
    }
    AddPhysicsComponents(e,n,os);
    Debug.Log($"Entidad '{n}' creada en {ap}");
}
private void AddPhysicsComponents(Entity e,string n,float s)
{
    BlobAssetReference<Unity.Physics.Collider> c=default;
    Material m=new Material
    {
        Restitution=0f
    }
    ;
    switch(n)
    {
        case "EColi":c=Unity.Physics.CapsuleCollider.Create(new CapsuleGeometry
        {
            Vertex0=new float3(0,-.5f,0),Vertex1=new float3(0,.5f,0),Radius=.25f
        }
        ,CollisionFilter.Default,m);
        break;
        case "SCerevisiae":c=Unity.Physics.SphereCollider.Create(new SphereGeometry
        {
            Center=float3.zero,Radius=s*0.1f
        }
        ,CollisionFilter.Default,m);
        break;
        default:Debug.LogWarning($"No collider para '{n}'");
        return;
    }
    entityManager.AddComponentData(e,new PhysicsCollider
    {
        Value=c
    }
    );
    if(c.IsCreated)
    {
        var mp=c.Value.MassProperties;
        entityManager.AddComponentData(e,PhysicsMass.CreateDynamic(mp,1f));
    }
    entityManager.AddComponentData(e,new PhysicsVelocity
    {
        Linear=float3.zero,Angular=float3.zero
    }
    );
    entityManager.AddComponentData(e,new PhysicsGravityFactor
    {
        Value=1f
    }
    );
    entityManager.AddComponentData(e,new PhysicsDamping
    {
        Linear=0f,Angular=50f
    }
    );
    Debug.Log($"Física añadida a '{n}' (fricción alta, damping angular)");
}

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
