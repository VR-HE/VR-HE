// VR-HE interactive browser demo: Unity <-> page bridge (C# side: Runtime/DemoBrowser.cs).
//
// Unity -> page: VRHE_Demo_Post(json) hands one message to window.VRHEDemoPage.onUnityMessage;
// VRHE_Demo_Tag positions the floating label. Page -> Unity uses unityInstance.SendMessage on
// the "VRHEDemo" object (see DemoApp.cs). Mouse input is collected by the page (demo-ui.js),
// because the page owns pointer lock, the context menu and click-versus-drag decisions; Unity
// pulls one packed frame per update with VRHE_Demo_TakeMouse.
//
// Storage calls wrap window.localStorage, which is per browser profile and per origin
// (scheme + host + port). Every call is guarded: storage can be disabled, full or blocked.
// Nothing here sends data off the computer.
mergeInto(LibraryManager.library, {
  $VRHEDemoString: function (text) {
    var size = lengthBytesUTF8(text) + 1;
    var buffer = _malloc(size);
    stringToUTF8(text, buffer, size);
    return buffer;
  },

  VRHE_Demo_Post__deps: ['$VRHEDemoString'],
  VRHE_Demo_Post: function (jsonPtr) {
    var text = UTF8ToString(jsonPtr);
    try {
      if (window.VRHEDemoPage) window.VRHEDemoPage.onUnityMessage(text);
    } catch (e) {
      console.error('[VRHE demo] page message handler failed: ' + (e && e.stack ? e.stack : e));
    }
  },

  VRHE_Demo_Tag: function (x, y, visible) {
    try {
      if (window.VRHEDemoPage) window.VRHEDemoPage.onTag(x, y, visible !== 0);
    } catch (e) {
      // the label is cosmetic; never let it break the frame
    }
  },

  // Fills a float[length] buffer owned by C#; returns the number of values written.
  VRHE_Demo_TakeMouse: function (bufferPtr, length) {
    var page = window.VRHEDemoPage;
    if (!page || !page.takeMouseFrame) return 0;
    var values = page.takeMouseFrame();
    var n = Math.min(length, values.length);
    var base = bufferPtr >> 2;
    for (var i = 0; i < n; i++) HEAPF32[base + i] = values[i];
    return n;
  },

  VRHE_Demo_StorageGet__deps: ['$VRHEDemoString'],
  VRHE_Demo_StorageGet: function (keyPtr) {
    var result;
    try {
      var value = window.localStorage.getItem(UTF8ToString(keyPtr));
      result = { ok: true, found: value !== null, value: value === null ? '' : value, error: '' };
    } catch (e) {
      result = { ok: false, found: false, value: '', error: String(e && e.name ? e.name + ': ' + e.message : e) };
    }
    return VRHEDemoString(JSON.stringify(result));
  },

  VRHE_Demo_StorageSet__deps: ['$VRHEDemoString'],
  VRHE_Demo_StorageSet: function (keyPtr, valuePtr) {
    var result;
    try {
      window.localStorage.setItem(UTF8ToString(keyPtr), UTF8ToString(valuePtr));
      result = { ok: true, found: true, value: '', error: '' };
    } catch (e) {
      result = { ok: false, found: false, value: '', error: String(e && e.name ? e.name + ': ' + e.message : e) };
    }
    return VRHEDemoString(JSON.stringify(result));
  },

  VRHE_Demo_StorageRemove__deps: ['$VRHEDemoString'],
  VRHE_Demo_StorageRemove: function (keyPtr) {
    var result;
    try {
      window.localStorage.removeItem(UTF8ToString(keyPtr));
      result = { ok: true, found: false, value: '', error: '' };
    } catch (e) {
      result = { ok: false, found: false, value: '', error: String(e && e.name ? e.name + ': ' + e.message : e) };
    }
    return VRHEDemoString(JSON.stringify(result));
  },

  VRHE_Demo_PageOrigin__deps: ['$VRHEDemoString'],
  VRHE_Demo_PageOrigin: function () {
    var origin = '';
    try { origin = window.location.origin; } catch (e) { origin = ''; }
    return VRHEDemoString(origin);
  }
});
