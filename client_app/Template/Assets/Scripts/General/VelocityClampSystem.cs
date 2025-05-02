using Unity.Entities;
using Unity.Mathematics;
using Unity.Physics;

[UpdateInGroup(typeof(SimulationSystemGroup))]
public partial class VelocityClampSystem : SystemBase
{
    protected override void OnUpdate()
    {
        float maxLinear = 0.5f;
        float maxAngular = 0.5f;

        Entities.ForEach((ref PhysicsVelocity velocity) =>
        {
            float linearMag = math.length(velocity.Linear);
            if (linearMag > maxLinear)
            {
                velocity.Linear = (velocity.Linear / linearMag) * maxLinear;
            }
            float angularMag = math.length(velocity.Angular);
            if (angularMag > maxAngular)
            {
                velocity.Angular = (velocity.Angular / angularMag) * maxAngular;
            }
        }).ScheduleParallel();
    }
}
