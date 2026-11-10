// VR-HE browser splat-rendering prototype: batch-mode project setup and WebGL build.
//
// Run with an explicit project path, for example:
//   Unity -batchmode -quit -projectPath <repo>/prototypes/browser-splat-rendering \
//         -executeMethod VRHE.BrowserSplatTest.Editor.BenchmarkProjectSetup.SetupBatch -logFile <log>
//   Unity -batchmode -quit -projectPath <repo>/prototypes/browser-splat-rendering -buildTarget WebGL \
//         -executeMethod VRHE.BrowserSplatTest.Editor.BenchmarkProjectSetup.BuildWebGLBatch \
//         -vrheBuildOutput <dir> -logFile <log>
//
// Setup is idempotent: it creates the UnitySplats settings asset, adds UnitySplats' URP
// feature to the template's URP renderers, creates the benchmark scene and applies the WebGL
// player settings listed in ConfigureWebGL. It adds no other packages.

using System;
using System.IO;
using System.Linq;
using Gsplat;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;

namespace VRHE.BrowserSplatTest.Editor
{
    public static class BenchmarkProjectSetup
    {
        public const string ScenePath = "Assets/BrowserSplatTest/Scenes/BrowserSplatBenchmark.unity";
        const string k_template = "PROJECT:VRHEBenchmark";
        const string k_urpFeatureType = "Gsplat.GsplatURPFeature, Gsplat";
        const int k_maxMemoryMb = 4096;

        static readonly string[] k_rendererPaths =
        {
            "Assets/Settings/PC_Renderer.asset",
            "Assets/Settings/Mobile_Renderer.asset",
        };

        // ---------------------------------------------------------------- entry points
        public static void SetupBatch() => RunBatch(Setup);

        public static void BuildWebGLBatch() => RunBatch(() =>
        {
            Setup();
            var output = ArgumentValue("-vrheBuildOutput") ?? Path.GetFullPath("Builds/WebGL");
            BuildWebGL(output);
        });

        [MenuItem("VR-HE/Browser Splat Test/Run Setup")]
        public static void SetupMenu() => Setup();

        static void RunBatch(Action action)
        {
            try
            {
                action();
                Debug.Log("[VRHE-SETUP] finished");
                EditorApplication.Exit(0);
            }
            catch (Exception e)
            {
                Debug.LogError("[VRHE-SETUP] FAILED: " + e);
                EditorApplication.Exit(1);
            }
        }

        // ---------------------------------------------------------------- setup
        public static void Setup()
        {
            var settings = GsplatSettings.Instance;
            if (!settings)
                throw new InvalidOperationException("GsplatSettings.Instance could not be created");
            if (settings.MaxRenderOrder < 2)
            {
                // Two transparent queues let the overlap test force one renderer to draw last.
                settings.MaxRenderOrder = 2;
                EditorUtility.SetDirty(settings);
            }
            Debug.Log($"[VRHE-SETUP] GsplatSettings: {AssetDatabase.GetAssetPath(settings)}, " +
                      $"valid={settings.Valid}, maxRenderOrder={settings.MaxRenderOrder}");

            foreach (var path in k_rendererPaths)
                EnsureUrpFeature(path);

            CreateScene();
            ConfigureWebGL();
            AssetDatabase.SaveAssets();
        }

        static void EnsureUrpFeature(string rendererPath)
        {
            var data = AssetDatabase.LoadAssetAtPath<ScriptableRendererData>(rendererPath);
            if (!data)
                throw new FileNotFoundException("URP renderer data not found", rendererPath);
            var featureType = Type.GetType(k_urpFeatureType, true);
            if (data.rendererFeatures.Any(f => f && f.GetType() == featureType))
            {
                Debug.Log($"[VRHE-SETUP] {rendererPath}: Gsplat URP feature already present");
                return;
            }

            // Same steps as the renderer inspector's Add Renderer Feature button: create the
            // feature as a sub-asset, then register it in both serialized lists.
            var feature = (ScriptableRendererFeature)ScriptableObject.CreateInstance(featureType);
            feature.name = "GsplatURPFeature";
            AssetDatabase.AddObjectToAsset(feature, data);
            AssetDatabase.SaveAssets();
            if (!AssetDatabase.TryGetGUIDAndLocalFileIdentifier(feature, out _, out long localId))
                throw new InvalidOperationException("Could not resolve the new feature's local file id");

            var so = new SerializedObject(data);
            var features = so.FindProperty("m_RendererFeatures");
            var map = so.FindProperty("m_RendererFeatureMap");
            features.arraySize++;
            features.GetArrayElementAtIndex(features.arraySize - 1).objectReferenceValue = feature;
            map.arraySize++;
            map.GetArrayElementAtIndex(map.arraySize - 1).longValue = localId;
            so.ApplyModifiedPropertiesWithoutUndo();
            data.SetDirty();
            EditorUtility.SetDirty(data);
            AssetDatabase.SaveAssets();
            Debug.Log($"[VRHE-SETUP] {rendererPath}: added Gsplat URP feature (local id {localId})");
        }

