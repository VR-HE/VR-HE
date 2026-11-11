// VR-HE interactive browser demo: walking, camera height, first/third-person views.
//
// Coordinates: metres, Unity world axes (x right, y up, z forward), floor at y = 0, the same
// frame as the synthetic room generator. Angles are degrees; yaw 0 faces +z, positive pitch
// looks down (Unity's convention for rotation about x).
//
// The values below are prototype implementation choices, not confirmed user decisions. They
// are serialized so they can be tuned in the scene or replaced by a settings file later.
// Physical scale accuracy is not demonstrated: the room is synthetic and the 1.73 m avatar is
// a scale cue only.
//
// Collision uses a CharacterController against the proxy floor, wall and rack boxes from the
// site file. The splat itself has no collision.

using UnityEngine;

namespace VRHE.InteractiveDemo
{
    [RequireComponent(typeof(CharacterController))]
    public sealed class DemoPlayer : MonoBehaviour
    {
        public enum ViewMode
        {
            FirstPerson,
            ThirdPerson
        }

        [Header("Walking")]
        public float walkSpeed = 1.3f;
        public float fastSpeed = 2.6f;  // while Shift is held
        public float keyTurnDegreesPerSecond = 90f;
        public float gravity = 9.81f;

        [Header("Camera height (Q raises, E lowers, X resets)")]
        public float eyeHeight = 1.6f;  // normal first-person eye height above the floor
        public float heightSpeed = 0.6f;
        public float minHeightOffset = -0.9f;
        public float maxHeightOffset = 1.0f;

        [Header("Looking")]
        public float lookDegreesPerPixel = 0.15f;
        public float firstPersonPitchLimit = 80f;

        [Header("Third person (V switches)")]
        // Orbit centre above the feet. 0.4 m above eye height, so a level (pitch 0) third-person
        // view looks over the avatar's head instead of into the back of it.
        public float orbitCenterHeight = 2.0f;
        public float orbitDistance = 2.6f;
        public float minOrbitDistance = 1.2f;
        public float maxOrbitDistance = 5f;
        public float zoomMetresPerNotch = 0.35f;
        public float orbitMinPitch = -30f;
        public float orbitMaxPitch = 70f;
        public float avatarTurnDegreesPerSecond = 540f;
        public float cameraCollisionRadius = 0.15f;
        public float cameraReturnSpeed = 3f;   // m/s when easing back out after a wall
        public float hideAvatarCloserThan = 0.6f;
        public ViewMode startView = ViewMode.FirstPerson;

        [Header("Scene references")]
        public Transform avatar;  // visual only; no colliders

        Camera m_camera;
        CharacterController m_controller;
        Renderer[] m_avatarRenderers = new Renderer[0];
        float m_viewYaw, m_pitch, m_bodyYaw, m_heightOffset, m_verticalVelocity, m_cameraDistance;
        bool m_avatarVisible = true;

        public ViewMode View { get; private set; }
        public float ViewYaw => m_viewYaw;
        public float Pitch => m_pitch;
        public float BodyYaw => m_bodyYaw;
        public float HeightOffset => m_heightOffset;
        public float CameraDistance => m_cameraDistance;
        public bool IsMoving { get; private set; }
        public bool IsChangingHeight { get; private set; }
        public bool IsLooking { get; private set; }
        public Vector3 Feet => transform.position;
        public Camera ViewCamera => m_camera;
        public float LookSpeedMultiplier { get; set; } = 1f;

        float PitchMin => View == ViewMode.FirstPerson ? -firstPersonPitchLimit : orbitMinPitch;
        float PitchMax => View == ViewMode.FirstPerson ? firstPersonPitchLimit : orbitMaxPitch;

        public void Initialize(Camera viewCamera)
        {
            m_camera = viewCamera;
            m_controller = GetComponent<CharacterController>();
            if (avatar)
                m_avatarRenderers = avatar.GetComponentsInChildren<Renderer>(true);
        }

        public void Spawn(Vector3 feet, float yawDegrees)
        {
            m_controller.enabled = false;
            transform.SetPositionAndRotation(feet + Vector3.up * (m_controller.skinWidth + 0.01f),
                Quaternion.Euler(0f, yawDegrees, 0f));
            m_controller.enabled = true;
            m_viewYaw = m_bodyYaw = yawDegrees;
            m_pitch = 0f;
            m_heightOffset = 0f;
            m_verticalVelocity = 0f;
            View = startView;
            m_cameraDistance = View == ViewMode.ThirdPerson ? orbitDistance : 0f;
            UpdateCamera(0f);
        }

