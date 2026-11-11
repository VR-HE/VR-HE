// VR-HE interactive browser demo: startup, per-frame flow and the page bridge endpoints.
//
// PROTOTYPE. Loads the synthetic 250k-splat room, builds proxy colliders and selectable
// anchors from data/site.json, and connects input, camera, selection and the provisional local
// record store to the HTML interface in WebGLTemplates/VRHEInteractiveDemo.
//
// Startup: data/site.json -> validate -> proxies -> record store (browser localStorage) ->
// splat download/decode/upload -> spawn -> "ready". The splat is a picture only: walking and
// picking use the proxies. Any failure, including an unexpected exception, is shown on the
// page instead of leaving it on the loading screen. File locations: DemoPaths.
//
// Page -> Unity calls (unityInstance.SendMessage("VRHEDemo", method, text)):
//   JsUiState     {"inputAllowed","panel","typing","lookSpeed"}  input gate from the page
//   JsOpenRecord  {"recordId","how","requestId"}   re-reads storage, replies "openRecord"
//   JsSelectRecord{"recordId","face"}              selects (and optionally turns toward) an item
//   JsSaveRecord  {"recordId","description","baseRevision","requestId"}  replies "saveResult"
//   JsCommand     toggleView | resetView | export | clearData | deselect | report
//   JsTest        state:<id> | pacingBegin:<label> | pacingEnd:<id> | project:<recordId>:<id>
// JsTest exists for the automated browser checks. It reads state or opens timing windows and
// changes nothing the user sees.
//
// Extension points: a production site package, tour content, built-in guidance, server-backed
// records and the spreadsheet adapter would replace data/site.json and DemoRecordStore here.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using Gsplat;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using VRHE.BrowserSplatTest;
using VRHE.InteractiveDemo.Records;

namespace VRHE.InteractiveDemo
{
    [DefaultExecutionOrder(100)]  // after DemoPlayer, so LateUpdate sees this frame's camera
    public sealed class DemoApp : MonoBehaviour
    {
        public const string BridgeObjectName = "VRHEDemo";

        [Header("Scene references (set by DemoProjectSetup)")]
        public DemoPlayer player;
        public DemoSelection selection;
        public Camera viewCamera;

        [Header("Prototype choices (not user decisions)")]
        // D022: Left/Right arrows step sideways like A/D (turning is by mouse). True makes them turn at
        // DemoPlayer.keyTurnDegreesPerSecond instead; not exposed in the page, kept for later comfort tests.
        public bool arrowKeysTurn = false;
        public float hudInterval = 0.5f;
        public float reportInterval = 30f;
        public float uploadTimeoutSeconds = 120f;

        static readonly Color k_clearColor = new(0.02f, 0.02f, 0.03f, 1f);
        static readonly string[] k_views = { "first", "third" };
        static readonly string[] k_activities = { "idle", "moving", "looking", "orbiting", "height", "panel", "typing", "unfocused" };
        static readonly string[,] k_labels = BuildLabels();

        readonly DemoPacing m_pacing = new();
        readonly SessionEvents m_events = new();
        readonly Dictionary<string, DemoAnchorProxy> m_proxyByRecord = new();
        readonly List<DemoAnchorProxy> m_proxies = new();

        DemoSiteDefinition m_site;
        DemoRecordStore m_store;
        DemoInput m_input;
        BuildInfo m_build = new();
        string m_origin = "";
        bool m_ready;
        bool m_failed;
        double m_startTime, m_loadSeconds;
        int m_splats;
        string m_panel = "";
        bool m_typing;
        string m_activity = "loading";
        long m_frame;
        float m_hudElapsed, m_reportElapsed;
        int m_hudFrames;
        Vector2 m_lastTag = new(float.NaN, float.NaN);
        bool m_tagVisible;

        static double Now => Time.realtimeSinceStartupAsDouble;

        void Awake()
        {
            gameObject.name = BridgeObjectName;  // the page addresses this object by name
            m_input = new DemoInput(DemoBrowser.IsBrowser ? new BrowserInputSource() : new EditorInputSource())
            {
                ArrowKeysTurn = arrowKeysTurn
            };
        }

