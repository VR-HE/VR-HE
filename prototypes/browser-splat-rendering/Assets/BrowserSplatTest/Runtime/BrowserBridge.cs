// VR-HE browser splat-rendering prototype: C# side of BrowserBridge.jslib.

using System.Runtime.InteropServices;

namespace VRHE.BrowserSplatTest
{
    public static class BrowserBridge
    {
#if UNITY_WEBGL && !UNITY_EDITOR
        [DllImport("__Internal")] static extern string VRHE_GetBrowserInfoJson();
        [DllImport("__Internal")] static extern double VRHE_GetWasmHeapBytes();
        [DllImport("__Internal")] static extern double VRHE_GetJsHeapBytes();
        [DllImport("__Internal")] static extern void VRHE_SetStatus(string text);

        public static string BrowserInfoJson() => VRHE_GetBrowserInfoJson();
        public static double WasmHeapBytes() => VRHE_GetWasmHeapBytes();
        public static double JsHeapBytes() => VRHE_GetJsHeapBytes();
        public static void SetStatus(string text) => VRHE_SetStatus(text);
#else
        public static string BrowserInfoJson() => "{\"contextSource\":\"not-webgl\"}";
        public static double WasmHeapBytes() => -1;
        public static double JsHeapBytes() => -1;
        public static void SetStatus(string text) => UnityEngine.Debug.Log("[VRHE] " + text);
#endif
    }
}
