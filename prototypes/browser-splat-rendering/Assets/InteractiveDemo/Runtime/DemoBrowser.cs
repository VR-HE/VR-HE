// VR-HE interactive browser demo: C# side of Plugins/WebGL/DemoBridge.jslib.
// Outside a WebGL player (Editor play mode) the calls fall back to the console and in-memory
// storage, so the scene can still be opened and stepped through without a browser.

using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using UnityEngine;
using VRHE.InteractiveDemo.Records;

namespace VRHE.InteractiveDemo
{
    public static class DemoBrowser
    {
        // Packed mouse frame written by demo-ui.js takeMouseFrame(); keep both sides in step.
        public const int MouseFrameLength = 12;
        public const int MouseDx = 0, MouseDy = 1, MouseWheel = 2;
        public const int LeftClicks = 3, LeftX = 4, LeftY = 5;
        public const int RightClicks = 6, RightX = 7, RightY = 8;
        public const int PointerX = 9, PointerY = 10, Flags = 11;
        public const int FlagOverView = 1, FlagLocked = 2, FlagDragging = 4;

#if UNITY_WEBGL && !UNITY_EDITOR
        [DllImport("__Internal")] static extern void VRHE_Demo_Post(string json);
        [DllImport("__Internal")] static extern void VRHE_Demo_Tag(float x, float y, int visible);
        [DllImport("__Internal")] static extern int VRHE_Demo_TakeMouse(float[] buffer, int length);
        [DllImport("__Internal")] static extern string VRHE_Demo_StorageGet(string key);
        [DllImport("__Internal")] static extern string VRHE_Demo_StorageSet(string key, string value);
        [DllImport("__Internal")] static extern string VRHE_Demo_StorageRemove(string key);
        [DllImport("__Internal")] static extern string VRHE_Demo_StorageKeys(string prefix);
        [DllImport("__Internal")] static extern string VRHE_Demo_PageOrigin();

        public static bool IsBrowser => true;
        public static void Post(string json) => VRHE_Demo_Post(json);
        public static void Tag(float x, float y, bool visible) => VRHE_Demo_Tag(x, y, visible ? 1 : 0);
        public static int TakeMouse(float[] buffer) => VRHE_Demo_TakeMouse(buffer, buffer.Length);
        public static string StorageGet(string key) => VRHE_Demo_StorageGet(key);
        public static string StorageSet(string key, string value) => VRHE_Demo_StorageSet(key, value);
        public static string StorageRemove(string key) => VRHE_Demo_StorageRemove(key);
        public static string StorageKeys(string prefix) => VRHE_Demo_StorageKeys(prefix);
        public static string PageOrigin() => VRHE_Demo_PageOrigin();
#else
        public static bool IsBrowser => false;
        public static void Post(string json) => Debug.Log("[VRHE demo -> page] " + json);
        public static void Tag(float x, float y, bool visible) { }
        public static int TakeMouse(float[] buffer) => 0;
        public static string StorageGet(string key) => throw new NotSupportedException("browser storage outside WebGL");
        public static string StorageSet(string key, string value) => throw new NotSupportedException("browser storage outside WebGL");
        public static string StorageRemove(string key) => throw new NotSupportedException("browser storage outside WebGL");
        public static string StorageKeys(string prefix) => throw new NotSupportedException("browser storage outside WebGL");
        public static string PageOrigin() => "editor";
#endif
    }

    /// <summary>IKeyValueStorage over window.localStorage (per browser profile and origin).</summary>
    public sealed class BrowserLocalStorage : IKeyValueStorage
    {
        [Serializable]
        sealed class Envelope
        {
            public bool ok;
            public bool found;
            public string value;
            public string error;
            public string[] keys;
        }

        readonly string m_origin;

        public BrowserLocalStorage(string origin) => m_origin = origin;

        public string Description => $"browser local storage for {m_origin} in this browser profile";

        public bool TryRead(string key, out string value, out string error)
        {
            var envelope = Call(() => DemoBrowser.StorageGet(key));
            value = envelope.ok && envelope.found ? envelope.value ?? "" : null;
            error = envelope.ok ? null : envelope.error;
            return envelope.ok;
        }

        public bool TryWrite(string key, string value, out string error)
        {
            var envelope = Call(() => DemoBrowser.StorageSet(key, value));
            error = envelope.ok ? null : envelope.error;
            return envelope.ok;
        }

        public bool TryRemove(string key, out string error)
        {
            var envelope = Call(() => DemoBrowser.StorageRemove(key));
            error = envelope.ok ? null : envelope.error;
            return envelope.ok;
        }

        public bool TryListKeys(string prefix, out List<string> keys, out string error)
        {
            var envelope = Call(() => DemoBrowser.StorageKeys(prefix));
            keys = new List<string>(envelope.ok && envelope.keys != null ? envelope.keys : Array.Empty<string>());
            error = envelope.ok ? null : envelope.error;
            return envelope.ok;
        }

        static Envelope Call(Func<string> call)
        {
            try
            {
                return JsonUtility.FromJson<Envelope>(call()) ?? new Envelope { error = "empty storage reply" };
            }
            catch (Exception e)
            {
                return new Envelope { ok = false, error = e.GetType().Name + ": " + e.Message };
            }
        }
    }
}
