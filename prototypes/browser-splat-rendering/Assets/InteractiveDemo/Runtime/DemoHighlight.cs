// VR-HE interactive browser demo: selection and hover outline (see DemoSelection.cs).
// The twelve bars are opaque geometry drawn before the splat, so splats in front of a bar
// cover it and the outline is not visible through other racks.

using UnityEngine;

namespace VRHE.InteractiveDemo
{
    /// <summary>Twelve thin edge bars around a box; built in the Editor by DemoProjectSetup.</summary>
    public sealed class DemoHighlight : MonoBehaviour
    {
        public float thickness = 0.02f;
        public float margin = 0.02f;
        public Transform[] bars = new Transform[0];

        static readonly Vector2[] k_corners = { new(-1, -1), new(-1, 1), new(1, -1), new(1, 1) };

        public void Show(Bounds bounds)
        {
            if (bars.Length < 12)
                return;
            transform.SetPositionAndRotation(bounds.center, Quaternion.identity);
            var size = bounds.size + Vector3.one * (2f * margin);
            var half = size * 0.5f;
            var t = thickness;
            for (var i = 0; i < 4; i++)
            {
                var c = k_corners[i];
                Place(bars[i], new Vector3(0f, c.x * half.y, c.y * half.z), new Vector3(size.x + t, t, t));
                Place(bars[4 + i], new Vector3(c.x * half.x, 0f, c.y * half.z), new Vector3(t, size.y + t, t));
                Place(bars[8 + i], new Vector3(c.x * half.x, c.y * half.y, 0f), new Vector3(t, t, size.z + t));
            }
            if (!gameObject.activeSelf)
                gameObject.SetActive(true);
        }

        public void Hide()
        {
            if (gameObject.activeSelf)
                gameObject.SetActive(false);
        }

        static void Place(Transform bar, Vector3 localPosition, Vector3 scale)
        {
            if (!bar)
                return;
            bar.localPosition = localPosition;
            bar.localRotation = Quaternion.identity;
            bar.localScale = scale;
        }
    }
}
