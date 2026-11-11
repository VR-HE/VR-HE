// VR-HE interactive browser demo: input adapters.
//
// Gameplay code reads one DemoInputFrame per update and never touches devices directly. That
// keeps the device question in one place:
//   BrowserInputSource  keyboard through the Input System (Unity only receives keys while the
//                       canvas has focus, because DemoApp sets captureAllKeyboardInput = false);
//                       mouse through the page (demo-ui.js), which owns pointer lock, the
//                       context menu and the click-versus-drag decision.
//   EditorInputSource   keyboard and mouse through the Input System, for Editor play mode.
// Extension points: a touch source (on-screen sticks, height and view buttons) or an XR source
// (6DoF head pose, controller rays) would produce the same frame. Requirements for phone and
// Quest control remain open and are not implemented here.
//
// DemoInput applies the page's gate: while a text field or panel has focus, it returns empty
// frames, drops queued clicks and forgets held keys, so a key released inside a text field can
// never leave the camera moving.

using UnityEngine;
using UnityEngine.InputSystem;

namespace VRHE.InteractiveDemo
{
    public struct DemoInputFrame
    {
        public Vector2 Move;            // x = step right, y = step forward, each -1..1
        public float Turn;              // keyboard turn, -1 left .. 1 right
        public bool Fast;               // Shift
        public float Height;            // 1 = raise camera (Q), -1 = lower (E)
        public bool ResetView;          // X
        public bool ToggleView;         // V
        public Vector2 LookPixels;      // pointer motion in CSS pixels, x right, y down
        public float Zoom;              // wheel notches, positive = farther
        public bool Select;             // left click without dragging
        public Vector2 SelectPosition;  // Unity screen pixels (origin bottom-left)
        public bool Open;               // right click
        public Vector2 OpenPosition;
        public Vector2 PointerPosition;
        public bool PointerOverView;
        public bool PointerLocked;
        public bool Dragging;

        public bool HasMovement => Move.sqrMagnitude > 0f || Turn != 0f;
        public bool HasLook => LookPixels.sqrMagnitude > 0f;
    }

    public interface IDemoInputSource
    {
        string Name { get; }
        DemoInputFrame Read(bool arrowKeysTurn);
        void Discard();         // drop queued clicks and motion without acting on them
        void ResetHeldState();  // treat every key and button as released
    }

    static class KeyboardInput
    {
        public static void Read(ref DemoInputFrame frame, bool arrowKeysTurn)
        {
            var k = Keyboard.current;
            if (k == null)
                return;
            var forward = Axis(k.wKey.isPressed || k.upArrowKey.isPressed, k.sKey.isPressed || k.downArrowKey.isPressed);
            var strafe = Axis(k.dKey.isPressed, k.aKey.isPressed);
            var arrowsSide = Axis(k.rightArrowKey.isPressed, k.leftArrowKey.isPressed);
            if (arrowKeysTurn)
                frame.Turn = arrowsSide;
            else
                strafe = Mathf.Clamp(strafe + arrowsSide, -1f, 1f);
            frame.Move = Vector2.ClampMagnitude(new Vector2(strafe, forward), 1f);
            frame.Fast = k.leftShiftKey.isPressed || k.rightShiftKey.isPressed;
            frame.Height = Axis(k.qKey.isPressed, k.eKey.isPressed);
            // Browser shortcuts such as Ctrl+W stay with the browser; ignore chords.
            var chord = k.ctrlKey.isPressed || k.altKey.isPressed || k.leftMetaKey.isPressed || k.rightMetaKey.isPressed;
            frame.ResetView = !chord && k.xKey.wasPressedThisFrame;
            frame.ToggleView = !chord && k.vKey.wasPressedThisFrame;
        }

        static float Axis(bool positive, bool negative) => (positive ? 1f : 0f) - (negative ? 1f : 0f);

        public static void Reset()
        {
            if (Keyboard.current != null)
                InputSystem.ResetDevice(Keyboard.current);
            if (Mouse.current != null)
                InputSystem.ResetDevice(Mouse.current);
        }
    }

    public sealed class BrowserInputSource : IDemoInputSource
    {
        readonly float[] m_mouse = new float[DemoBrowser.MouseFrameLength];

        public string Name => "browser keyboard + page mouse bridge";

