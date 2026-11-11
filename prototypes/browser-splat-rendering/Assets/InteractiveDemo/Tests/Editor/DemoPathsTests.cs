// VR-HE interactive browser demo: guards the runtime file locations against Unity's URL guessing.
//
// UnityWebRequest decides from the text alone whether a relative URL is a path or a host name.
// A bare "site.json" is taken as the host "site.json"; in the WebGL player that becomes
// http://site.json/ and is refused under "Allow downloads over HTTP: Not allowed" (seen in the
// first real-browser run of this demo). These tests run Unity's own URL handling in the Editor.

using NUnit.Framework;
using UnityEngine.Networking;
using VRHE.InteractiveDemo.Records;

namespace VRHE.InteractiveDemo.Tests
{
    public class DemoPathsTests
    {
        [TestCase(DemoPaths.SiteUrl)]
        [TestCase(DemoPaths.BuildInfoUrl)]
        [TestCase(DemoPaths.FixtureBase + "scene_250000.ply")]
        public void RuntimePathsStayRelativeToThePage(string path)
        {
            using var request = UnityWebRequest.Get(path);
            var url = request.url;
            var firstSegment = path.Split('/')[0];
            Assert.That(url, Does.EndWith(path), "the path survives unchanged");
            Assert.That(url, Does.Not.StartWith("http://" + firstSegment).And.Not.StartWith("https://" + firstSegment),
                "the first path segment must not become a host name");
        }

        [Test]
        public void BareFileNameIsTakenAsAHostName()
        {
            // Records the Unity behaviour the paths above avoid. If a Unity upgrade changes it,
            // this fails as information, not as a demo defect.
            using var request = UnityWebRequest.Get("site.json");
            Assert.That(request.url, Does.Match("^https?://site\\.json/?$"), request.url);
        }
    }
}
