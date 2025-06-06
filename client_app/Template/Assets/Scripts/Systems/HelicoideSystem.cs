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
public partial class HelicoideSystem : SystemBase
{
    protected override void OnUpdate()
    {
        if (!GameStateManager.IsSetupComplete || GameStateManager.IsPaused)
            return;

        float deltaTime = GameStateManager.DeltaTime; 
        float elapsedTimeForSeed = (float)SystemAPI.Time.ElapsedTime; 
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
        Dependency=Entities.WithReadOnly(parentMap).ForEach((Entity entity,int entityInQueryIndex,ref LocalTransform transform,ref HelicoideComponent organism)=>
        {
            if (organism.RandomState.state == 0)
            {
                uint seed = (uint)(entity.Index ^ (entity.Version << 16) ^ entityInQueryIndex) + (uint)(elapsedTimeForSeed * 1000.0f) + 1;
                organism.RandomState = new Unity.Mathematics.Random(seed == 0 ? 1u : seed);
            }
            bool isChild = organism.Parent != Entity.Null;
            if (!isChild && organism.IsInitialCell && !organism.TimeReferenceInitialized)
            {
                float randomMultiplier = organism.RandomState.NextFloat(0.9f, 1.1f);
                organism.TimeReference *= randomMultiplier;
                organism.TimeReferenceInitialized = true;
            }
            if (isChild)
            {
                bool childIsActivelySeparating = organism.CurrentAxialLength < organism.MaxAxialLength;
                if (childIsActivelySeparating)
                {
                    if (organism.ForwardSpeed > 0.00001f)
                    {
                        float distanceToMoveThisFrame = organism.ForwardSpeed * deltaTime;
                        float remainingDistance = organism.MaxAxialLength - organism.CurrentAxialLength;
                        float actualDistanceMovedThisFrame = math.min(distanceToMoveThisFrame, remainingDistance);
                        if (actualDistanceMovedThisFrame > 0.00001f) organism.CurrentAxialLength += actualDistanceMovedThisFrame;
                        else if (remainingDistance <= 0.00001f && remainingDistance >= 0f) organism.CurrentAxialLength = organism.MaxAxialLength;
                    }
                    if (organism.CurrentAxialLength >= organism.MaxAxialLength)
                    {
                        organism.CurrentAxialLength = organism.MaxAxialLength;
                        organism.ForwardSpeed = 0f;
                        childIsActivelySeparating = false;
                    }
                }
                if (parentMap.TryGetValue(organism.Parent, out ParentData parentInfo))
                {
                    float3 parentLocalYAxis = new float3(0f, 1f, 0f);
                    float3 separationAxisInWorld = math.mul(parentInfo.Rotation, parentLocalYAxis);
                    transform.Position = parentInfo.Position + (separationAxisInWorld * organism.SeparationSign * organism.CurrentAxialLength);
                    transform.Rotation = parentInfo.Rotation;
                }
                if (!childIsActivelySeparating && organism.Parent != Entity.Null)
                {
                    organism.Parent = Entity.Null;
                    organism.TimeSinceLastDivision = 0f;
                    organism.IsInitialCell = false;
                    organism.GrowthTime = organism.GrowthDuration;
                    float randomMultiplier = organism.RandomState.NextFloat(0.90f, 1.10f);
                    organism.DivisionInterval = organism.DivisionInterval * randomMultiplier;
                    organism.TimeReferenceInitialized = true;
                }
            }
            else 
            {
                if (organism.IsInitialCell && !organism.InitialPositionSet)
                {
                    transform.Position.y = 2f;
                    float randomHorizontalAngleRad = organism.RandomState.NextFloat(0f, 2f * math.PI);
                    quaternion randomYawRotation = quaternion.Euler(0, randomHorizontalAngleRad, 0);
                    quaternion lieDownRotation = quaternion.Euler(0, 0, math.radians(90f));
                    transform.Rotation = math.mul(lieDownRotation, randomYawRotation);
                    organism.InitialPositionSet = true;
                }

                bool parentIsWaitingOrJustDivided = false;
                if (!organism.IsInitialCell) parentIsWaitingOrJustDivided = organism.GrowthTime < organism.GrowthDuration && organism.GrowthDuration > 0.001f;
                if (organism.ForwardSpeed > 0.0001f && !parentIsWaitingOrJustDivided)
                {
                    float3 parentLocalUp = new float3(0f, 1f, 0f);
                    float3 worldMoveDirection = math.mul(transform.Rotation, parentLocalUp);
                    transform.Position += worldMoveDirection * organism.ForwardSpeed * deltaTime;
                }
                if (parentIsWaitingOrJustDivided)
                {
                    organism.GrowthTime += deltaTime;
                    if (organism.GrowthTime >= organism.GrowthDuration) organism.GrowthTime = organism.GrowthDuration;
                }
                organism.TimeSinceLastDivision += deltaTime;
                bool canDivide = false;
                float currentDivisionThreshold = organism.IsInitialCell ? organism.TimeReference : organism.DivisionInterval;
                if (organism.TimeSinceLastDivision >= currentDivisionThreshold && !parentIsWaitingOrJustDivided && currentDivisionThreshold > 0) canDivide = true;
                if (canDivide)
                {
                    Entity newChildEntity = ecb.Instantiate(entityInQueryIndex, entity);
                    LocalTransform childTransform = new LocalTransform {
                        Position = transform.Position, Rotation = transform.Rotation, Scale = transform.Scale
                    };
                    ecb.SetComponent(entityInQueryIndex, newChildEntity, childTransform);

                    HelicoideComponent cd = organism; 
                    cd.Parent = entity;
                    cd.IsInitialCell = false;
                    cd.TimeSinceLastDivision = 0f;
                    cd.TimeReferenceInitialized = true; 
                    cd.CurrentAxialLength = 0f;
                    cd.GrowthTime = 0f;
                    cd.ForwardSpeed = 0.3f; 
                    uint childSeed = (uint)(entity.Index ^ entity.Version ^ entityInQueryIndex ^ organism.RandomState.NextUInt()) + (uint)(elapsedTimeForSeed * 1000.0f) + 2;
                    cd.RandomState = new Unity.Mathematics.Random(childSeed == 0 ? 1u : childSeed); 
                    cd.SeparationSign = cd.RandomState.NextBool() ? 1 : -1;
                    cd.InitialPositionSet = false;
                    
                    ecb.SetComponent(entityInQueryIndex, newChildEntity, cd);
                    organism.TimeSinceLastDivision = 0f;
                    organism.GrowthTime = 0f; 
                    float randomMultiplierForParentInterval;
                    if (organism.IsInitialCell) {
                        organism.IsInitialCell = false; 
                        randomMultiplierForParentInterval = organism.RandomState.NextFloat(0.90f, 1.10f);
                        organism.DivisionInterval = organism.DivisionInterval * randomMultiplierForParentInterval;
                    } else {
                        randomMultiplierForParentInterval = organism.RandomState.NextFloat(0.90f, 1.10f);
                        organism.DivisionInterval = organism.DivisionInterval * randomMultiplierForParentInterval;
                    }
                }
            }
            float maxVibrationAngleDeg = 1.0f; 
            float randomAngleDeg = organism.RandomState.NextFloat(-maxVibrationAngleDeg, maxVibrationAngleDeg);
            float randomAngleRad = math.radians(randomAngleDeg);
            quaternion localYVibration = quaternion.Euler(0, randomAngleRad, 0);
            transform.Rotation = math.mul(transform.Rotation, localYVibration);
            transform.Position.y = math.max(transform.Position.y, -0.3f); 

        }).ScheduleParallel(Dependency);
        ecbSystem.AddJobHandleForProducer(Dependency);
        Dependency = parentMap.Dispose(Dependency);
    }

}