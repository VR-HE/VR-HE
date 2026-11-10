// VR-HE browser splat-rendering prototype: small browser queries for the benchmark.
// Reads browser/WebGL capability strings and updates the page status line. It sends nothing;
// results are posted by Unity's own UnityWebRequest to the local test server.
mergeInto(LibraryManager.library, {
  VRHE_GetBrowserInfoJson: function () {
    var info = {};
    try {
      info.userAgent = navigator.userAgent;
      info.platform = navigator.platform;
      info.hardwareConcurrency = navigator.hardwareConcurrency;
      info.deviceMemoryGb = (typeof navigator.deviceMemory === 'number') ? navigator.deviceMemory : null;
      info.devicePixelRatio = window.devicePixelRatio;
      info.screen = [screen.width, screen.height];
      info.crossOriginIsolated = window.crossOriginIsolated === true;
      info.webgpuApiPresent = !!navigator.gpu;
      // Prefer Emscripten's current context; otherwise getContext on Unity's canvas returns the
      // context Unity already created (same type), without creating a new one.
      var gl = null;
      info.contextSource = 'none';
      if (typeof GLctx !== 'undefined' && GLctx) {
        gl = GLctx;
        info.contextSource = 'GLctx';
      } else if (typeof Module !== 'undefined' && Module['canvas']) {
        gl = Module['canvas'].getContext('webgl2') || Module['canvas'].getContext('webgl');
        if (gl) info.contextSource = 'unity-canvas';
      }
      if (gl) {
        info.isWebGL2 = (typeof WebGL2RenderingContext !== 'undefined') && (gl instanceof WebGL2RenderingContext);
        info.glVersion = gl.getParameter(gl.VERSION);
        info.glslVersion = gl.getParameter(gl.SHADING_LANGUAGE_VERSION);
        info.glVendor = gl.getParameter(gl.VENDOR);
        info.glRenderer = gl.getParameter(gl.RENDERER);
        var dbg = gl.getExtension('WEBGL_debug_renderer_info');
        if (dbg) {
          info.unmaskedVendor = gl.getParameter(dbg.UNMASKED_VENDOR_WEBGL);
          info.unmaskedRenderer = gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL);
        }
        info.maxTextureSize = gl.getParameter(gl.MAX_TEXTURE_SIZE);
        info.maxVertexTextureImageUnits = gl.getParameter(gl.MAX_VERTEX_TEXTURE_IMAGE_UNITS);
        info.contextAttributes = gl.getContextAttributes();
        info.extensions = gl.getSupportedExtensions();
      }
    } catch (e) {
      info.error = String(e);
    }
    var text = JSON.stringify(info);
    var size = lengthBytesUTF8(text) + 1;
    var buffer = _malloc(size);
    stringToUTF8(text, buffer, size);
    return buffer;
  },

  VRHE_GetWasmHeapBytes: function () {
    return (typeof HEAPU8 !== 'undefined') ? HEAPU8.length : -1;
  },

  VRHE_GetJsHeapBytes: function () {
    return (performance && performance.memory) ? performance.memory.usedJSHeapSize : -1;
  },

  VRHE_SetStatus: function (textPtr) {
    var el = document.getElementById('vrhe-status');
    if (el) el.textContent = UTF8ToString(textPtr);
  }
});