        public DemoInputFrame Read(bool arrowKeysTurn)
        {
            var frame = new DemoInputFrame();
            KeyboardInput.Read(ref frame, arrowKeysTurn);
            if (DemoBrowser.TakeMouse(m_mouse) < DemoBrowser.MouseFrameLength)
                return frame;
            frame.LookPixels = new Vector2(m_mouse[DemoBrowser.MouseDx], m_mouse[DemoBrowser.MouseDy]);
            frame.Zoom = m_mouse[DemoBrowser.MouseWheel];
            frame.Select = m_mouse[DemoBrowser.LeftClicks] > 0f;
            frame.SelectPosition = new Vector2(m_mouse[DemoBrowser.LeftX], m_mouse[DemoBrowser.LeftY]);
            frame.Open = m_mouse[DemoBrowser.RightClicks] > 0f;
            frame.OpenPosition = new Vector2(m_mouse[DemoBrowser.RightX], m_mouse[DemoBrowser.RightY]);
            frame.PointerPosition = new Vector2(m_mouse[DemoBrowser.PointerX], m_mouse[DemoBrowser.PointerY]);
            var flags = (int)m_mouse[DemoBrowser.Flags];
            frame.PointerOverView = (flags & DemoBrowser.FlagOverView) != 0;
            frame.PointerLocked = (flags & DemoBrowser.FlagLocked) != 0;
            frame.Dragging = (flags & DemoBrowser.FlagDragging) != 0;
            return frame;
        }

        public void Discard() => DemoBrowser.TakeMouse(m_mouse);

        public void ResetHeldState() => KeyboardInput.Reset();
    }

    public sealed class EditorInputSource : IDemoInputSource
    {
        const float k_clickSlopPixels = 5f;
        Vector2 m_pressPosition;
        float m_dragDistance;
        bool m_pressed;

        public string Name => "Input System keyboard + mouse (Editor)";

        public DemoInputFrame Read(bool arrowKeysTurn)
        {
            var frame = new DemoInputFrame();
            KeyboardInput.Read(ref frame, arrowKeysTurn);
            var mouse = Mouse.current;
            if (mouse == null)
                return frame;
            var position = mouse.position.ReadValue();
            frame.PointerPosition = position;
            frame.PointerOverView = position.x >= 0 && position.y >= 0 && position.x < Screen.width && position.y < Screen.height;
            var delta = mouse.delta.ReadValue();
            if (mouse.leftButton.wasPressedThisFrame && frame.PointerOverView)
            {
                m_pressed = true;
                m_pressPosition = position;
                m_dragDistance = 0f;
            }
            if (m_pressed && mouse.leftButton.isPressed)
            {
                m_dragDistance += delta.magnitude;
                if (m_dragDistance > k_clickSlopPixels)
                {
                    frame.Dragging = true;
                    frame.LookPixels = new Vector2(delta.x, -delta.y);  // Input System y is up
                }
            }
            if (m_pressed && mouse.leftButton.wasReleasedThisFrame)
            {
                m_pressed = false;
                if (m_dragDistance <= k_clickSlopPixels)
                {
                    frame.Select = true;
                    frame.SelectPosition = m_pressPosition;
                }
            }
            if (mouse.rightButton.wasPressedThisFrame && frame.PointerOverView)
            {
                frame.Open = true;
                frame.OpenPosition = position;
            }
            frame.Zoom = -mouse.scroll.ReadValue().y / 120f;
            return frame;
        }

        public void Discard() => m_pressed = false;

        public void ResetHeldState()
        {
            m_pressed = false;
            KeyboardInput.Reset();
        }
    }

    /// <summary>Applies the page's input gate to a source.</summary>
    public sealed class DemoInput
    {
        readonly IDemoInputSource m_source;
        bool m_resetPending;

        public DemoInput(IDemoInputSource source) => m_source = source;

        public string SourceName => m_source.Name;
        public bool Allowed { get; private set; } = true;
        public bool ArrowKeysTurn { get; set; } = true;

        public void SetAllowed(bool allowed)
        {
            if (allowed == Allowed)
                return;
            Allowed = allowed;
            // Applied in the next update, inside the player loop, not inside the page callback.
            m_resetPending = true;
        }

        public DemoInputFrame Read()
        {
            if (m_resetPending)
            {
                m_resetPending = false;
                m_source.ResetHeldState();
                m_source.Discard();
                return default;
            }
            if (!Allowed)
            {
                m_source.Discard();
                return default;
            }
            return m_source.Read(ArrowKeysTurn);
        }
    }
}
