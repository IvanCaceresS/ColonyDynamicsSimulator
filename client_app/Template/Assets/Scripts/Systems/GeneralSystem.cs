using Unity.Burst;
using Unity.Collections;
using Unity.Entities;
using Unity.Jobs;
using Unity.Mathematics;
using Unity.Physics;
using Unity.Physics.Extensions;
using Unity.Transforms;
using UnityEngine;

[BurstCompile]
[UpdateInGroup(typeof(SimulationSystemGroup))]
public partial class GeneralSystem : SystemBase
{
    protected override void OnUpdate()
    {
        if (!GameStateManager.IsSetupComplete || GameStateManager.IsPaused)
            return;

        float deltaTime = GameStateManager.DeltaTime;
        EntityQuery query = GetEntityQuery(typeof(LocalTransform));
        int capacity = math.max(1024, query.CalculateEntityCount() * 2);
        NativeParallelHashMap<Entity, ParentData> parentMap =
            new NativeParallelHashMap<Entity, ParentData>(capacity, Allocator.TempJob);
        var parentMapWriter = parentMap.AsParallelWriter();
        Dependency = Entities.ForEach((Entity e, in LocalTransform transform) =>
        {
            parentMapWriter.TryAdd(e, new ParentData
            {
                Position = transform.Position,
                Rotation = transform.Rotation,
                Scale    = transform.Scale
            });
        }).ScheduleParallel(Dependency);

        EndSimulationEntityCommandBufferSystem ecbSystem =
            World.GetOrCreateSystemManaged<EndSimulationEntityCommandBufferSystem>();
        var ecb = ecbSystem.CreateCommandBuffer().AsParallelWriter();
        Dependency=Entities.WithReadOnly(parentMap).ForEach((Entity entity,int entityInQueryIndex,ref LocalTransform transform,ref GeneralComponent organism)=>
        {   
            if (!organism.TimeReferenceInitialized)
            {
                Unity.Mathematics.Random rng = new Unity.Mathematics.Random((uint)(entityInQueryIndex + 1) * 99999);
                float randomMultiplier = rng.NextFloat(0.9f, 1.1f);
                organism.TimeReference *= randomMultiplier;
                organism.TimeReferenceInitialized = true;
            }
            float maxScale=organism.MaxScale;
            organism.GrowthDuration=organism.DivisionInterval=organism.TimeReference*organism.SeparationThreshold;
            if(transform.Scale<maxScale)
            {
                organism.GrowthTime+=deltaTime;
                float t=math.clamp(organism.GrowthTime/organism.GrowthDuration,0f,1f);
                float initialScale=organism.IsInitialCell?maxScale:0.01f;
                transform.Scale=math.lerp(initialScale,maxScale,t);}




            ecb.SetComponent(entityInQueryIndex, entity, transform);
            ecb.SetComponent(entityInQueryIndex, entity, organism);
        }).ScheduleParallel(Dependency);
        ecbSystem.AddJobHandleForProducer(Dependency);
        Dependency = parentMap.Dispose(Dependency);
    }
}
