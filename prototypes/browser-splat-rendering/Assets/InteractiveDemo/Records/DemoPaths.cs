// VR-HE interactive browser demo: where the demo's runtime files sit next to index.html.
//
// One definition shared by the player (DemoApp), the build script (DemoProjectSetup), the
// tests and, by convention, Tools/demo_server.py and Tools/package_demo_bundle.py.
//
// Every path deliberately starts with a folder name. UnityWebRequest (Unity 6000.3) treats a
// bare relative name such as "site.json" as a host name: it matches Unity's internal domain
// pattern ^\s*\w+(?:\.\w+)+(\/.*)?$, so the player asks for http://site.json/ and, with this
// project's "Allow downloads over HTTP: Not allowed" setting, throws "Insecure connection not
// allowed" before any request is sent. "data/site.json" is resolved relative to the page, as
// the benchmark's "fixtures/..." paths always were. DemoPathsTests guards this.
namespace VRHE.InteractiveDemo.Records
{
    public static class DemoPaths
    {
        /// <summary>Build sub-folder holding the site definition and build description.</summary>
        public const string DataFolder = "data";

        /// <summary>The validated copy of Data/demo-site.json that the player loads.</summary>
        public const string SiteUrl = DataFolder + "/site.json";

        /// <summary>Build label, Unity version and site hash written by the build script.</summary>
        public const string BuildInfoUrl = DataFolder + "/build-info.json";

        /// <summary>Generated splat fixtures, served by the demo server (not part of the build).</summary>
        public const string FixtureBase = "fixtures/";
    }
}