        static void CreateScene()
        {
            Directory.CreateDirectory(Path.GetDirectoryName(ScenePath) ?? "Assets");
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            var cameraObject = new GameObject("Main Camera") { tag = "MainCamera" };
            var camera = cameraObject.AddComponent<Camera>();
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.02f, 0.02f, 0.03f, 1f);
            camera.fieldOfView = 60f;
            camera.nearClipPlane = 0.05f;
            camera.farClipPlane = 100f;
            cameraObject.transform.position = new Vector3(0f, 1.25f, -3f);
            var cameraData = cameraObject.AddComponent<UniversalAdditionalCameraData>();
            cameraData.renderPostProcessing = false;
            cameraData.antialiasing = AntialiasingMode.None;

            new GameObject("Browser Benchmark").AddComponent<BrowserBenchmark>();

            if (!EditorSceneManager.SaveScene(scene, ScenePath))
                throw new IOException("Could not save " + ScenePath);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
            Debug.Log($"[VRHE-SETUP] scene saved: {ScenePath}");
        }

        static void ConfigureWebGL()
        {
            var web = NamedBuildTarget.WebGL;
            PlayerSettings.SetUseDefaultGraphicsAPIs(BuildTarget.WebGL, false);
            PlayerSettings.SetGraphicsAPIs(BuildTarget.WebGL, new[] { GraphicsDeviceType.OpenGLES3 });
            PlayerSettings.WebGL.template = k_template;
            PlayerSettings.WebGL.compressionFormat = WebGLCompressionFormat.Disabled;
            PlayerSettings.WebGL.decompressionFallback = false;
            PlayerSettings.WebGL.dataCaching = false;
            PlayerSettings.WebGL.maximumMemorySize = k_maxMemoryMb;
            PlayerSettings.WebGL.powerPreference = WebGLPowerPreference.HighPerformance;
            PlayerSettings.WebGL.exceptionSupport = WebGLExceptionSupport.ExplicitlyThrownExceptionsOnly;
            PlayerSettings.runInBackground = true;
            PlayerSettings.SetManagedStrippingLevel(web, ManagedStrippingLevel.Minimal);
            Debug.Log("[VRHE-SETUP] WebGL: OpenGLES3 (WebGL 2) only, template " + k_template +
                      $", compression disabled, data caching off, max memory {k_maxMemoryMb} MB");
        }

        // ---------------------------------------------------------------- build
        public static void BuildWebGL(string outputPath)
        {
            if (EditorUserBuildSettings.activeBuildTarget != BuildTarget.WebGL)
                throw new InvalidOperationException(
                    $"Active build target is {EditorUserBuildSettings.activeBuildTarget}; start Unity with -buildTarget WebGL");

            var options = new BuildPlayerOptions
            {
                scenes = new[] { ScenePath },
                locationPathName = outputPath,
                target = BuildTarget.WebGL,
                options = BuildOptions.None
            };
            var report = BuildPipeline.BuildPlayer(options);
            var summary = report.summary;
            Debug.Log($"[VRHE-BUILD] result={summary.result} errors={summary.totalErrors} " +
                      $"warnings={summary.totalWarnings} size={summary.totalSize} bytes " +
                      $"time={summary.totalTime} output={summary.outputPath}");
            if (summary.result != BuildResult.Succeeded)
                throw new InvalidOperationException("WebGL build " + summary.result);
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
