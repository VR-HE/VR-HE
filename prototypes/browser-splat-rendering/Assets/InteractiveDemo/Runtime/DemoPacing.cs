// VR-HE interactive browser demo: frame pacing by activity.
//
// Every frame interval is filed under what the user was doing in that frame (idle, moving,
// looking, changing height, using a panel, typing) and the view mode, so movement and panel
// use are reported separately instead of one idle average. Intervals come from FrameTimer
// (frame start to next frame start on the main thread) when it has a sample, otherwise from
// Time.unscaledDeltaTime. Histograms use 0.5 ms bins up to 300 ms; percentiles are bin upper
// edges, so they are conservative by at most 0.5 ms.
//
// This measures what the browser delivered at the display's refresh rate (no frame cap is
// set). It is not a measure of uncapped capacity, and no pass/fail threshold is implied.

using System;
using System.Collections.Generic;

namespace VRHE.InteractiveDemo
{
    [Serializable]
    public sealed class PacingStats
    {
        public string label;
        public long frames;
        public double seconds;
        public double fps;
        public double meanMs;
        public double p50Ms;
        public double p95Ms;
        public double p99Ms;
        public double maxMs;
        public long over50Ms;
        public long over100Ms;
        public long cpuFrames;
        public double cpuMeanMs;
        public double cpuP95Ms;
        public double sortMeanMs;
    }

    public sealed class DemoPacing
    {
        const double k_binMs = 0.5;
        const int k_bins = 600;

        sealed class Histogram
        {
            public readonly int[] Intervals = new int[k_bins + 1];
            public readonly int[] Cpu = new int[k_bins + 1];
            public long Frames, CpuFrames, Over50, Over100;
            public double SumMs, MaxMs, CpuSumMs, SortSumMs;

            public void Add(double intervalMs, double cpuMs, double sortMs)
            {
                Frames++;
                SumMs += intervalMs;
                if (intervalMs > MaxMs)
                    MaxMs = intervalMs;
                if (intervalMs > 50.0)
                    Over50++;
                if (intervalMs > 100.0)
                    Over100++;
                Intervals[Bin(intervalMs)]++;
                if (cpuMs >= 0)
                {
                    CpuFrames++;
                    CpuSumMs += cpuMs;
                    SortSumMs += Math.Max(0, sortMs);
                    Cpu[Bin(cpuMs)]++;
                }
            }

            static int Bin(double ms) => Math.Min(k_bins, Math.Max(0, (int)(ms / k_binMs)));
        }

        readonly SortedDictionary<string, Histogram> m_session = new(StringComparer.Ordinal);
        Histogram m_window;

        public string WindowLabel { get; private set; }
        public bool WindowOpen => m_window != null;

        public void Add(string activity, double intervalMs, double cpuMs, double sortMs)
        {
            if (intervalMs <= 0 || double.IsNaN(intervalMs))
                return;
            if (!m_session.TryGetValue(activity, out var histogram))
                m_session[activity] = histogram = new Histogram();
            histogram.Add(intervalMs, cpuMs, sortMs);
            m_window?.Add(intervalMs, cpuMs, sortMs);
        }

        /// <summary>Starts a labelled measurement window (used by the automated browser checks).</summary>
        public void BeginWindow(string label)
        {
            WindowLabel = string.IsNullOrEmpty(label) ? "window" : label;
            m_window = new Histogram();
        }

        public PacingStats EndWindow()
        {
            var stats = Summarize(WindowLabel ?? "window", m_window ?? new Histogram());
            m_window = null;
            return stats;
        }

        public List<PacingStats> SessionStats()
        {
            var list = new List<PacingStats>(m_session.Count);
            foreach (var pair in m_session)
                list.Add(Summarize(pair.Key, pair.Value));
            return list;
        }

        static PacingStats Summarize(string label, Histogram h)
        {
            var stats = new PacingStats { label = label, frames = h.Frames, cpuFrames = h.CpuFrames };
            if (h.Frames == 0)
                return stats;
            stats.seconds = h.SumMs / 1000.0;
            stats.fps = h.Frames / stats.seconds;
            stats.meanMs = h.SumMs / h.Frames;
            stats.p50Ms = Percentile(h.Intervals, h.Frames, 0.50);
            stats.p95Ms = Percentile(h.Intervals, h.Frames, 0.95);
            stats.p99Ms = Percentile(h.Intervals, h.Frames, 0.99);
            stats.maxMs = h.MaxMs;
            stats.over50Ms = h.Over50;
            stats.over100Ms = h.Over100;
            if (h.CpuFrames > 0)
            {
                stats.cpuMeanMs = h.CpuSumMs / h.CpuFrames;
                stats.cpuP95Ms = Percentile(h.Cpu, h.CpuFrames, 0.95);
                stats.sortMeanMs = h.SortSumMs / h.CpuFrames;
            }
            return stats;
        }

        static double Percentile(int[] bins, long total, double q)
        {
            var target = Math.Max(1, (long)Math.Ceiling(q * total));
            long cumulative = 0;
            for (var i = 0; i < bins.Length; i++)
            {
                cumulative += bins[i];
                if (cumulative >= target)
                    return (i + 1) * k_binMs;
            }
            return bins.Length * k_binMs;
        }
    }
}
