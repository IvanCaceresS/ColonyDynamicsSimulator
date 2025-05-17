using UnityEngine;

public class GameStyleCamera : MonoBehaviour
{
    [Header("Movimiento")]
    public float moveSpeed = 20f;
    public float verticalSpeed = 20f;
    public float moveSmoothTime = 0.1f;

    [Header("Rotación")]
    public float rotationSpeed = 200f;
    public float rotationSmoothTime = 0.05f;

    [Header("Zoom")]
    public float zoomSpeed = 15f; 
    public float minZoom = 5f;
    public float maxZoom = 60f;
    public float zoomSmoothTime = 0.1f;

    [Header("Restricciones")]
    public float maxDistance = 200f;
    public float minHeight = 0.5f;

    [Header("Apariencia")]
    public Color backgroundColor = new Color(194f/255f, 218f/255f, 255f/255f, 1f); // #C2DAFF

    private float currentActualFOV;
    private float targetDesiredFOV;
    private float fovVelocityRef;

    private float currentYaw;
    private float currentPitch;
    private float yawVelocityRef;
    private float pitchVelocityRef;

    private Vector3 smoothedMoveInput = Vector3.zero;
    private Vector3 moveInputVelocity = Vector3.zero;

    private Vector3 freeCameraSmoothedPosition;
    private Quaternion freeCameraSmoothedRotation;
    private float freeCameraTargetDesiredFOV;

    private readonly Vector3 topDownPosition = new Vector3(0, 250, 0);
    private readonly Quaternion topDownRotation = Quaternion.Euler(90, 0, 0);
    private bool isTopDownView = false;
    
    private Vector3 initialPosition;
    private Quaternion initialRotation;
    private float initialTargetDesiredFOV;

    private bool wasSetupCompletedLastFrame = false;
    private bool wasAcceptingInputLastFrame = false;

    void Start()
    {
        initialPosition = transform.position;
        initialRotation = transform.rotation;
        initialTargetDesiredFOV = maxZoom;

        targetDesiredFOV = initialTargetDesiredFOV;
        if (Camera.main != null)
        {
            Camera.main.clearFlags = CameraClearFlags.SolidColor;
            Camera.main.backgroundColor = backgroundColor;
            Camera.main.fieldOfView = targetDesiredFOV;
        }
        currentActualFOV = targetDesiredFOV;

        currentYaw = initialRotation.eulerAngles.y;
        currentPitch = initialRotation.eulerAngles.x;
        transform.rotation = initialRotation;
        transform.position = initialPosition;
        
        freeCameraSmoothedPosition = initialPosition;
        freeCameraSmoothedRotation = initialRotation;
        freeCameraTargetDesiredFOV = initialTargetDesiredFOV;

        Cursor.visible = true;
        Cursor.lockState = CursorLockMode.None;

        wasSetupCompletedLastFrame = GameStateManager.IsSetupComplete;
        wasAcceptingInputLastFrame = wasSetupCompletedLastFrame && !GameStateManager.IsPaused;

        if (!wasSetupCompletedLastFrame)
        {
            ResetCameraToInitialState(); 
        }
    }

    private void ResetCameraToInitialState()
    {
        transform.position = initialPosition;
        transform.rotation = initialRotation;

        targetDesiredFOV = initialTargetDesiredFOV;
        currentActualFOV = initialTargetDesiredFOV;
        if (Camera.main != null)
        {
            Camera.main.fieldOfView = initialTargetDesiredFOV;
            Camera.main.backgroundColor = backgroundColor; // Re-apply on reset
        }

        currentYaw = initialRotation.eulerAngles.y;
        currentPitch = initialRotation.eulerAngles.x;

        yawVelocityRef = 0f;
        pitchVelocityRef = 0f;
        fovVelocityRef = 0f;
        smoothedMoveInput = Vector3.zero;
        moveInputVelocity = Vector3.zero;

        isTopDownView = false;

        freeCameraSmoothedPosition = initialPosition;
        freeCameraSmoothedRotation = initialRotation;
        freeCameraTargetDesiredFOV = initialTargetDesiredFOV;

        Cursor.lockState = CursorLockMode.None;
        Cursor.visible = true;
    }

