// VR-HE interactive browser demo: selectable equipment proxies and their highlights.
//
// Selection never looks at the splat. Each anchor in the site file becomes an axis-aligned
// BoxCollider placed over the rack in the splat (alignment is checked by
// Tools/check_demo_site.py against the room generator). A ray from the camera through the
// pointer picks the first proxy, wall or boundary it meets; only proxies are selectable, so a
// wall between the camera and a rack blocks the pick, as it should.
//
// Extension point: captured sites will need anchors placed or reviewed by a person, several
// anchors per record (front, rear, cabinet open/closed) and oriented boxes. The recordId link
// stays the same.

using UnityEngine;

namespace VRHE.InteractiveDemo
{
    public sealed class DemoSelection : MonoBehaviour
    {
        public DemoHighlight selectedHighlight;
        public DemoHighlight hoverHighlight;
        public float maxPickDistance = 40f;

        public DemoAnchorProxy Selected { get; private set; }
        public DemoAnchorProxy Hovered { get; private set; }

        /// <summary>First thing the ray meets, if it is a proxy. Walls and boundaries block it.</summary>
        public DemoAnchorProxy Pick(Camera viewCamera, Vector2 screenPosition)
        {
            if (!viewCamera)
                return null;
            var ray = viewCamera.ScreenPointToRay(new Vector3(screenPosition.x, screenPosition.y, 0f));
            if (!Physics.Raycast(ray, out var hit, maxPickDistance, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore))
                return null;
            return hit.collider ? hit.collider.GetComponent<DemoAnchorProxy>() : null;
        }

        /// <summary>Returns true when the selection changed.</summary>
        public bool Select(DemoAnchorProxy proxy)
        {
            if (proxy == Selected)
                return false;
            Selected = proxy;
            if (proxy)
                selectedHighlight.Show(proxy.WorldBounds);
            else
                selectedHighlight.Hide();
            RefreshHover();
            return true;
        }

        /// <summary>Returns true when the hovered proxy changed.</summary>
        public bool Hover(DemoAnchorProxy proxy)
        {
            if (proxy == Hovered)
                return false;
            Hovered = proxy;
            RefreshHover();
            return true;
        }

        void RefreshHover()
        {
            if (Hovered && Hovered != Selected)
                hoverHighlight.Show(Hovered.WorldBounds);
            else
                hoverHighlight.Hide();
        }
    }
}