        IEnumerator Start()
        {
            m_startTime = Now;
            // No frame cap: the browser paces frames to the display (requestAnimationFrame).
            // The 30 fps project floor (D034) is a minimum to judge against, not a cap.
            Application.targetFrameRate = -1;
            if (GraphicsSettings.currentRenderPipeline is UniversalRenderPipelineAsset urp)
                urp.renderScale = 1f;  // the WebGL quality level's asset defaults to 0.8
#if UNITY_WEBGL && !UNITY_EDITOR
            // Let HTML text fields receive keys; Unity then hears the keyboard only while the
            // canvas has focus. The page keeps focus on the canvas outside panels.
            WebGLInput.captureAllKeyboardInput = false;
#endif
            FrameTimer.Recording = true;
            FrameTimer.Samples.Clear();
            m_origin = DemoBrowser.PageOrigin();
            SetupCamera();
            player.Initialize(viewCamera);

            Status("site", "Loading the demo site definition", 0.02f);
            string siteJson = null, siteError = null;
            yield return GetText(DemoPaths.SiteUrl, EditorPath("Assets/InteractiveDemo/Data/demo-site.json"), (t, e) => (siteJson, siteError) = (t, e));
            if (siteJson == null)
            {
                Fail($"Could not load {DemoPaths.SiteUrl}: {siteError}");
                yield break;
            }
            try
            {
                m_site = DemoSiteDefinition.FromJson(siteJson);
            }
            catch (Exception e)
            {
                Fail($"{DemoPaths.SiteUrl} is not valid JSON: {e.Message}");
                yield break;
            }
            var problems = DemoSiteValidator.Validate(m_site);
            if (problems.Count > 0)
            {
                Fail($"{DemoPaths.SiteUrl} failed validation: " + string.Join("; ", problems));
                yield break;
            }

            string buildJson = null;
            yield return GetText(DemoPaths.BuildInfoUrl, null, (t, _) => buildJson = t);
            if (!string.IsNullOrEmpty(buildJson))
                try
                {
                    m_build = JsonUtility.FromJson<BuildInfo>(buildJson) ?? new BuildInfo();
                }
                catch (Exception)
                {
                    m_build = new BuildInfo();
                }

            BuildProxies();
            IKeyValueStorage storage = DemoBrowser.IsBrowser
                ? new BrowserLocalStorage(m_origin)
                : new InMemoryKeyValueStorage();
            m_store = new DemoRecordStore(m_site, storage);
            PostSite();

            yield return LoadSplat();
            if (!m_renderer)
                yield break;

            player.Spawn(V(m_site.spawn.feet), m_site.spawn.yawDegrees);
            m_loadSeconds = Now - m_startTime;
            m_ready = true;
            m_activity = Label();
            Post(new ReadyMessage
            {
                splats = m_splats,
                loadSeconds = Math.Round(m_loadSeconds, 2),
                screenWidth = Screen.width,
                screenHeight = Screen.height,
                view = k_views[(int)player.View],
                inputSource = m_input.SourceName,
                arrowKeysTurn = m_input.ArrowKeysTurn
            });
            PostFile("report", "client.json", BrowserBridge.BrowserInfoJson());
        }

        // ------------------------------------------------------------------ loading
        GsplatRenderer m_renderer;

        IEnumerator LoadSplat()
        {
            var file = m_site.splat.file;
            byte[] bytes;
            var request = NewGet(Url(DemoPaths.FixtureBase + file, EditorPath("Fixtures/Generated/" + file)), out var refused);
            if (request == null)
            {
                Fail($"Could not request {file}: {refused}");
                yield break;
            }
            using (request)
            {
                var operation = request.SendWebRequest();
                while (!operation.isDone)
                {
                    Status("download", $"Downloading the synthetic room ({request.downloadedBytes / 1048576.0:F1} MB)",
                        0.05f + 0.6f * request.downloadProgress);
                    yield return null;
                }
                if (request.result != UnityWebRequest.Result.Success)
                {
                    Fail($"Could not download {file}: {request.error}. Start the demo with the provided launcher so the room file is served.");
                    yield break;
                }
                bytes = request.downloadHandler.data;
            }

            Status("decode", $"Preparing {m_site.splat.splats:N0} splats", 0.7f);
            yield return null;  // let the status paint before the synchronous decode
            GsplatAsset asset;
            try
            {
                asset = GsplatRuntimeLoader.Load(bytes, GsplatFileFormat.Ply, CompressionMode.Spark, SourceCoordinates.RUB);
                asset.name = file;
            }
            catch (Exception e)
            {
                Fail($"Could not decode {file}: {e.GetType().Name}: {e.Message}");
                yield break;
            }

            var go = new GameObject("Synthetic room splat (picture only; no collision)");
            go.SetActive(false);
            var renderer = go.AddComponent<GsplatRenderer>();
            renderer.GsplatAsset = asset;
            go.SetActive(true);

            var started = Now;
            while (renderer.SplatCount < asset.SplatCount)
            {
                if (Now - started > uploadTimeoutSeconds)
                {
                    Fail($"The splat upload did not finish within {uploadTimeoutSeconds:F0} s.");
                    yield break;
                }
                Status("upload", "Uploading splats to the GPU", 0.75f + 0.2f * renderer.SplatCount / Mathf.Max(1f, asset.SplatCount));
                yield return null;
            }
            m_splats = (int)asset.SplatCount;
            m_renderer = renderer;
            Status("ready", "Ready", 1f);
        }

