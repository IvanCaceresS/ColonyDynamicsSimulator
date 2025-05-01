using UnityEngine;
using Unity.Entities;

public class PlaneAuthoring : MonoBehaviour
{
    // Este script actúa como marcador para la conversión a ECS.
}

public class PlaneBaker : Baker<PlaneAuthoring>
{
    public override void Bake(PlaneAuthoring authoring)
    {
        var entity = GetEntity(TransformUsageFlags.None);

        // Agregar un componente vacío para identificar el plano en ECS
        AddComponent<PlaneComponent>(entity);
    }
}

// Componente ECS para el plano
public struct PlaneComponent : IComponentData {}
