// VR-HE interactive browser demo: Editor setup and WebGL build.
//
// Creates the demo's materials and scene (Assets/InteractiveDemo/Scenes/InteractiveDemo.unity)
// and builds it to a separate output folder. It deliberately does not call the benchmark's
// setup, does not change the scene list in Build Settings and leaves the benchmark scene,
// fixtures and Builds/WebGL output alone. The only shared setting it touches is the WebGL
// template, which it switches for the build and restores afterwards.
//
// Batch use (always name this project explicitly; never point it at another project):
//   Unity -batchmode -quit -projectPath ~/Projects/VR-HE/prototypes/browser-splat-rendering
//         -buildTarget WebGL -executeMethod VRHE.InteractiveDemo.EditorTools.DemoProjectSetup.BuildBatch
//         -vrheBuildOutput <folder> -vrheBuildLabel <label> -logFile <log>
// Tools/build_interactive_demo.sh wraps this.

using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;
using VRHE.InteractiveDemo.Records;

namespace VRHE.InteractiveDemo.EditorTools
{
    public static class DemoProjectSetup
    {
        public const string Root = "Assets/InteractiveDemo";
        public const string ScenePath = Root + "/Scenes/InteractiveDemo.unity";
        public const string SiteAssetPath = Root + "/Data/demo-site.json";
        const string k_materials = Root + "/Materials";
        const string k_template = "PROJECT:VRHEInteractiveDemo";
        const string k_defaultOutput = "Builds/InteractiveDemo";
        const int k_ignoreRaycastLayer = 2;

        [MenuItem("VR-HE/Interactive demo/Create scene")]
        public static void SetupMenu() => Setup();

        [MenuItem("VR-HE/Interactive demo/Build WebGL to Builds/InteractiveDemo")]
        public static void BuildMenu() => Build(k_defaultOutput, "editor-menu");

        public static void SetupBatch() => RunBatch(Setup);

        // Builds reuse the committed scene so repeated builds do not rewrite it; pass
        // -vrheRecreateScene to regenerate the scene and materials first.
        public static void BuildBatch() => RunBatch(() =>
        {
            if (!File.Exists(ScenePath) || Environment.GetCommandLineArgs().Contains("-vrheRecreateScene"))
                Setup();
            Build(ArgumentValue("-vrheBuildOutput") ?? k_defaultOutput, ArgumentValue("-vrheBuildLabel") ?? "unlabelled");
        });

        static void RunBatch(Action action)
        {
            try
            {
                action();
                Debug.Log("[VRHE-DEMO] finished");
                EditorApplication.Exit(0);
            }
            catch (Exception e)
            {
                Debug.LogError("[VRHE-DEMO] FAILED: " + e);
                EditorApplication.Exit(1);
            }
        }

        public static void Setup()
        {
            if (!File.Exists(SiteAssetPath))
                throw new FileNotFoundException("site definition missing", SiteAssetPath);
            Directory.CreateDirectory(k_materials);
            Directory.CreateDirectory(Path.GetDirectoryName(ScenePath));
            var body = EnsureMaterial("AvatarBody", "Universal Render Pipeline/Lit", new Color(0.56f, 0.60f, 0.66f), 0.25f);
            var accent = EnsureMaterial("AvatarVisor", "Universal Render Pipeline/Lit", new Color(0.95f, 0.62f, 0.18f), 0.5f);
            var selected = EnsureMaterial("OutlineSelected", "Universal Render Pipeline/Unlit", new Color(0.10f, 0.88f, 1.00f), 0f);
            var hover = EnsureMaterial("OutlineHover", "Universal Render Pipeline/Unlit", new Color(0.95f, 0.95f, 0.95f), 0f);
            // Save only these materials: a project-wide SaveAssets would also write unrelated
            // assets that Unity marked dirty on load (for example URP's asset-version bookkeeping).
            foreach (var material in new[] { body, accent, selected, hover })
                AssetDatabase.SaveAssetIfDirty(material);
            CreateScene(body, accent, selected, hover);
        }

        static Material EnsureMaterial(string name, string shaderName, Color color, float smoothness)
        {
            var shader = Shader.Find(shaderName);
            if (!shader)
                throw new InvalidOperationException("shader not found: " + shaderName);
            var path = $"{k_materials}/{name}.mat";
            var material = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (!material)
            {
                material = new Material(shader) { name = name };
                AssetDatabase.CreateAsset(material, path);
            }
            material.shader = shader;
            material.SetColor("_BaseColor", color);
            if (material.HasProperty("_Smoothness"))
                material.SetFloat("_Smoothness", smoothness);
            material.enableInstancing = false;
            EditorUtility.SetDirty(material);
            return material;
        }

