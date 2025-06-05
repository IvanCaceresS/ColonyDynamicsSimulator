using Unity.Entities;
using Unity.Mathematics;
public struct CoccoComponent:IComponentData
{
    public float TimeReference,MaxScale,GrowthTime,GrowthDuration,TimeSinceLastDivision,DivisionInterval,SeparationThreshold;
    public bool IsInitialCell,TimeReferenceInitialized;
    public Entity Parent;
    public float3 GrowthDirection;
}