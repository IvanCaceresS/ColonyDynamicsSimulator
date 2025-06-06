using Unity.Entities;
using Unity.Mathematics;

public struct HelicoideComponent:IComponentData
{
    public float CurrentAxialLength,MaxAxialLength,GrowthTime,GrowthDuration,TimeSinceLastDivision,DivisionInterval,TimeReference,ForwardSpeed;
    public bool IsInitialCell,TimeReferenceInitialized,InitialPositionSet;
    public Entity Parent;
    public int SeparationSign;
    public Unity.Mathematics.Random RandomState;
}