        void BuildProxies()
        {
            var root = new GameObject("Site proxies (from site.json)").transform;
            foreach (var box in m_site.obstacles ?? Array.Empty<DemoBox>())
            {
                var go = new GameObject("Obstacle: " + box.name);
                go.transform.SetParent(root, false);
                go.transform.position = V(box.center);
                go.AddComponent<BoxCollider>().size = V(box.size);
            }
            var names = new Dictionary<string, string>();
            foreach (var record in m_site.records)
                names[record.recordId] = record.name;
            foreach (var anchor in m_site.anchors ?? Array.Empty<DemoAnchorDefinition>())
            {
                var go = new GameObject($"Anchor: {names[anchor.recordId]} ({anchor.anchorId})");
                go.transform.SetParent(root, false);
                go.transform.position = V(anchor.center);
                var collider = go.AddComponent<BoxCollider>();
                collider.size = V(anchor.size);
                var proxy = go.AddComponent<DemoAnchorProxy>();
                proxy.anchorId = anchor.anchorId;
                proxy.recordId = anchor.recordId;
                proxy.displayName = names[anchor.recordId];
                proxy.box = collider;
                m_proxies.Add(proxy);
                m_proxyByRecord.TryAdd(anchor.recordId, proxy);
            }
            Physics.SyncTransforms();
        }

        void SetupCamera()
        {
            if (!viewCamera)
                viewCamera = Camera.main;
            viewCamera.clearFlags = CameraClearFlags.SolidColor;
            viewCamera.backgroundColor = k_clearColor;
            viewCamera.fieldOfView = 60f;
            viewCamera.nearClipPlane = 0.05f;
            viewCamera.farClipPlane = 100f;
            var data = viewCamera.GetUniversalAdditionalCameraData();
            if (data)
            {
                data.renderPostProcessing = false;
                data.antialiasing = AntialiasingMode.None;
            }
        }

        // ------------------------------------------------------------------ frame
        void Update()
        {
            DrainFrameTimes();
            if (!m_ready)
                return;
            var frame = m_input.Read();
            HandlePointer(frame);
            player.Tick(frame, Time.deltaTime);
            if (frame.ToggleView)
                m_events.viewToggles++;
            if (frame.ResetView)
                m_events.viewResets++;
            m_activity = Label(frame);
            m_frame++;

            m_hudFrames++;
            m_hudElapsed += Time.unscaledDeltaTime;
            if (m_hudElapsed >= hudInterval)
            {
                Post(new HudMessage
                {
                    fps = m_hudFrames / m_hudElapsed,
                    frameMs = 1000f * m_hudElapsed / m_hudFrames,
                    screenWidth = Screen.width,
                    screenHeight = Screen.height,
                    view = k_views[(int)player.View]
                });
                m_hudFrames = 0;
                m_hudElapsed = 0f;
            }
            m_reportElapsed += Time.unscaledDeltaTime;
            if (m_reportElapsed >= reportInterval)
            {
                m_reportElapsed = 0f;
                PostSessionReport("periodic");
            }
        }

        void LateUpdate()
        {
            if (!m_ready)
                return;
            var proxy = selection.Selected;
            var visible = false;
            var position = Vector2.zero;
            if (proxy)
            {
                var bounds = proxy.WorldBounds;
                var screen = viewCamera.WorldToScreenPoint(bounds.center + Vector3.up * (bounds.extents.y + 0.12f));
                visible = screen.z > 0.05f && screen.x >= 0 && screen.y >= 0 && screen.x <= Screen.width && screen.y <= Screen.height;
                position = new Vector2(screen.x, screen.y);
            }
            if (visible != m_tagVisible || (visible && (position - m_lastTag).sqrMagnitude > 0.25f))
            {
                m_tagVisible = visible;
                m_lastTag = position;
                DemoBrowser.Tag(position.x, position.y, visible);
            }
        }

