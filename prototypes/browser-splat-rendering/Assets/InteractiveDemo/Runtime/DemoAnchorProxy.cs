// VR-HE interactive browser demo: one placed selection/collision proxy (see DemoSelection.cs).
// It holds identities only: anchorId for the placed box, recordId for the equipment record,
// displayName for labels. It never refers to splat indexes.

using UnityEngine;

namespace VRHE.InteractiveDemo
{
    /// <summary>One placed selection/collision proxy. Holds identities, never a splat index.</summary>
    public sealed class DemoAnchorProxy : MonoBehaviour
    {
        public string anchorId;
        public string recordId;
        public string displayName;
        public BoxCollider box;

        public Bounds WorldBounds => box ? box.bounds : new Bounds(transform.position, Vector3.zero);
    }
}
