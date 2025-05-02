using UnityEngine;
using Unity.Entities;

public class PlaneAuthoring : MonoBehaviour
{
}

public class PlaneBaker : Baker<PlaneAuthoring>
{
    public override void Bake(PlaneAuthoring authoring)
    {
        var entity = GetEntity(TransformUsageFlags.None);
        AddComponent<PlaneComponent>(entity);
    }
}

public struct PlaneComponent : IComponentData {}