        static void CreateScene(Material body, Material accent, Material selected, Material hover)
        {
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            RenderSettings.skybox = null;
            RenderSettings.ambientMode = AmbientMode.Flat;
            RenderSettings.ambientLight = new Color(0.42f, 0.43f, 0.46f);
            RenderSettings.fog = false;

            var lightGo = new GameObject("Directional Light");
            var light = lightGo.AddComponent<Light>();
            light.type = LightType.Directional;
            light.intensity = 1.1f;
            light.shadows = LightShadows.None;
            lightGo.transform.rotation = Quaternion.Euler(50f, -30f, 0f);

            var cameraGo = new GameObject("Main Camera") { tag = "MainCamera" };
            var camera = cameraGo.AddComponent<Camera>();
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.02f, 0.02f, 0.03f, 1f);
            camera.fieldOfView = 60f;
            camera.nearClipPlane = 0.05f;
            camera.farClipPlane = 100f;
            var cameraData = cameraGo.AddComponent<UniversalAdditionalCameraData>();
            cameraData.renderPostProcessing = false;
            cameraData.antialiasing = AntialiasingMode.None;
            cameraGo.transform.position = new Vector3(2.8f, 1.6f, -2.35f);

            // Player: CharacterController capsule 1.75 m x 0.5 m on the Ignore Raycast layer, so
            // neither picking rays nor the third-person camera cast ever hit the player.
            var playerGo = new GameObject("Player") { layer = k_ignoreRaycastLayer };
            var controller = playerGo.AddComponent<CharacterController>();
            controller.height = 1.75f;
            controller.radius = 0.25f;
            controller.center = new Vector3(0f, 0.875f, 0f);
            controller.skinWidth = 0.02f;
            controller.stepOffset = 0.3f;
            controller.slopeLimit = 45f;
            controller.minMoveDistance = 0f;
            var player = playerGo.AddComponent<DemoPlayer>();
            player.avatar = BuildAvatar(playerGo.transform, body, accent);

            var selectionGo = new GameObject("Selection");
            var selection = selectionGo.AddComponent<DemoSelection>();
            selection.selectedHighlight = BuildOutline("Selected outline (cyan)", selectionGo.transform, selected);
            selection.hoverHighlight = BuildOutline("Hover outline (white)", selectionGo.transform, hover);

            var appGo = new GameObject(DemoApp.BridgeObjectName);
            var app = appGo.AddComponent<DemoApp>();
            app.player = player;
            app.selection = selection;
            app.viewCamera = camera;

            if (!EditorSceneManager.SaveScene(scene, ScenePath))
                throw new IOException("Could not save " + ScenePath);
            AssetDatabase.ImportAsset(ScenePath);
            Debug.Log("[VRHE-DEMO] scene saved: " + ScenePath);
        }

        // Generic, non-gendered mannequin about 1.73 m tall for scale; the orange visor shows
        // which way it faces. Visual only: the colliders the primitives come with are removed.
        static Transform BuildAvatar(Transform parent, Material body, Material accent)
        {
            var root = new GameObject("Avatar (placeholder, 1.73 m)") { layer = k_ignoreRaycastLayer }.transform;
            root.SetParent(parent, false);
            Part(PrimitiveType.Capsule, "Leg L", root, new Vector3(-0.1f, 0.45f, 0f), new Vector3(0.22f, 0.45f, 0.22f), body);
            Part(PrimitiveType.Capsule, "Leg R", root, new Vector3(0.1f, 0.45f, 0f), new Vector3(0.22f, 0.45f, 0.22f), body);
            Part(PrimitiveType.Capsule, "Torso", root, new Vector3(0f, 1.2f, 0f), new Vector3(0.4f, 0.33f, 0.24f), body);
            Part(PrimitiveType.Capsule, "Arm L", root, new Vector3(-0.27f, 1.17f, 0f), new Vector3(0.12f, 0.32f, 0.12f), body);
            Part(PrimitiveType.Capsule, "Arm R", root, new Vector3(0.27f, 1.17f, 0f), new Vector3(0.12f, 0.32f, 0.12f), body);
            Part(PrimitiveType.Sphere, "Head", root, new Vector3(0f, 1.615f, 0f), Vector3.one * 0.23f, body);
            Part(PrimitiveType.Cube, "Visor (front)", root, new Vector3(0f, 1.63f, 0.1f), new Vector3(0.17f, 0.05f, 0.06f), accent);
            return root;
        }

