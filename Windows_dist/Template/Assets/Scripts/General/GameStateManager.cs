using System;
using UnityEngine;

public static class GameStateManager
{
    public static bool IsSetupComplete { get; set; } = false;
    public static bool IsPaused { get; private set; } = true;
    public static event Action OnSetupComplete;

    public static float DeltaTime { get; private set; } = 1.00f;

    public static void CompleteSetup()
    {
        IsSetupComplete = true;
        Debug.Log("GameStateManager: Setup complete, firing event.");
        OnSetupComplete?.Invoke();
    }

    public static void ResetGameState()
    {
        IsSetupComplete = false;
        IsPaused = true;
        DeltaTime = 1.00f;
        Debug.Log("GameStateManager: Resetting game state.");
    }

    public static void SetDeltaTime(float value)
    {
        DeltaTime = Mathf.Clamp(value, 0.01f, 99.99f);
        Debug.Log($"GameStateManager: DeltaTime updated to {DeltaTime:F2}");
    }

    public static void SetPauseState(bool pause)
    {
        IsPaused = pause;
    }
}