        void HandlePointer(in DemoInputFrame frame)
        {
            var center = new Vector2(Screen.width * 0.5f, Screen.height * 0.5f);
            DemoAnchorProxy hovered = null;
            if (frame.PointerLocked)
                hovered = selection.Pick(viewCamera, center);
            else if (frame.PointerOverView && !frame.Dragging && m_input.Allowed)
                hovered = selection.Pick(viewCamera, frame.PointerPosition);
            if (selection.Hover(hovered))
                Post(new HoverMessage { recordId = hovered ? hovered.recordId : "", name = hovered ? hovered.displayName : "" });

            if (frame.Select)
                SetSelection(selection.Pick(viewCamera, frame.PointerLocked ? center : frame.SelectPosition), "click");
            if (frame.Open)
            {
                var proxy = selection.Pick(viewCamera, frame.PointerLocked ? center : frame.OpenPosition);
                if (proxy)
                {
                    SetSelection(proxy, "right-click");
                    OpenRecord(proxy.recordId, "right-click", "");
                }
                else
                    Status("hint", "Nothing to open there. Right-click a rack, or use Equipment list (L).", 1f);
            }
        }

        void SetSelection(DemoAnchorProxy proxy, string how)
        {
            if (!selection.Select(proxy))
                return;
            if (proxy)
                m_events.selections++;
            Post(new SelectionMessage
            {
                recordId = proxy ? proxy.recordId : "",
                anchorId = proxy ? proxy.anchorId : "",
                name = proxy ? proxy.displayName : "",
                how = how
            });
        }

        void OpenRecord(string recordId, string how, string requestId)
        {
            m_store.Reload();  // pick up saves from another tab or an earlier session
            var view = m_store.Get(recordId);
            if (view == null)
            {
                Post(new ErrorMessage { text = "Unknown record " + recordId });
                return;
            }
            m_events.recordsOpened++;
            Post(new RecordMessage
            {
                type = "openRecord",
                requestId = requestId ?? "",
                how = how ?? "",
                readOnly = m_store.IsReadOnly,
                storeStatus = m_store.StatusMessage,
                record = view
            });
        }

        void DrainFrameTimes()
        {
            var samples = FrameTimer.Samples;
            if (samples.Count > 0)
            {
                foreach (var s in samples)
                    m_pacing.Add(m_activity, s.IntervalMs, s.CpuMs, s.SortMs);
                samples.Clear();
            }
            else if (!FrameTimer.Installed)
                m_pacing.Add(m_activity, Time.unscaledDeltaTime * 1000.0, -1, -1);
        }

        string Label(in DemoInputFrame frame = default)
        {
            int activity;
            if (m_typing)
                activity = 6;
            else if (!string.IsNullOrEmpty(m_panel))
                activity = 5;
            else if (!m_input.Allowed)
                activity = 7;
            else if (player.IsMoving || frame.Turn != 0f)
                activity = 1;
            else if (player.IsLooking)
                activity = player.View == DemoPlayer.ViewMode.ThirdPerson ? 3 : 2;
            else if (player.IsChangingHeight)
                activity = 4;
            else
                activity = 0;
            return k_labels[(int)player.View, activity];
        }

        static string[,] BuildLabels()
        {
            var labels = new string[k_views.Length, k_activities.Length];
            for (var v = 0; v < k_views.Length; v++)
                for (var a = 0; a < k_activities.Length; a++)
                    labels[v, a] = k_views[v] + "." + k_activities[a];
            return labels;
        }

        // ------------------------------------------------------------------ page -> Unity
        public void JsUiState(string json)
        {
            var state = Parse<UiState>(json);
            if (state == null)
                return;
            m_input.SetAllowed(state.inputAllowed);
            m_panel = state.panel ?? "";
            m_typing = state.typing;
            if (player)
                player.LookSpeedMultiplier = Mathf.Clamp(state.lookSpeed, 0.2f, 4f);
        }

        [Serializable]
        sealed class RecordRequest
        {
            public string recordId;
            public string how;
            public string requestId;
            public bool face;
        }

        public void JsOpenRecord(string json)
        {
            var request = Parse<RecordRequest>(json);
            if (!m_ready || request == null)
                return;
            if (m_proxyByRecord.TryGetValue(request.recordId ?? "", out var proxy))
                SetSelection(proxy, request.how ?? "page");
            OpenRecord(request.recordId, request.how, request.requestId);
        }

