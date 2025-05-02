using UnityEditor;
using UnityEngine;

public class BuildScript
{
    public static void PerformBuild()
    {
        string[] scenes = { "Assets/Scenes/SampleScene.unity" };

        BuildTarget target;
        string buildPath;

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
        target = BuildTarget.StandaloneWindows64;
        buildPath = "Build/Windows/Simulation.exe";
#endif

        BuildPlayerOptions buildPlayerOptions = new BuildPlayerOptions
        {
            scenes = scenes,
            locationPathName = buildPath,
            target = target,
            options = BuildOptions.None
        };

        BuildPipeline.BuildPlayer(buildPlayerOptions);
    }
}
