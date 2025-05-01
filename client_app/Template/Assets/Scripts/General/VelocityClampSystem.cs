using Unity.Entities;
using Unity.Mathematics;
using Unity.Physics;

[UpdateInGroup(typeof(SimulationSystemGroup))]
// Opcional: [AlwaysUpdateSystem] para garantizar que se ejecute cada frame
public partial class VelocityClampSystem : SystemBase
{
    protected override void OnUpdate()
    {
        // Define umbrales máximos para velocidad lineal y angular
        float maxLinear = 0.5f;   // Ajusta este valor según lo que consideres realista
        float maxAngular = 0.5f;  // Ajusta este valor según lo que consideres realista

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