        static DemoHighlight BuildOutline(string name, Transform parent, Material material)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            var outline = go.AddComponent<DemoHighlight>();
            outline.bars = Enumerable.Range(0, 12)
                .Select(i => Part(PrimitiveType.Cube, "Edge " + i, go.transform, Vector3.zero, Vector3.one * 0.02f, material))
                .ToArray();
            go.SetActive(false);
            return outline;
        }

        static Transform Part(PrimitiveType type, string name, Transform parent, Vector3 position, Vector3 scale, Material material)
        {
            var go = GameObject.CreatePrimitive(type);
            go.name = name;
            go.layer = parent.gameObject.layer;
            UnityEngine.Object.DestroyImmediate(go.GetComponent<Collider>());
            go.transform.SetParent(parent, false);
            go.transform.localPosition = position;
            go.transform.localScale = scale;
            var renderer = go.GetComponent<MeshRenderer>();
            renderer.sharedMaterial = material;
            renderer.shadowCastingMode = ShadowCastingMode.Off;
            renderer.receiveShadows = false;
            return go.transform;
        }

        public static void Build(string output, string label)
        {
            if (EditorUserBuildSettings.activeBuildTarget != BuildTarget.WebGL)
                throw new InvalidOperationException(
                    $"Active build target is {EditorUserBuildSettings.activeBuildTarget}; start Unity with -buildTarget WebGL");
            var fullOutput = Path.GetFullPath(output);
            var benchmarkOutput = Path.GetFullPath("Builds/WebGL");
            if (string.Equals(fullOutput.TrimEnd('/', '\\'), benchmarkOutput, StringComparison.Ordinal))
                throw new InvalidOperationException("refusing to overwrite the benchmark build at Builds/WebGL");

            var previousTemplate = PlayerSettings.WebGL.template;
            BuildReport report;
            try
            {
                PlayerSettings.WebGL.template = k_template;
                Debug.Log($"[VRHE-DEMO] WebGL settings in use: template={k_template} (restored to {previousTemplate} afterwards), " +
                          $"compression={PlayerSettings.WebGL.compressionFormat}, memory max={PlayerSettings.WebGL.maximumMemorySize} MB, " +
                          $"exceptions={PlayerSettings.WebGL.exceptionSupport}, dataCaching={PlayerSettings.WebGL.dataCaching}");
                report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
                {
                    scenes = new[] { ScenePath },
                    locationPathName = fullOutput,
                    target = BuildTarget.WebGL,
                    targetGroup = BuildTargetGroup.WebGL,
                    options = BuildOptions.None
                });
            }
            finally
            {
                PlayerSettings.WebGL.template = previousTemplate;
            }
            var summary = report.summary;
            Debug.Log($"[VRHE-DEMO] build result={summary.result} errors={summary.totalErrors} warnings={summary.totalWarnings} " +
                      $"size={summary.totalSize} bytes time={summary.totalTime} output={summary.outputPath}");
            if (summary.result != BuildResult.Succeeded)
                throw new InvalidOperationException("WebGL build " + summary.result);

            // Runtime data goes in a sub-folder; see DemoPaths for why a bare "site.json" fails.
            // Earlier builds put these files at the root, so remove those copies.
            foreach (var stale in new[] { "site.json", "build-info.json" })
                File.Delete(Path.Combine(fullOutput, stale));
            var dataFolder = Path.Combine(fullOutput, DemoPaths.DataFolder);
            Directory.CreateDirectory(dataFolder);
            var siteTarget = Path.Combine(fullOutput, DemoPaths.SiteUrl);
            File.Copy(SiteAssetPath, siteTarget, true);
            var info = new BuildInfoFile
            {
                label = label,
                builtAt = DateTime.UtcNow.ToString("yyyy-MM-dd'T'HH:mm:ss'Z'"),
                unityVersion = Application.unityVersion,
                scene = ScenePath,
                siteSha256 = Sha256(siteTarget),
                template = k_template
            };
            File.WriteAllText(Path.Combine(fullOutput, DemoPaths.BuildInfoUrl), JsonUtility.ToJson(info, true) + "\n");
            Debug.Log($"[VRHE-DEMO] wrote {DemoPaths.SiteUrl} and {DemoPaths.BuildInfoUrl} to " + fullOutput);
        }

        [Serializable]
        sealed class BuildInfoFile
        {
            public string product = "VR-HE interactive browser demo (prototype)";
            public string label;
            public string builtAt;
            public string unityVersion;
            public string scene;
            public string siteSha256;
            public string template;
        }

        static string Sha256(string path)
        {
            using var sha = SHA256.Create();
            using var stream = File.OpenRead(path);
            return string.Concat(sha.ComputeHash(stream).Select(b => b.ToString("x2")));
        }

        static string ArgumentValue(string name)
        {
            var args = Environment.GetCommandLineArgs();
            for (var i = 0; i < args.Length - 1; i++)
                if (args[i] == name)
                    return args[i + 1];
            return null;
        }
    }
}
