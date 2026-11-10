// VR-HE browser splat-rendering prototype: per-frame stage timing.
// Test instrumentation only; it reads no capture or operational data.

using System.Collections.Generic;
using UnityEngine;
using UnityEngine.LowLevel;
using UnityEngine.PlayerLoop;
using UnityEngine.Rendering;

namespace VRHE.BrowserSplatTest
{
    /// <summary>One completed frame. Times are milliseconds.</summary>
    public struct FrameSample
    {
        public double IntervalMs;   // frame start to next frame start (browser frame pacing)
        public double CpuMs;        // frame start to end of URP context rendering
        public double SortMs;       // UnitySplats player-loop hook: CPU sort, order upload, draw submission
        public double RenderMs;     // end of that hook to end of URP context rendering
    }

    /// <summary>
    /// Records timestamps at four points of each frame by inserting player-loop systems:
    /// frame start (first Initialization system), immediately before and after the UnitySplats
    /// hook (which UnitySplats installs at the start of PostLateUpdate), and the end of URP
    /// context rendering. A frame's sample is completed when the next frame starts.
    /// GPU execution is asynchronous in WebGL, so these are main-thread costs, not GPU times.
    /// Browser timer precision limits single-frame resolution; averages remain useful.
    /// </summary>
    public static class FrameTimer
    {
        struct VrheFrameStart { }
        struct VrheSortStart { }
        struct VrheSortEnd { }

        const string k_gsplatHookTypeName = "Gsplat.GsplatPlayerLoopHook";

        static double s_frameStart = -1, s_sortStart = -1, s_sortEnd = -1, s_renderEnd = -1;
        static readonly List<FrameSample> s_samples = new();

        public static bool Installed { get; private set; }
        public static bool GsplatHookFound { get; private set; }
        public static bool Recording { get; set; }
        public static List<FrameSample> Samples => s_samples;

        static double Now => Time.realtimeSinceStartupAsDouble * 1000.0;

        // BeforeSceneLoad runs after SubsystemRegistration, where UnitySplats installs its hook.
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Install()
        {
            if (Installed)
                return;
            var loop = PlayerLoop.GetCurrentPlayerLoop();
            for (var i = 0; i < loop.subSystemList.Length; i++)
            {
                ref var phase = ref loop.subSystemList[i];
                if (phase.type == typeof(Initialization))
                    phase.subSystemList = Insert(phase.subSystemList, 0,
                        new PlayerLoopSystem { type = typeof(VrheFrameStart), updateDelegate = OnFrameStart });
                else if (phase.type == typeof(PostLateUpdate))
                    phase.subSystemList = WrapGsplatHook(phase.subSystemList);
            }
            PlayerLoop.SetPlayerLoop(loop);
            RenderPipelineManager.endContextRendering += (_, _) => s_renderEnd = Now;
            Installed = true;
        }

        static PlayerLoopSystem[] WrapGsplatHook(PlayerLoopSystem[] systems)
        {
            var list = new List<PlayerLoopSystem>(systems ?? new PlayerLoopSystem[0]);
            var index = list.FindIndex(s => s.type != null && s.type.FullName == k_gsplatHookTypeName);
            GsplatHookFound = index >= 0;
            if (index < 0)
                index = 0; // fall back to timing from the start of PostLateUpdate
            list.Insert(GsplatHookFound ? index + 1 : index,
                new PlayerLoopSystem { type = typeof(VrheSortEnd), updateDelegate = () => s_sortEnd = Now });
            list.Insert(index,
                new PlayerLoopSystem { type = typeof(VrheSortStart), updateDelegate = () => s_sortStart = Now });
            return list.ToArray();
        }

        static PlayerLoopSystem[] Insert(PlayerLoopSystem[] systems, int index, PlayerLoopSystem system)
        {
            var list = new List<PlayerLoopSystem>(systems ?? new PlayerLoopSystem[0]);
            list.Insert(index, system);
            return list.ToArray();
        }

        static void OnFrameStart()
        {
            var now = Now;
            if (Recording && s_frameStart >= 0 && s_sortStart >= s_frameStart && s_sortEnd >= s_sortStart &&
                s_renderEnd >= s_sortEnd)
            {
                s_samples.Add(new FrameSample
                {
                    IntervalMs = now - s_frameStart,
                    CpuMs = s_renderEnd - s_frameStart,
                    SortMs = s_sortEnd - s_sortStart,
                    RenderMs = s_renderEnd - s_sortEnd
                });
            }
            s_frameStart = now;
            s_sortStart = s_sortEnd = s_renderEnd = -1;
        }

        public static void BeginRecording()
        {
            s_samples.Clear();
            Recording = true;
        }

        public static List<FrameSample> EndRecording()
        {
            Recording = false;
            return new List<FrameSample>(s_samples);
        }
    }
}
