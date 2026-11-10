// VR-HE browser splat-rendering prototype: self-reporting benchmark.
//
// Loads synthetic Gaussian-splat fixtures from the local test server, renders them through
// UnitySplats, measures frame timing and posts JSON results and screenshots back to the same
// server. Fixtures are procedural (Tools/generate_synthetic_splats.py); no capture,
// operational headend data or credentials are involved.
//
// Query parameters (all optional):
//   run=<id>           result folder name ([A-Za-z0-9_-], default "manual")
//   browser=<label>    label recorded with the results
//   suites=overlap,scale
//   counts=25000,100000,...   scale-suite fixtures: N loads scene_<N>.ply, N_sh3 loads scene_<N>_sh3.ply
//   warmup=<s> measure=<s> overlapMeasure=<s>
//   fixtures=<url>     fixture base URL (default "fixtures/")
//   report=<url>|none  result base URL (default "report/")
//   quality=<name>     Unity quality level by name (default: the build's WebGL default)
//   scale=<f>|keep     URP render scale (default 1.0)
//   orbit=0|1          move the camera during scale measurements (default 1)
//   compression=spark|uncompressed

using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Text;
using Gsplat;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace VRHE.BrowserSplatTest
{
    public sealed class BrowserBenchmark : MonoBehaviour
    {
        const string k_benchmarkVersion = "1";
        const float k_orbitDegreesPerSecond = 15f;
        const float k_uploadTimeoutSeconds = 120f;
        static readonly Color k_clearColor = new(0.02f, 0.02f, 0.03f, 1f);

        // ------------------------------------------------------------------ configuration
        string m_runId = "manual";
        string m_browserLabel = "unknown";
        string m_fixtureBase = "fixtures/";
        string m_reportBase = "report/";
        bool m_report = true;
        readonly List<string> m_suites = new() { "overlap", "scale" };
        readonly List<string> m_counts = new() { "25000", "100000", "250000", "500000", "1000000", "2000000" };
        float m_warmupSeconds = 2f;
        float m_measureSeconds = 6f;
        float m_overlapMeasureSeconds = 3f;
        string m_quality = "";
        float m_renderScale = 1f;
        bool m_keepRenderScale;
        bool m_orbit = true;
        CompressionMode m_compression = CompressionMode.Spark;

        // ------------------------------------------------------------------ state
        Camera m_camera;
        bool m_orbiting;
        float m_orbitAngle = 270f;
        int m_sectionACount = -1;
        int m_sectionBCount = -1;
        readonly List<CaseResult> m_results = new();
        readonly List<string> m_log = new();

        static double Now => Time.realtimeSinceStartupAsDouble * 1000.0;

        // ------------------------------------------------------------------ report types
        [Serializable]
        public class Stats
        {
            public int count;
            public double mean, median, p5, p95, p99, min, max;
        }

        [Serializable]
        public class RegionColor
        {
            public string name;
            public float r, g, b;
            public string nearest;
            public float distance;
            public int pixels;
        }

        [Serializable]
        public class CaseResult
        {
            public string suite;
            public string caseName;
            public string status = "started";
            public string error;
            public string notes;
            public int requestedSplats;
            public long uploadedSplats;
            public int rendererCount;
            public long fileBytes;
            public double downloadMs, decodeMs, uploadMs;
            public int frames;
            public Stats intervalMs, cpuMs, sortMs, renderMs, unityDeltaMs;
            public double fpsFromMeanInterval;
            public double wasmHeapMbBefore, wasmHeapMbAfterLoad, wasmHeapMbAfterMeasure;
            public double jsHeapMb;
            public double managedHeapMb;
            public string screenshot, thumbnail;
            public int screenshotWidth, screenshotHeight;
            public RegionColor[] regions;
        }

        [Serializable]
        class FrameSeries
        {
            public string caseName;
            public double[] intervalMs, cpuMs, sortMs, renderMs;
        }

        [Serializable]
        class EnvReport
        {
            public string benchmarkVersion = k_benchmarkVersion;
            public string run, browserLabel, url, unityVersion, platform;
            public string graphicsDeviceType, graphicsDeviceName, graphicsDeviceVendor, graphicsDeviceVersion;
            public int graphicsShaderLevel, graphicsMemorySize, maxTextureSize, maxComputeBufferInputsVertex;
            public bool supportsComputeShaders, supportsInstancing;
            public string operatingSystem, processorType;
            public int processorCount, systemMemorySize;
            public int screenWidth, screenHeight, cameraPixelWidth, cameraPixelHeight;
            public string qualityLevel, renderPipelineAsset, colorSpace, compression;
            public float renderScale;
            public bool hdr;
            public int msaa;
            public bool gsplatCpuFallback, gsplatGpuSort, gsplatVertexTextures, gsplatBackgroundCpuSort;
            public bool gsplatSettingsValid;
            public int gsplatMaxRenderOrder;
            public bool frameTimerInstalled, frameTimerFoundGsplatHook;
            public string browserInfoJson;
        }

        [Serializable]
        class RunSummary
        {
            public string benchmarkVersion = k_benchmarkVersion;
            public string run, browserLabel;
            public string status;
            public double totalSeconds;
            public List<CaseResult> results;
            public List<string> log;
        }

        [Serializable]
        class FixtureManifest
        {
            public OverlapInfo overlap;
        }

        [Serializable]
        class OverlapInfo
        {
            public int section_a_count;
            public int section_b_count;
        }

        struct RegionSpec
        {
            public string Name;
            public Vector3 Min, Max; // world-space rectangle on a constant-z plane

            public RegionSpec(string name, float x0, float x1, float y0, float y1, float z)
            {
                Name = name;
                Min = new Vector3(x0, y0, z);
                Max = new Vector3(x1, y1, z);
            }
        }

        // Regions on the overlap fixture (see generate_synthetic_splats.py): A's red sheet at
        // z = 0.0, B's blue sheet at z = 0.3, shared band x in [-0.5, 0.5]. Insets keep each
        // sample inside its sheet.
        static readonly RegionSpec[] k_overlapRegions =
        {
            new("a_only", -1.35f, -0.65f, 0.8f, 1.7f, 0.0f),
            new("shared_band", -0.35f, 0.35f, 0.8f, 1.7f, 0.0f),
            new("b_only", 0.65f, 1.35f, 0.8f, 1.7f, 0.3f),
        };

        static readonly (string name, Color color)[] k_referenceColors =
        {
            ("red_A", new Color(0.90f, 0.15f, 0.10f)),
            ("blue_B", new Color(0.10f, 0.25f, 0.95f)),
            ("backdrop_A", new Color(0.45f, 0.32f, 0.30f)),
            ("background", k_clearColor),
        };

        // ------------------------------------------------------------------ lifecycle
        IEnumerator Start()
        {
            var started = Now;
            ParseQuery();
            Application.runInBackground = true;
            ApplyQualityAndScale();
            SetupCamera();
            Status("VR-HE splat benchmark: starting");

            yield return null;
            yield return null;
            var env = CollectEnvironment();
            yield return PostText("env.json", JsonUtility.ToJson(env, true), "application/json");

            yield return LoadManifest();

            foreach (var suite in m_suites)
            {
                if (suite == "overlap")
                    yield return RunOverlapSuite();
                else if (suite == "scale")
                    yield return RunScaleSuite();
                else
                    Log($"unknown suite '{suite}' skipped");
            }

            var summary = new RunSummary
            {
                run = m_runId,
                browserLabel = m_browserLabel,
                status = "done",
                totalSeconds = (Now - started) / 1000.0,
                results = m_results,
                log = m_log
            };
            yield return PostText("summary.json", JsonUtility.ToJson(summary, true), "application/json");
            yield return PostText("done.json", "{\"done\":true}", "application/json");
            Status($"VR-HE splat benchmark: DONE ({summary.totalSeconds:F0} s)");
        }

        void Update()
        {
            if (!m_orbiting || !m_camera)
                return;
            m_orbitAngle = (m_orbitAngle + k_orbitDegreesPerSecond * Time.unscaledDeltaTime) % 360f;
            PlaceOrbitCamera(m_orbitAngle);
        }

        // ------------------------------------------------------------------ suites
        IEnumerator RunOverlapSuite()
        {
            PlaceOverlapCamera();

            yield return RunOverlapCase("overlap_merged_single_renderer",
                new[] { "overlap_AB.ply" }, new uint[] { 0 }, false);
            yield return RunOverlapCase("overlap_separate_renderers",
                new[] { "overlap_A.ply", "overlap_B.ply" }, new uint[] { 0, 0 }, false);
            yield return RunOverlapCase("overlap_separate_A_forced_last",
                new[] { "overlap_A.ply", "overlap_B.ply" }, new uint[] { 1, 0 }, false);
            yield return RunOverlapCase("overlap_merged_active_ranges",
                new[] { "overlap_AB.ply" }, new uint[] { 0 }, true);
        }

        IEnumerator RunOverlapCase(string caseName, string[] files, uint[] renderOrders, bool rangeSteps)
        {
            var result = NewResult("overlap", caseName);
            var renderers = new List<GsplatRenderer>();
            var assets = new List<GsplatAsset>();
            PlaceOverlapCamera();
            Status($"overlap: {caseName}");

            if (renderOrders[0] >= GsplatSettings.Instance.MaxRenderOrder ||
                (renderOrders.Length > 1 && renderOrders[1] >= GsplatSettings.Instance.MaxRenderOrder))
                result.notes = Append(result.notes,
                    $"MaxRenderOrder is {GsplatSettings.Instance.MaxRenderOrder}; requested orders are clamped");

            result.wasmHeapMbBefore = Mb(BrowserBridge.WasmHeapBytes());
            for (var i = 0; i < files.Length; i++)
            {
                GsplatAsset asset = null;
                yield return LoadAsset(files[i], result, a => asset = a);
                if (!asset)
                    break;
                assets.Add(asset);
                renderers.Add(CreateRenderer(System.IO.Path.GetFileNameWithoutExtension(files[i]), asset,
                    renderOrders[i]));
            }

            if (renderers.Count == files.Length)
            {
                yield return WaitForUpload(renderers, result);
                result.wasmHeapMbAfterLoad = Mb(BrowserBridge.WasmHeapBytes());
                if (result.status != "failed")
                {
                    yield return Settle(10);
                    yield return Capture(caseName, k_overlapRegions, result);
                    yield return Measure(m_overlapMeasureSeconds, false, result, caseName);

                    if (rangeSteps)
                        yield return RunRangeSteps(caseName, renderers[0], result);
                    if (result.status == "started")
                        result.status = "ok";
                }
            }
            else if (result.status == "started")
                result.status = "failed";

            yield return Teardown(renderers, assets);
            yield return Finish(result);
        }

        IEnumerator RunRangeSteps(string caseName, GsplatRenderer renderer, CaseResult parent)
        {
            if (m_sectionACount <= 0 || m_sectionBCount <= 0)
            {
                parent.notes = Append(parent.notes, "manifest section counts unavailable; range steps skipped");
                yield break;
            }

            var a = new GsplatActiveRange(0, (uint)m_sectionACount);
            var b = new GsplatActiveRange((uint)m_sectionACount, (uint)m_sectionBCount);
            var steps = new (string suffix, GsplatActiveRange[] ranges)[]
            {
                ("only_A", new[] { a }),
                ("only_B", new[] { b }),
                ("A_and_B", new[] { a, b }),
                ("cleared", null),
            };

            foreach (var (suffix, ranges) in steps)
            {
                var step = NewResult("overlap", caseName + "__" + suffix);
                step.rendererCount = 1;
                step.requestedSplats = ranges == null ? m_sectionACount + m_sectionBCount : 0;
                if (ranges != null)
                    foreach (var r in ranges)
                        step.requestedSplats += (int)r.Count;

                var error = ApplyRanges(renderer, ranges);
                if (error != null)
                {
                    step.status = "failed";
                    step.error = error;
                    yield return Finish(step);
                    continue;
                }

                var t0 = Now;
                yield return Settle(10);
                step.uploadMs = Now - t0;
                step.uploadedSplats = renderer.HasActiveRanges ? renderer.ActiveSplatCount : renderer.SplatCount;
                yield return Capture(caseName + "__" + suffix, k_overlapRegions, step);
                yield return Measure(1.5f, false, step, caseName + "__" + suffix);
                if (step.status == "started")
                    step.status = "ok";
                yield return Finish(step);
            }
        }

        static string ApplyRanges(GsplatRenderer renderer, GsplatActiveRange[] ranges)
        {
            try
            {
                if (ranges == null)
                    renderer.ClearActiveRanges();
                else
                    renderer.SetActiveRanges(ranges);
                return null;
            }
            catch (Exception e)
            {
                return e.GetType().Name + ": " + e.Message;
            }
        }

        IEnumerator RunScaleSuite()
        {
            foreach (var token in m_counts)
            {
                var count = ParseScaleToken(token);
                var caseName = $"scale_{token}";
                var result = NewResult("scale", caseName);
                result.requestedSplats = count;
                var renderers = new List<GsplatRenderer>();
                var assets = new List<GsplatAsset>();
                Status($"scale: {token} - loading");

                PlaceShotCamera();
                result.wasmHeapMbBefore = Mb(BrowserBridge.WasmHeapBytes());
                GsplatAsset asset = null;
                yield return LoadAsset($"scene_{token}.ply", result, x => asset = x);
                if (asset)
                {
                    assets.Add(asset);
                    renderers.Add(CreateRenderer(caseName, asset, 0));
                    yield return WaitForUpload(renderers, result);
                    result.wasmHeapMbAfterLoad = Mb(BrowserBridge.WasmHeapBytes());
                    if (result.status != "failed")
                    {
                        Status($"scale: {token} - measuring");
                        yield return Settle(5);
                        yield return Capture(caseName, null, result);
                        PlaceOrbitCamera(m_orbitAngle = 270f);
                        if (m_warmupSeconds > 0)
                        {
                            m_orbiting = m_orbit;
                            var w0 = Now;
                            while (Now - w0 < m_warmupSeconds * 1000.0)
                                yield return null;
                        }
                        yield return Measure(m_measureSeconds, m_orbit, result, caseName);
                        if (result.status == "started")
                            result.status = "ok";
                    }
                }
                else if (result.status == "started")
                    result.status = "failed";

                m_orbiting = false;
                yield return Teardown(renderers, assets);
                yield return Finish(result);
            }
        }

        // ------------------------------------------------------------------ steps
        IEnumerator LoadAsset(string file, CaseResult result, Action<GsplatAsset> done)
        {
            var url = m_fixtureBase + file;
            var t0 = Now;
            byte[] bytes = null;
            using (var request = UnityWebRequest.Get(url))
            {
                yield return request.SendWebRequest();
                result.downloadMs += Now - t0;
                if (request.result != UnityWebRequest.Result.Success)
                {
                    result.status = "failed";
                    result.error = Append(result.error, $"download {file}: {request.error}");
                    done(null);
                    yield break;
                }
                bytes = request.downloadHandler.data;
            }

            result.fileBytes += bytes.LongLength;
            Status($"{result.caseName}: decoding {file} ({bytes.LongLength / 1048576.0:F1} MB)");
            yield return null; // let the status text paint before the synchronous decode

            var t1 = Now;
            var asset = Decode(bytes, file, out var error);
            result.decodeMs += Now - t1;
            bytes = null;
            if (!asset)
            {
                result.status = "failed";
                result.error = Append(result.error, $"decode {file}: {error}");
            }
            done(asset);
        }

        GsplatAsset Decode(byte[] bytes, string name, out string error)
        {
            error = null;
            try
            {
                var asset = GsplatRuntimeLoader.Load(bytes, GsplatFileFormat.Ply, m_compression,
                    SourceCoordinates.RUB);
                asset.name = name;
                return asset;
            }
            catch (Exception e)
            {
                error = e.GetType().Name + ": " + e.Message;
                return null;
            }
        }

        static GsplatRenderer CreateRenderer(string name, GsplatAsset asset, uint renderOrder)
        {
            var go = new GameObject(name);
            go.SetActive(false);
            var renderer = go.AddComponent<GsplatRenderer>();
            renderer.GsplatAsset = asset;
            renderer.RenderOrder = renderOrder;
            go.SetActive(true);
            return renderer;
        }

        IEnumerator WaitForUpload(List<GsplatRenderer> renderers, CaseResult result)
        {
            var t0 = Now;
            result.rendererCount = renderers.Count;
            while (true)
            {
                long uploaded = 0;
                var complete = true;
                foreach (var r in renderers)
                {
                    if (!r || !r.GsplatAsset)
                    {
                        complete = false;
                        continue;
                    }
                    uploaded += r.SplatCount;
                    if (r.SplatCount < r.GsplatAsset.SplatCount)
                        complete = false;
                }
                result.uploadedSplats = uploaded;
                if (complete)
                    break;
                if (Now - t0 > k_uploadTimeoutSeconds * 1000.0)
                {
                    result.status = "failed";
                    result.error = Append(result.error, $"upload incomplete after {k_uploadTimeoutSeconds} s");
                    break;
                }
                yield return null;
            }
            result.uploadMs = Now - t0;
            if (result.requestedSplats == 0)
                foreach (var r in renderers)
                    if (r && r.GsplatAsset)
                        result.requestedSplats += (int)r.GsplatAsset.SplatCount;
        }

        static IEnumerator Settle(int frames)
        {
            for (var i = 0; i < frames; i++)
                yield return null;
        }

        IEnumerator Measure(float seconds, bool orbit, CaseResult result, string seriesName)
        {
            m_orbiting = orbit;
            var unity = new List<double>();
            FrameTimer.BeginRecording();
            var t0 = Now;
            while (Now - t0 < seconds * 1000.0)
            {
                yield return null;
                unity.Add(Time.unscaledDeltaTime * 1000.0);
            }
            var samples = FrameTimer.EndRecording();
            m_orbiting = false;

            var interval = new double[samples.Count];
            var cpu = new double[samples.Count];
            var sort = new double[samples.Count];
            var render = new double[samples.Count];
            for (var i = 0; i < samples.Count; i++)
            {
                interval[i] = samples[i].IntervalMs;
                cpu[i] = samples[i].CpuMs;
                sort[i] = samples[i].SortMs;
                render[i] = samples[i].RenderMs;
            }

            result.frames = samples.Count;
            result.intervalMs = Summarize(interval);
            result.cpuMs = Summarize(cpu);
            result.sortMs = Summarize(sort);
            result.renderMs = Summarize(render);
            result.unityDeltaMs = Summarize(unity.ToArray());
            result.fpsFromMeanInterval = result.intervalMs.mean > 0 ? 1000.0 / result.intervalMs.mean : 0;
            result.wasmHeapMbAfterMeasure = Mb(BrowserBridge.WasmHeapBytes());
            result.jsHeapMb = Mb(BrowserBridge.JsHeapBytes());
            result.managedHeapMb = GC.GetTotalMemory(false) / 1048576.0;
            if (samples.Count == 0)
                result.notes = Append(result.notes, "no frame samples recorded");

            var series = new FrameSeries
                { caseName = seriesName, intervalMs = interval, cpuMs = cpu, sortMs = sort, renderMs = render };
            yield return PostText(seriesName + ".frames.json", JsonUtility.ToJson(series), "application/json");
        }

        IEnumerator Capture(string baseName, RegionSpec[] regions, CaseResult result)
        {
            yield return new WaitForEndOfFrame();
            Texture2D shot = null;
            string error = null;
            try
            {
                shot = ScreenCapture.CaptureScreenshotAsTexture();
            }
            catch (Exception e)
            {
                error = e.GetType().Name + ": " + e.Message;
            }
            if (!shot)
            {
                result.notes = Append(result.notes, "screenshot failed" + (error != null ? ": " + error : ""));
                yield break;
            }

            var pixels = shot.GetPixels32();
            int w = shot.width, h = shot.height;
            result.screenshotWidth = w;
            result.screenshotHeight = h;
            if (regions != null)
            {
                var measured = new RegionColor[regions.Length];
                for (var i = 0; i < regions.Length; i++)
                    measured[i] = MeasureRegion(regions[i], pixels, w, h);
                result.regions = measured;
            }

            var png = shot.EncodeToPNG();
            var thumb = Downsample(pixels, w, h, 2);
            var jpg = thumb.EncodeToJPG(85);
            Destroy(shot);
            Destroy(thumb);

            result.screenshot = baseName + ".png";
            result.thumbnail = baseName + ".jpg";
            yield return PostBytes(result.screenshot, png, "image/png");
            yield return PostBytes(result.thumbnail, jpg, "image/jpeg");
        }

        RegionColor MeasureRegion(RegionSpec spec, Color32[] pixels, int w, int h)
        {
            var a = m_camera.WorldToScreenPoint(spec.Min);
            var b = m_camera.WorldToScreenPoint(spec.Max);
            var sx = (float)w / Mathf.Max(1, m_camera.pixelWidth);
            var sy = (float)h / Mathf.Max(1, m_camera.pixelHeight);
            var x0 = Mathf.Clamp(Mathf.RoundToInt(Mathf.Min(a.x, b.x) * sx), 0, w - 1);
            var x1 = Mathf.Clamp(Mathf.RoundToInt(Mathf.Max(a.x, b.x) * sx), 0, w - 1);
            var y0 = Mathf.Clamp(Mathf.RoundToInt(Mathf.Min(a.y, b.y) * sy), 0, h - 1);
            var y1 = Mathf.Clamp(Mathf.RoundToInt(Mathf.Max(a.y, b.y) * sy), 0, h - 1);
            double sr = 0, sg = 0, sb = 0;
            var n = 0;
            for (var y = y0; y <= y1; y++)
            for (var x = x0; x <= x1; x++)
            {
                var c = pixels[y * w + x];
                sr += c.r;
                sg += c.g;
                sb += c.b;
                n++;
            }
            var color = n > 0
                ? new Color((float)(sr / n / 255.0), (float)(sg / n / 255.0), (float)(sb / n / 255.0))
                : Color.black;
            var nearest = "none";
            var best = float.MaxValue;
            foreach (var (name, reference) in k_referenceColors)
            {
                var d = Mathf.Sqrt(Sq(color.r - reference.r) + Sq(color.g - reference.g) + Sq(color.b - reference.b));
                if (d < best)
                {
                    best = d;
                    nearest = name;
                }
            }
            return new RegionColor
                { name = spec.Name, r = color.r, g = color.g, b = color.b, nearest = nearest, distance = best, pixels = n };
        }

        static float Sq(float v) => v * v;

        static Texture2D Downsample(Color32[] pixels, int w, int h, int factor)
        {
            int tw = Mathf.Max(1, w / factor), th = Mathf.Max(1, h / factor);
            var output = new Color32[tw * th];
            for (var y = 0; y < th; y++)
            for (var x = 0; x < tw; x++)
            {
                int r = 0, g = 0, b = 0, n = 0;
                for (var dy = 0; dy < factor; dy++)
                for (var dx = 0; dx < factor; dx++)
                {
                    int px = x * factor + dx, py = y * factor + dy;
                    if (px >= w || py >= h)
                        continue;
                    var c = pixels[py * w + px];
                    r += c.r;
                    g += c.g;
                    b += c.b;
                    n++;
                }
                output[y * tw + x] = new Color32((byte)(r / n), (byte)(g / n), (byte)(b / n), 255);
            }
            var tex = new Texture2D(tw, th, TextureFormat.RGBA32, false);
            tex.SetPixels32(output);
            tex.Apply(false);
            return tex;
        }

        IEnumerator Teardown(List<GsplatRenderer> renderers, List<GsplatAsset> assets)
        {
            foreach (var r in renderers)
                if (r)
                    Destroy(r.gameObject);
            yield return null;
            foreach (var a in assets)
                if (a)
                    Destroy(a);
            yield return null;
            yield return Resources.UnloadUnusedAssets();
            GC.Collect();
            yield return null;
            yield return null;
        }

        IEnumerator Finish(CaseResult result)
        {
            if (result.status == "started")
                result.status = "failed";
            m_results.Add(result);
            Log($"{result.caseName}: {result.status}" +
                (result.frames > 0 ? $", {result.fpsFromMeanInterval:F1} fps, sort {result.sortMs.mean:F2} ms" : "") +
                (result.error != null ? $", error: {result.error}" : ""));
            yield return PostText(result.caseName + ".json", JsonUtility.ToJson(result, true), "application/json");
        }

        // ------------------------------------------------------------------ setup
        void ParseQuery()
        {
            var url = Application.absoluteURL ?? string.Empty;
            var q = url.IndexOf('?');
            if (q < 0)
                return;
            var query = url.Substring(q + 1);
            var hash = query.IndexOf('#');
            if (hash >= 0)
                query = query.Substring(0, hash);

            foreach (var part in query.Split('&'))
            {
                if (part.Length == 0)
                    continue;
                var eq = part.IndexOf('=');
                var key = UnityWebRequest.UnEscapeURL(eq < 0 ? part : part.Substring(0, eq));
                var value = eq < 0 ? "" : UnityWebRequest.UnEscapeURL(part.Substring(eq + 1));
                switch (key)
                {
                    case "run":
                        m_runId = SafeId(value, m_runId);
                        break;
                    case "browser":
                        m_browserLabel = SafeId(value, m_browserLabel);
                        break;
                    case "suites":
                        m_suites.Clear();
                        foreach (var s in value.Split(','))
                            if (s.Trim().Length > 0)
                                m_suites.Add(s.Trim());
                        break;
                    case "counts":
                        m_counts.Clear();
                        foreach (var s in value.Split(','))
                            if (ParseScaleToken(s.Trim()) > 0)
                                m_counts.Add(s.Trim());
                        break;
                    case "warmup":
                        m_warmupSeconds = ParseFloat(value, m_warmupSeconds);
                        break;
                    case "measure":
                        m_measureSeconds = ParseFloat(value, m_measureSeconds);
                        break;
                    case "overlapMeasure":
                        m_overlapMeasureSeconds = ParseFloat(value, m_overlapMeasureSeconds);
                        break;
                    case "fixtures":
                        m_fixtureBase = value.EndsWith("/") ? value : value + "/";
                        break;
                    case "report":
                        m_report = value != "none";
                        if (m_report)
                            m_reportBase = value.EndsWith("/") ? value : value + "/";
                        break;
                    case "quality":
                        m_quality = value;
                        break;
                    case "scale":
                        m_keepRenderScale = value == "keep";
                        if (!m_keepRenderScale)
                            m_renderScale = Mathf.Clamp(ParseFloat(value, m_renderScale), 0.25f, 2f);
                        break;
                    case "orbit":
                        m_orbit = value != "0";
                        break;
                    case "compression":
                        m_compression = value.ToLowerInvariant() == "uncompressed"
                            ? CompressionMode.Uncompressed
                            : CompressionMode.Spark;
                        break;
                }
            }
        }

        // "250000" or "250000_sh3" -> 250000; anything else -> 0.
        static int ParseScaleToken(string token)
        {
            var number = token.EndsWith("_sh3") ? token.Substring(0, token.Length - 4) : token;
            return int.TryParse(number, NumberStyles.None, CultureInfo.InvariantCulture, out var count) ? count : 0;
        }

        static string SafeId(string value, string fallback)
        {
            var sb = new StringBuilder();
            foreach (var ch in value)
                if (char.IsLetterOrDigit(ch) || ch == '-' || ch == '_' || ch == '.')
                    sb.Append(ch);
            var s = sb.ToString().Trim('.');
            return s.Length is > 0 and <= 80 ? s : fallback;
        }

        static float ParseFloat(string value, float fallback) =>
            float.TryParse(value, NumberStyles.Float, CultureInfo.InvariantCulture, out var f) ? f : fallback;

        void ApplyQualityAndScale()
        {
            if (!string.IsNullOrEmpty(m_quality))
            {
                var index = Array.IndexOf(QualitySettings.names, m_quality);
                if (index >= 0)
                    QualitySettings.SetQualityLevel(index, true);
                else
                    Log($"quality level '{m_quality}' not found; keeping {QualitySettings.names[QualitySettings.GetQualityLevel()]}");
            }
            if (!m_keepRenderScale && GraphicsSettings.currentRenderPipeline is UniversalRenderPipelineAsset urp)
                urp.renderScale = m_renderScale;
        }

        void SetupCamera()
        {
            m_camera = Camera.main;
            if (!m_camera)
            {
                var go = new GameObject("Benchmark Camera") { tag = "MainCamera" };
                m_camera = go.AddComponent<Camera>();
            }
            m_camera.clearFlags = CameraClearFlags.SolidColor;
            m_camera.backgroundColor = k_clearColor;
            m_camera.fieldOfView = 60f;
            m_camera.nearClipPlane = 0.05f;
            m_camera.farClipPlane = 100f;
            var data = m_camera.GetUniversalAdditionalCameraData();
            if (data)
            {
                data.renderPostProcessing = false;
                data.antialiasing = AntialiasingMode.None;
            }
        }

        void PlaceOverlapCamera()
        {
            m_orbiting = false;
            m_camera.transform.position = new Vector3(0f, 1.25f, -3f);
            m_camera.transform.LookAt(new Vector3(0f, 1.25f, 1f));
        }

        // Elliptical walk-around inside the synthetic room, clear of both rack rows, the walls
        // and the wall cabinet.
        void PlaceOrbitCamera(float degrees)
        {
            var radians = degrees * Mathf.Deg2Rad;
            m_camera.transform.position = new Vector3(3.4f * Mathf.Cos(radians), 1.7f, 2.7f * Mathf.Sin(radians));
            m_camera.transform.LookAt(new Vector3(0f, 1.0f, 0f));
        }

        // Fixed overview from the open front corner for the comparison screenshots.
        void PlaceShotCamera()
        {
            m_orbiting = false;
            m_camera.transform.position = new Vector3(3.3f, 2.1f, -2.8f);
            m_camera.transform.LookAt(new Vector3(-0.6f, 0.9f, 0.6f));
        }

        IEnumerator LoadManifest()
        {
            using var request = UnityWebRequest.Get(m_fixtureBase + "manifest.json");
            yield return request.SendWebRequest();
            if (request.result != UnityWebRequest.Result.Success)
            {
                Log($"fixture manifest unavailable: {request.error}");
                yield break;
            }
            try
            {
                var manifest = JsonUtility.FromJson<FixtureManifest>(request.downloadHandler.text);
                if (manifest?.overlap != null)
                {
                    m_sectionACount = manifest.overlap.section_a_count;
                    m_sectionBCount = manifest.overlap.section_b_count;
                }
            }
            catch (Exception e)
            {
                Log($"fixture manifest parse failed: {e.Message}");
            }
        }

        EnvReport CollectEnvironment()
        {
            var urp = GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset;
            return new EnvReport
            {
                run = m_runId,
                browserLabel = m_browserLabel,
                url = Application.absoluteURL,
                unityVersion = Application.unityVersion,
                platform = Application.platform.ToString(),
                graphicsDeviceType = SystemInfo.graphicsDeviceType.ToString(),
                graphicsDeviceName = SystemInfo.graphicsDeviceName,
                graphicsDeviceVendor = SystemInfo.graphicsDeviceVendor,
                graphicsDeviceVersion = SystemInfo.graphicsDeviceVersion,
                graphicsShaderLevel = SystemInfo.graphicsShaderLevel,
                graphicsMemorySize = SystemInfo.graphicsMemorySize,
                maxTextureSize = SystemInfo.maxTextureSize,
                maxComputeBufferInputsVertex = SystemInfo.maxComputeBufferInputsVertex,
                supportsComputeShaders = SystemInfo.supportsComputeShaders,
                supportsInstancing = SystemInfo.supportsInstancing,
                operatingSystem = SystemInfo.operatingSystem,
                processorType = SystemInfo.processorType,
                processorCount = SystemInfo.processorCount,
                systemMemorySize = SystemInfo.systemMemorySize,
                screenWidth = Screen.width,
                screenHeight = Screen.height,
                cameraPixelWidth = m_camera ? m_camera.pixelWidth : 0,
                cameraPixelHeight = m_camera ? m_camera.pixelHeight : 0,
                qualityLevel = QualitySettings.names[QualitySettings.GetQualityLevel()],
                renderPipelineAsset = urp ? urp.name : "none",
                colorSpace = QualitySettings.activeColorSpace.ToString(),
                compression = m_compression.ToString(),
                renderScale = urp ? urp.renderScale : 0f,
                hdr = urp && urp.supportsHDR,
                msaa = urp ? urp.msaaSampleCount : 0,
                gsplatCpuFallback = GsplatSorter.Instance.CpuFallbackEnabled,
                gsplatGpuSort = GsplatSorter.Instance.GpuSortEnabled,
                gsplatVertexTextures = GsplatUtils.UseVertexDataTextures,
                gsplatBackgroundCpuSort = GsplatUtils.SupportsBackgroundCpuSort,
                gsplatSettingsValid = GsplatSettings.Instance && GsplatSettings.Instance.Valid,
                gsplatMaxRenderOrder = GsplatSettings.Instance ? (int)GsplatSettings.Instance.MaxRenderOrder : 0,
                frameTimerInstalled = FrameTimer.Installed,
                frameTimerFoundGsplatHook = FrameTimer.GsplatHookFound,
                browserInfoJson = BrowserBridge.BrowserInfoJson()
            };
        }

        // ------------------------------------------------------------------ reporting
        IEnumerator PostText(string name, string text, string contentType) =>
            PostBytes(name, Encoding.UTF8.GetBytes(text), contentType);

        IEnumerator PostBytes(string name, byte[] body, string contentType)
        {
            if (!m_report)
                yield break;
            using var request = new UnityWebRequest(m_reportBase + m_runId + "/" + name, "POST");
            request.uploadHandler = new UploadHandlerRaw(body) { contentType = contentType };
            request.downloadHandler = new DownloadHandlerBuffer();
            yield return request.SendWebRequest();
            if (request.result != UnityWebRequest.Result.Success)
                Debug.LogWarning($"[VRHE] report upload failed for {name}: {request.error}");
        }

        CaseResult NewResult(string suite, string caseName) => new() { suite = suite, caseName = caseName };

        void Log(string line)
        {
            m_log.Add(line);
            Debug.Log("[VRHE] " + line);
        }

        static void Status(string text) => BrowserBridge.SetStatus(text);

        static string Append(string existing, string addition) =>
            string.IsNullOrEmpty(existing) ? addition : existing + "; " + addition;

        static double Mb(double bytes) => bytes < 0 ? -1 : bytes / 1048576.0;

        static Stats Summarize(double[] values)
        {
            var stats = new Stats { count = values.Length };
            if (values.Length == 0)
                return stats;
            var sorted = (double[])values.Clone();
            Array.Sort(sorted);
            double sum = 0;
            foreach (var v in sorted)
                sum += v;
            stats.mean = sum / sorted.Length;
            stats.median = Percentile(sorted, 0.5);
            stats.p5 = Percentile(sorted, 0.05);
            stats.p95 = Percentile(sorted, 0.95);
            stats.p99 = Percentile(sorted, 0.99);
            stats.min = sorted[0];
            stats.max = sorted[sorted.Length - 1];
            return stats;
        }

        static double Percentile(double[] sorted, double p)
        {
            var rank = (int)Math.Ceiling(p * sorted.Length) - 1;
            return sorted[Mathf.Clamp(rank, 0, sorted.Length - 1)];
        }
    }
}