    void Update()
    {
        bool isSetupNow = GameStateManager.IsSetupComplete;
        bool isPausedNow = GameStateManager.IsPaused;
        bool canAcceptInputNow = isSetupNow && !isPausedNow;

        if (!isSetupNow)
        {
            if (wasSetupCompletedLastFrame)
            {
                ResetCameraToInitialState();
            }
            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;
        }
        else
        {
            if (canAcceptInputNow)
            {
                if (!wasAcceptingInputLastFrame)
                {
                    currentYaw = transform.eulerAngles.y;
                    currentPitch = transform.eulerAngles.x;
                    targetDesiredFOV = Camera.main != null ? Camera.main.fieldOfView : initialTargetDesiredFOV;
                    currentActualFOV = targetDesiredFOV;
                    yawVelocityRef = 0f;
                    pitchVelocityRef = 0f;
                    fovVelocityRef = 0f;
                    moveInputVelocity = Vector3.zero;
                }

                if (Input.GetKeyDown(KeyCode.C))
                {
                    ToggleCameraMode();
                }

                if (!isTopDownView)
                {
                    HandleRotation();
                    HandleMovement();
                    HandleZoom();
                }
                else
                {
                    Cursor.lockState = CursorLockMode.None;
                    Cursor.visible = true;
                }
            }
            else 
            {
                Cursor.lockState = CursorLockMode.None;
                Cursor.visible = true;
            }
        }
        wasSetupCompletedLastFrame = isSetupNow;
        wasAcceptingInputLastFrame = canAcceptInputNow;
    }

    private void HandleRotation()
    {
        float targetYaw = currentYaw;
        float targetPitch = currentPitch;

        if (Input.GetMouseButton(1))
        {
            Cursor.lockState = CursorLockMode.Locked;
            Cursor.visible = false;

            float mouseX = Input.GetAxis("Mouse X") * rotationSpeed;
            float mouseY = Input.GetAxis("Mouse Y") * rotationSpeed;

            targetYaw += mouseX * Time.deltaTime;
            targetPitch -= mouseY * Time.deltaTime;
            targetPitch = Mathf.Clamp(targetPitch, -89f, 89f);
        }
        else
        {
            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;
        }
        
        currentYaw = Mathf.SmoothDampAngle(currentYaw, targetYaw, ref yawVelocityRef, rotationSmoothTime);
        currentPitch = Mathf.SmoothDampAngle(currentPitch, targetPitch, ref pitchVelocityRef, rotationSmoothTime);
        transform.rotation = Quaternion.Euler(currentPitch, currentYaw, 0f);
    }

    private void HandleMovement()
    {
        float horiz = Input.GetAxis("Horizontal");
        float vert = Input.GetAxis("Vertical");
        Vector3 rawInput = new Vector3(horiz, 0, vert);
        smoothedMoveInput = Vector3.SmoothDamp(smoothedMoveInput, rawInput, ref moveInputVelocity, moveSmoothTime);

        Vector3 move = transform.right * smoothedMoveInput.x + transform.forward * smoothedMoveInput.z;
        move = move.normalized * new Vector2(smoothedMoveInput.x, smoothedMoveInput.z).magnitude;
        move *= moveSpeed;

        if (Input.GetKey(KeyCode.Space))
            move.y += verticalSpeed;
        if (Input.GetKey(KeyCode.LeftControl))
            move.y -= verticalSpeed;

        transform.position += move * Time.deltaTime;
        RestrictPosition();
    }

    private void HandleZoom()
    {
        float scroll = Input.GetAxis("Mouse ScrollWheel");
        if (scroll != 0)
        {
            targetDesiredFOV = Mathf.Clamp(targetDesiredFOV - scroll * zoomSpeed, minZoom, maxZoom);
        }
        if (Camera.main != null)
        {
            currentActualFOV = Mathf.SmoothDamp(Camera.main.fieldOfView, targetDesiredFOV, ref fovVelocityRef, zoomSmoothTime);
            Camera.main.fieldOfView = currentActualFOV;
        }
    }

    private void RestrictPosition()
    {
        Vector3 pos = transform.position;
        if (Vector3.Distance(pos, Vector3.zero) > maxDistance)
        {
            pos = Vector3.zero + (pos - Vector3.zero).normalized * maxDistance;
        }
        pos.y = Mathf.Max(pos.y, minHeight);
        transform.position = pos;
    }

    public void ToggleCameraMode()
    {
        isTopDownView = !isTopDownView;

        if (isTopDownView)
        {
            freeCameraSmoothedPosition = transform.position;
            freeCameraSmoothedRotation = transform.rotation;
            freeCameraTargetDesiredFOV = targetDesiredFOV; 

            transform.position = topDownPosition;
            transform.rotation = topDownRotation;
            
            currentYaw = topDownRotation.eulerAngles.y;
            currentPitch = topDownRotation.eulerAngles.x;
            
            smoothedMoveInput = Vector3.zero;
            moveInputVelocity = Vector3.zero;
            yawVelocityRef = 0f;
            pitchVelocityRef = 0f;
            fovVelocityRef = 0f;
        }
        else
        {
            transform.position = freeCameraSmoothedPosition;
            transform.rotation = freeCameraSmoothedRotation;

            currentYaw = freeCameraSmoothedRotation.eulerAngles.y;
            currentPitch = freeCameraSmoothedRotation.eulerAngles.x;
            targetDesiredFOV = freeCameraTargetDesiredFOV;
            
            smoothedMoveInput = Vector3.zero;
            moveInputVelocity = Vector3.zero;
            yawVelocityRef = 0f;
            pitchVelocityRef = 0f;
            fovVelocityRef = 0f; 
        }
    }
}