        public void JsSelectRecord(string json)
        {
            var request = Parse<RecordRequest>(json);
            if (!m_ready || request == null)
                return;
            if (!m_proxyByRecord.TryGetValue(request.recordId ?? "", out var proxy))
            {
                SetSelection(null, request.how ?? "page");
                return;
            }
            SetSelection(proxy, request.how ?? "page");
            if (request.face)
                player.FaceTowards(proxy.WorldBounds.center);
        }

        public void JsSaveRecord(string json)
        {
            var request = Parse<SaveRequest>(json);
            if (!m_ready || request == null)
                return;
            var result = m_store.Save(request.recordId, request.description, request.baseRevision);
            switch (result.Status)
            {
                case SaveStatus.Saved: m_events.saves++; break;
                case SaveStatus.NoChange: m_events.noChangeSaves++; break;
                case SaveStatus.Conflict: m_events.conflicts++; break;
                default: m_events.failedSaves++; break;
            }
            Post(new RecordMessage
            {
                type = "saveResult",
                requestId = request.requestId ?? "",
                status = result.Status.ToString(),
                message = result.Message ?? "",
                readOnly = m_store.IsReadOnly,
                storeStatus = m_store.StatusMessage,
                record = result.Record
            });
            if (result.Status == SaveStatus.Saved)
                PostSite();
        }

        public void JsCommand(string command)
        {
            if (!m_ready)
                return;
            switch (command)
            {
                case "toggleView":
                    player.SetView(player.View == DemoPlayer.ViewMode.FirstPerson
                        ? DemoPlayer.ViewMode.ThirdPerson
                        : DemoPlayer.ViewMode.FirstPerson);
                    m_events.viewToggles++;
                    break;
                case "resetView":
                    player.ResetView();
                    m_events.viewResets++;
                    break;
                case "deselect":
                    SetSelection(null, "page");
                    break;
                case "export":
                    m_events.exports++;
                    var stamp = DateTime.Now.ToString("yyyyMMdd-HHmmss", CultureInfo.InvariantCulture);
                    PostFile("export", $"vrhe-demo-records-{stamp}.json", m_store.ExportJson(m_origin, BuildLabel()));
                    break;
                case "clearData":
                    if (m_store.Clear(out var error))
                    {
                        m_events.clears++;
                        PostSite();
                        Status("hint", m_store.StatusMessage, 1f);
                    }
                    else
                        Post(new ErrorMessage { text = "Could not remove saved demo data: " + error });
                    break;
                case "report":
                    PostSessionReport("page request");
                    break;
                default:
                    Debug.LogWarning("[VRHE demo] unknown command " + command);
                    break;
            }
        }

        public void JsTest(string command)
        {
            var parts = (command ?? "").Split(':');
            var verb = parts[0];
            var arg = parts.Length > 1 ? parts[1] : "";
            switch (verb)
            {
                case "state":
                    Post(BuildState(arg));
                    break;
                case "pacingBegin":
                    m_pacing.BeginWindow(arg);
                    break;
                case "pacingEnd":
                    Post(new PacingMessage { requestId = arg, window = m_pacing.EndWindow() });
                    break;
                case "project":
                    var reply = new ProjectionMessage { recordId = arg, requestId = parts.Length > 2 ? parts[2] : "" };
                    if (m_ready && m_proxyByRecord.TryGetValue(arg, out var proxy))
                    {
                        var screen = viewCamera.WorldToScreenPoint(proxy.WorldBounds.center);
                        reply.visible = screen.z > 0f;
                        reply.x = screen.x;
                        reply.y = screen.y;
                    }
                    Post(reply);
                    break;
            }
        }

        StateMessage BuildState(string requestId)
        {
            var state = new StateMessage
            {
                requestId = requestId ?? "",
                ready = m_ready,
                inputAllowed = m_input.Allowed,
                screenWidth = Screen.width,
                screenHeight = Screen.height,
                frame = m_frame
            };
            if (!m_ready)
                return state;
            var feet = player.Feet;
            var cam = viewCamera.transform.position;
            state.view = k_views[(int)player.View];
            state.feet = new[] { feet.x, feet.y, feet.z };
            state.camera = new[] { cam.x, cam.y, cam.z };
            state.viewYaw = player.ViewYaw;
            state.bodyYaw = player.BodyYaw;
            state.pitch = player.Pitch;
            state.heightOffset = player.HeightOffset;
            state.eyeHeight = cam.y - feet.y;
            state.orbitDistance = player.orbitDistance;
            state.cameraDistance = player.CameraDistance;
            state.selectedRecordId = selection.Selected ? selection.Selected.recordId : "";
            state.hoveredRecordId = selection.Hovered ? selection.Hovered.recordId : "";
            state.lookSpeed = player.LookSpeedMultiplier;
            return state;
        }