        public void Tick(in DemoInputFrame input, float dt)
        {
            var look = input.LookPixels * (lookDegreesPerPixel * LookSpeedMultiplier);
            IsLooking = look.sqrMagnitude > 0f;
            m_viewYaw = Mathf.Repeat(m_viewYaw + look.x + input.Turn * keyTurnDegreesPerSecond * dt, 360f);
            m_pitch = Mathf.Clamp(m_pitch + look.y, PitchMin, PitchMax);

            if (View == ViewMode.ThirdPerson && input.Zoom != 0f)
                orbitDistance = Mathf.Clamp(orbitDistance + input.Zoom * zoomMetresPerNotch, minOrbitDistance, maxOrbitDistance);

            IsChangingHeight = input.Height != 0f;
            m_heightOffset = Mathf.Clamp(m_heightOffset + input.Height * heightSpeed * dt, minHeightOffset, maxHeightOffset);

            if (input.ToggleView)
                SetView(View == ViewMode.FirstPerson ? ViewMode.ThirdPerson : ViewMode.FirstPerson);
            if (input.ResetView)
                ResetView();

            // Movement is relative to where the camera looks, in both views (strafing in third person).
            var wish = Quaternion.Euler(0f, m_viewYaw, 0f) * new Vector3(input.Move.x, 0f, input.Move.y);
            IsMoving = wish.sqrMagnitude > 1e-4f;
            var velocity = wish * (input.Fast ? fastSpeed : walkSpeed);
            if (m_controller.isGrounded && m_verticalVelocity < 0f)
                m_verticalVelocity = -1f;  // keep contact with the floor
            else
                m_verticalVelocity -= gravity * dt;
            velocity.y = m_verticalVelocity;
            m_controller.Move(velocity * dt);

            if (View == ViewMode.FirstPerson)
                m_bodyYaw = m_viewYaw;
            else if (IsMoving)
                m_bodyYaw = Mathf.MoveTowardsAngle(m_bodyYaw, m_viewYaw, avatarTurnDegreesPerSecond * dt);
            transform.rotation = Quaternion.Euler(0f, m_bodyYaw, 0f);
        }

        /// <summary>X: normal height, level view; in third person also back behind the avatar.
        /// It never turns the avatar.</summary>
        public void ResetView()
        {
            m_heightOffset = 0f;
            m_pitch = 0f;
            if (View == ViewMode.ThirdPerson)
                m_viewYaw = m_bodyYaw;
        }

        public void SetView(ViewMode mode)
        {
            if (mode == View)
                return;
            if (mode == ViewMode.FirstPerson)
                m_bodyYaw = m_viewYaw;  // keep looking where the camera looked
            else
                m_cameraDistance = 0.3f;  // ease out from the head
            View = mode;
            m_pitch = Mathf.Clamp(m_pitch, PitchMin, PitchMax);
        }

        /// <summary>Turns the view and the avatar toward a world point (equipment list "Show").</summary>
        public void FaceTowards(Vector3 target)
        {
            var flat = target - transform.position;
            flat.y = 0f;
            if (flat.sqrMagnitude < 1e-4f)
                return;
            m_viewYaw = m_bodyYaw = Mathf.Atan2(flat.x, flat.z) * Mathf.Rad2Deg;
            transform.rotation = Quaternion.Euler(0f, m_bodyYaw, 0f);
            m_pitch = View == ViewMode.FirstPerson
                ? Mathf.Clamp(Mathf.Atan2(eyeHeight + m_heightOffset - target.y, flat.magnitude) * Mathf.Rad2Deg, -firstPersonPitchLimit, firstPersonPitchLimit)
                : Mathf.Clamp(10f, orbitMinPitch, orbitMaxPitch);
        }

        void LateUpdate() => UpdateCamera(Time.deltaTime);

        void UpdateCamera(float dt)
        {
            if (!m_camera)
                return;
            var rotation = Quaternion.Euler(m_pitch, m_viewYaw, 0f);
            var feet = transform.position;
            if (View == ViewMode.FirstPerson)
            {
                m_cameraDistance = 0f;
                m_camera.transform.SetPositionAndRotation(feet + Vector3.up * (eyeHeight + m_heightOffset), rotation);
            }
            else
            {
                var center = feet + Vector3.up * (orbitCenterHeight + m_heightOffset);
                var back = rotation * Vector3.back;
                var allowed = orbitDistance;
                // The player is on the Ignore Raycast layer, so the cast only meets proxies.
                if (Physics.SphereCast(center, cameraCollisionRadius, back, out var hit, orbitDistance,
                        Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore))
                    allowed = Mathf.Max(0.05f, hit.distance);
                m_cameraDistance = allowed <= m_cameraDistance || dt <= 0f
                    ? allowed
                    : Mathf.MoveTowards(m_cameraDistance, allowed, cameraReturnSpeed * dt);
                m_camera.transform.SetPositionAndRotation(center + back * m_cameraDistance, rotation);
            }
            SetAvatarVisible(View == ViewMode.ThirdPerson && m_cameraDistance >= hideAvatarCloserThan);
        }

        void SetAvatarVisible(bool visible)
        {
            if (visible == m_avatarVisible)
                return;
            m_avatarVisible = visible;
            foreach (var r in m_avatarRenderers)
                if (r)
                    r.enabled = visible;
        }
    }
}
