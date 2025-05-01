using UnityEditor;
using UnityEngine;

public class BuildScript
{
    public static void PerformBuild()
    {
        // Lista de escenas a incluir (asegúrate de que la ruta de la escena sea correcta)
        string[] scenes = { "Assets/Scenes/SampleScene.unity" };

        // Variables para el build target y la ruta de salida.
        BuildTarget target;
        string buildPath;

        // Se utilizan directivas de compilación para definir el target según el Editor:
#if UNITY_EDITOR_WIN
        target = BuildTarget.StandaloneWindows64;
        buildPath = "Build/Windows/Simulation.exe";
#elif UNITY_EDITOR_OSX
        target = BuildTarget.StandaloneOSX;
        buildPath = "Build/Mac/Simulation.app";
#elif UNITY_EDITOR_LINUX
        target = BuildTarget.StandaloneLinux64;
        buildPath = "Build/Linux/Simulation";
#else
        // Por defecto, si no se detecta ninguno de los anteriores se utiliza Windows.
        target = BuildTarget.StandaloneWindows64;
        buildPath = "Build/Windows/Simulation.exe";
#endif

        // Opciones de construcción
        BuildPlayerOptions buildPlayerOptions = new BuildPlayerOptions
        {
            scenes = scenes,
            locationPathName = buildPath,
            target = target,
            options = BuildOptions.None
        };

        // Ejecuta el build
        BuildPipeline.BuildPlayer(buildPlayerOptions);
    }
}
