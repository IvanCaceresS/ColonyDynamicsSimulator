using Unity.Entities;
using Unity.Mathematics;
public struct EColiComponent:IComponentData
{
    public float TimeReference,MaxScale,GrowthTime,GrowthDuration,TimeSinceLastDivision,DivisionInterval,SeparationThreshold;
    public bool HasGeneratedChild,IsInitialCell,TimeReferenceInitialized;
    public Entity Parent;
    public int SeparationSign;
}