        // ------------------------------------------------------------------ Unity -> page
        void PostSite()
        {
            var message = new SiteMessage
            {
                siteId = m_site.siteId,
                siteName = m_site.siteName,
                dataNotice = m_site.dataNotice,
                notice = DemoRecordStore.Notice,
                storageKey = m_store.StorageKey,
                storageDescription = m_store.StorageDescription,
                storeStatus = m_store.StatusMessage,
                readOnly = m_store.IsReadOnly,
                build = BuildLabel()
            };
            foreach (var view in m_store.All())
                message.records.Add(new RecordSummary
                {
                    recordId = view.recordId,
                    name = view.name,
                    kind = view.kind,
                    location = view.location,
                    revision = view.revision,
                    source = view.source
                });
            Post(message);
        }

        void PostSessionReport(string reason)
        {
            var report = new SessionReport
            {
                reason = reason,
                build = BuildLabel(),
                uptimeSeconds = Math.Round(Now - m_startTime, 1),
                loadSeconds = Math.Round(m_loadSeconds, 2),
                splats = m_splats,
                screenWidth = Screen.width,
                screenHeight = Screen.height,
                inputSource = m_input.SourceName,
                events = m_events,
                pacing = m_pacing.SessionStats()
            };
            PostFile("report", "session.json", JsonUtility.ToJson(report, true));
        }

        void PostFile(string type, string fileName, string json) =>
            Post(new FileMessage { type = type, fileName = fileName, json = json });

        void Status(string phase, string text, float progress) =>
            Post(new StatusMessage { phase = phase, text = text, progress = progress });

        void Fail(string text)
        {
            if (m_failed)
                return;
            m_failed = true;
            Debug.LogError("[VRHE demo] " + text);
            Post(new ErrorMessage { text = text });
        }

        // An exception inside the startup coroutine ends it without a word. Until the demo is
        // ready, show any exception on the page instead of an endless loading screen.
        void OnEnable() => Application.logMessageReceived += OnLogMessage;
        void OnDisable() => Application.logMessageReceived -= OnLogMessage;

        void OnLogMessage(string condition, string stackTrace, LogType type)
        {
            if (type == LogType.Exception && !m_ready && !m_failed)
                Fail("Unexpected error while starting the demo: " + condition);
        }

        static void Post(object message) => DemoBrowser.Post(JsonUtility.ToJson(message));

        string BuildLabel() => string.IsNullOrEmpty(m_build.label) ? Application.unityVersion : m_build.label;

        // ------------------------------------------------------------------ helpers
        static T Parse<T>(string json) where T : class
        {
            try
            {
                return JsonUtility.FromJson<T>(json);
            }
            catch (Exception e)
            {
                Debug.LogWarning($"[VRHE demo] ignored malformed {typeof(T).Name}: {e.Message}");
                return null;
            }
        }

        static Vector3 V(float[] v) => new(v[0], v[1], v[2]);

        static IEnumerator GetText(string url, string editorPath, Action<string, string> done)
        {
            var request = NewGet(Url(url, editorPath), out var refused);
            if (request == null)
            {
                done(null, refused);
                yield break;
            }
            using (request)
            {
                yield return request.SendWebRequest();
                if (request.result == UnityWebRequest.Result.Success)
                    done(request.downloadHandler.text, null);
                else
                    done(null, request.error);
            }
        }

        // UnityWebRequest validates the URL when it is created and throws for one it refuses
        // (see DemoPaths). Return null with the reason instead, so startup can report it.
        static UnityWebRequest NewGet(string url, out string error)
        {
            try
            {
                error = null;
                return UnityWebRequest.Get(url);
            }
            catch (Exception e)
            {
                error = $"{e.GetType().Name}: {e.Message} ({url})";
                return null;
            }
        }

        // In Editor play mode there is no page or server; read the project files directly.
        static string Url(string url, string editorPath) =>
#if UNITY_EDITOR
            editorPath != null ? "file://" + editorPath : url;
#else
            url;
#endif

        static string EditorPath(string projectRelative) =>
#if UNITY_EDITOR
            System.IO.Path.GetFullPath(System.IO.Path.Combine(Application.dataPath, "..", projectRelative));
#else
            null;
#endif
    }
}
