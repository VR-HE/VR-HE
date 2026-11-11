// VR-HE interactive browser demo: page interface and Unity bridge (PROTOTYPE).
//
// Division of work
//   Page (this file): panels, help, record editor, equipment list, export download, mouse
//   handling (click versus drag, right-click, wheel, pointer lock), the input gate and local
//   results reporting to the demo server on 127.0.0.1.
//   Unity (Assets/InteractiveDemo): 3D view, walking, camera, picking, highlights and the
//   provisional record store in this browser profile's localStorage.
//
// Bridge contract
//   Unity -> page: window.VRHEDemoPage.onUnityMessage(json) with a "type" field (see
//   DemoMessages.cs), onTag(x, y, visible) for the floating label, and takeMouseFrame(), which
//   Unity polls once per frame. Unity coordinates are canvas pixels with the origin at the
//   bottom-left; page coordinates are CSS pixels from the top-left.
//   Page -> Unity: unityInstance.SendMessage('VRHEDemo', method, text); see DemoApp.cs.
//   SendMessage runs synchronously, so replies tagged with a requestId are available when the
//   call returns.
//
// Input gate: Unity acts on keyboard and mouse only while the canvas has focus, the browser
// window has focus, no panel is open and no text field is focused. Each change is sent to
// Unity (JsUiState), which then forgets held keys, so text typed into a description never moves
// the view.
//
// Reporting: when served by Tools/demo_server.py on a loopback address, the page posts console
// output, a heartbeat, Unity's session report (timings and counts, no record text) and copies
// of exports to the server's local results folder. Nothing is sent anywhere else.
(function () {
  'use strict';

  var BRIDGE = 'VRHEDemo';
  var DRAG_SLOP = 5;           // CSS pixels of movement before a press becomes a drag
  var HEARTBEAT_MS = 5000;
  var STANDARD = { w: 1280, h: 720 };
  var PREFS_KEY = 'vrhe.demo.ui-preferences.v1';
  var PANELS = ['record', 'list', 'help', 'data'];

  function $(id) { return document.getElementById(id); }
  var canvas = $('unity-canvas');
  var stage = $('stage');

  var session = makeSessionId();
  var reporting = location.protocol === 'http:' &&
    /^(127\.0\.0\.1|localhost|\[::1\])$/.test(location.hostname);
  var unity = null;
  var ready = false;
  var requestCounter = 0;
  var replies = {};

  var page = {
    panel: '',
    typing: false,
    focused: false,
    windowFocused: document.hasFocus(),
    locked: false,
    large: false,
    selected: '',
    selectedName: '',
    hovered: '',
    view: 'first',
    site: null,
    records: [],
    base: null,          // record as opened or last saved: {recordId, revision, description, ...}
    conflict: null,
    saving: false,
    pendingDiscard: null,
    lastGate: '',
    hud: null,
    lastSave: null,
    lastExport: null,
    lastError: '',
    messages: 0,
    lookSpeed: clamp(Number(loadPrefs().lookSpeed) || 1, 0.25, 3)
  };

  var mouse = {
    dx: 0, dy: 0, wheel: 0,
    leftClicks: 0, leftX: 0, leftY: 0,
    rightClicks: 0, rightX: 0, rightY: 0,
    px: 0, py: 0, over: false, dragging: false,
    down: null
  };

  // ------------------------------------------------------------------ local reporting
  var logQueue = [];
  var logSeq = 0;
  var logBusy = false;

  function post(path, body, contentType) {
    if (!reporting) return;
    try {
      fetch(path, {
        method: 'POST',
        headers: { 'Content-Type': contentType || 'application/json' },
        body: body,
        keepalive: body.length < 60000
      }).catch(function () {});
    } catch (e) {
      // reporting is best effort
    }
  }

  function postReport(name, json) {
    var path = 'report/' + encodeURIComponent(session) + '/' + encodeURIComponent(name);
    if (document.visibilityState === 'hidden' && reporting && navigator.sendBeacon) {
      try {
        if (navigator.sendBeacon(path, new Blob([json], { type: 'application/json' }))) return;
      } catch (e) {
        // fall back to fetch
      }
    }
    post(path, json);
  }

  function flushLog() {
    if (!reporting || logBusy || logQueue.length === 0) return;
    logBusy = true;
    var batch = logQueue.splice(0, logQueue.length);
    fetch('log/' + encodeURIComponent(session), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(batch)
    }).catch(function () {}).finally(function () {
      logBusy = false;
      if (logQueue.length) setTimeout(flushLog, 100);
    });
  }

  function recordLog(level, args) {
    var text;
    try {
      text = Array.prototype.map.call(args, function (a) {
        if (a && a.stack) return String(a.stack);
        return (typeof a === 'object') ? JSON.stringify(a) : String(a);
      }).join(' ');
    } catch (e) {
      text = String(args && args[0]);
    }
    if (logQueue.length < 5000)
      logQueue.push({ seq: logSeq++, t: Math.round(performance.now()), level: level, text: text.slice(0, 4000) });
    setTimeout(flushLog, 0);
  }

  ['log', 'info', 'warn', 'error'].forEach(function (level) {
    var original = console[level];
    console[level] = function () {
      recordLog(level, arguments);
      return original.apply(console, arguments);
    };
  });
  window.addEventListener('error', function (e) {
    recordLog('pageerror', [e.message + ' @ ' + e.filename + ':' + e.lineno]);
  });
  window.addEventListener('unhandledrejection', function (e) {
    recordLog('unhandledrejection', [e.reason]);
  });

  // Catch focus changes that arrive without an event (for example a window activated by the OS).
  setInterval(function () { if (ready) pushUiState(); }, 500);

  setInterval(function () {
    post('heartbeat', JSON.stringify({ session: session, ready: ready, visible: !document.hidden, t: Date.now() }));
  }, HEARTBEAT_MS);

  // ------------------------------------------------------------------ helpers
  function clamp(v, lo, hi) { return Math.min(hi, Math.max(lo, v)); }

  function pad(n) { return String(n).padStart(2, '0'); }

  function makeSessionId() {
    var d = new Date();
    var r = new Uint8Array(3);
    (window.crypto || {}).getRandomValues ? window.crypto.getRandomValues(r) : r.fill(0);
    return 'demo-' + d.getFullYear() + pad(d.getMonth() + 1) + pad(d.getDate()) + '-' +
      pad(d.getHours()) + pad(d.getMinutes()) + pad(d.getSeconds()) + '-' +
      Array.prototype.map.call(r, function (b) { return b.toString(16).padStart(2, '0'); }).join('');
  }

  function loadPrefs() {
    try {
      return JSON.parse(window.localStorage.getItem(PREFS_KEY) || '{}') || {};
    } catch (e) {
      return {};
    }
  }

  function savePrefs() {
    try {
      window.localStorage.setItem(PREFS_KEY, JSON.stringify({ lookSpeed: page.lookSpeed }));
    } catch (e) {
      // preferences are optional
    }
  }

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function nextRequestId() { return 'r' + (++requestCounter); }

  function timeNow() {
    var d = new Date();
    return pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds());
  }

  function isTextField(node) {
    if (!node) return false;
    if (node.isContentEditable) return true;
    if (node.tagName === 'TEXTAREA') return true;
    return node.tagName === 'INPUT' && /^(text|search|email|number|password|url|tel)$/i.test(node.type || 'text');
  }

  function hint(text, tone) {
    var line = $('statusline');
    line.textContent = text || '';
    line.title = text || '';   // the full text when the top bar is too narrow
    line.style.color = tone === 'bad' ? 'var(--bad)' : tone === 'good' ? 'var(--good)' : '';
  }

  function setStatus(id, text, tone) {
    var node = $(id);
    node.textContent = text || '';
    node.className = 'status' + (tone ? ' ' + tone : '');
  }

  function send(method, text) {
    if (!unity) return false;
    try {
      unity.SendMessage(BRIDGE, method, text);
      return true;
    } catch (e) {
      console.error('[VRHE demo] SendMessage ' + method + ' failed: ' + e);
      return false;
    }
  }

  function command(name) { send('JsCommand', name); }

  function focusView() {
    try {
      canvas.focus({ preventScroll: true });
    } catch (e) {
      canvas.focus();
    }
  }

  // ------------------------------------------------------------------ layout
  function layout() {
    var chrome = $('topbar').offsetHeight + $('toolbar').offsetHeight + 16;
    var availW = Math.max(320, window.innerWidth - 16);
    var availH = Math.max(180, window.innerHeight - chrome);
    var w = page.large ? availW : Math.min(STANDARD.w, availW);
    var h = Math.round(w * 9 / 16);
    if (h > availH) {
      h = availH;
      w = Math.round(h * 16 / 9);
    }
    canvas.style.width = Math.floor(w) + 'px';
    canvas.style.height = Math.floor(h) + 'px';
    $('btn-size').textContent = page.large ? 'Standard view' : 'Larger view';
    updateHud();
  }

  function updateHud() {
    var text = canvas.width + 'x' + canvas.height + ' px';
    if (!page.large && (canvas.width < STANDARD.w || canvas.height < STANDARD.h)) text += ' (reduced to fit)';
    if (page.hud) {
      text += ' | ' + page.hud.fps.toFixed(0) + ' fps';
      if (page.hud.screenWidth !== canvas.width || page.hud.screenHeight !== canvas.height)
        text += ' | Unity ' + page.hud.screenWidth + 'x' + page.hud.screenHeight;
    } else {
      text += ' | -- fps';
    }
    $('hud').textContent = text;
  }

  // ------------------------------------------------------------------ input gate
  function gateOpen() {
    // document.hasFocus() is read live: a cached window-focus flag can miss the first focus event.
    page.windowFocused = document.hasFocus();
    return ready && !page.panel && !page.typing && page.focused && page.windowFocused;
  }

  function pushUiState(force) {
    var gate = gateOpen();
    var key = [gate, page.panel, page.typing, page.lookSpeed].join('|');
    updateHints();
    if (!force && key === page.lastGate) return;
    page.lastGate = key;
    send('JsUiState', JSON.stringify({
      inputAllowed: gate, panel: page.panel, typing: page.typing, lookSpeed: page.lookSpeed
    }));
  }

  function updateHints() {
    $('focus-hint').hidden = !(ready && !page.focused && !page.panel && !page.locked);
    $('crosshair').hidden = !page.locked;
    if (page.panel) $('tag').hidden = true;
  }

  canvas.addEventListener('focus', function () {
    page.focused = true;
    canvas.classList.add('focused');
    pushUiState();
  });
  canvas.addEventListener('blur', function () {
    page.focused = false;
    canvas.classList.remove('focused');
    pushUiState();
  });
  window.addEventListener('blur', function () {
    page.windowFocused = false;
    pushUiState();
  });
  window.addEventListener('focus', function () {
    page.windowFocused = true;
    pushUiState();
  });
  document.addEventListener('focusin', function (e) {
    page.typing = isTextField(e.target);
    pushUiState();
  });
  document.addEventListener('focusout', function () {
    setTimeout(function () {
      page.typing = isTextField(document.activeElement);
      pushUiState();
    }, 0);
  });

  // ------------------------------------------------------------------ mouse
  function toUnity(clientX, clientY) {
    var r = canvas.getBoundingClientRect();
    return [
      (clientX - r.left) * canvas.width / r.width,
      canvas.height - (clientY - r.top) * canvas.height / r.height
    ];
  }

  function takeMouseFrame() {
    var px = page.locked ? canvas.width / 2 : mouse.px;
    var py = page.locked ? canvas.height / 2 : mouse.py;
    var flags = (mouse.over ? 1 : 0) | (page.locked ? 2 : 0) | (mouse.dragging ? 4 : 0);
    var frame = [mouse.dx, mouse.dy, mouse.wheel, mouse.leftClicks, mouse.leftX, mouse.leftY,
      mouse.rightClicks, mouse.rightX, mouse.rightY, px, py, flags];
    mouse.dx = mouse.dy = mouse.wheel = 0;
    mouse.leftClicks = mouse.rightClicks = 0;
    return frame;
  }

  canvas.addEventListener('mousedown', function (e) {
    var wasFocused = page.focused && document.hasFocus();
    var consumed = false;
    if (page.panel) {
      consumed = true;        // a click on the view closes the open panel first
      closePanel();
      if (page.panel) {       // unsaved edits: keep focus on the discard question
        e.preventDefault();
        return;
      }
    } else if (!wasFocused) {
      consumed = true;        // the first click only gives the view the keyboard
    }
    focusView();
    var p = page.locked ? [canvas.width / 2, canvas.height / 2] : toUnity(e.clientX, e.clientY);
    mouse.down = { button: e.button, moved: 0, drag: false, consumed: consumed, ux: p[0], uy: p[1], pdx: 0, pdy: 0,
      lastX: e.clientX, lastY: e.clientY };
    if (e.button !== 0) e.preventDefault();
  });

  window.addEventListener('mousemove', function (e) {
    if (page.locked) {
      if (gateOpen()) {
        mouse.dx += e.movementX || 0;
        mouse.dy += e.movementY || 0;
      }
      return;
    }
    if (e.target === canvas) {
      var p = toUnity(e.clientX, e.clientY);
      mouse.px = p[0];
      mouse.py = p[1];
    }
    var d = mouse.down;
    if (!d || d.button !== 0 || d.consumed || !(e.buttons & 1)) return;
    // Unlocked drags use position differences (CSS pixels); movementX/Y is only needed, and
    // only used, under pointer lock, where the position stops changing.
    var mx = e.clientX - d.lastX;
    var my = e.clientY - d.lastY;
    d.lastX = e.clientX;
    d.lastY = e.clientY;
    d.moved += Math.abs(mx) + Math.abs(my);
    if (d.drag) {
      mouse.dx += mx;
      mouse.dy += my;
    } else {
      d.pdx += mx;
      d.pdy += my;
      if (d.moved > DRAG_SLOP && gateOpen()) {
        d.drag = true;
        mouse.dragging = true;
        mouse.dx += d.pdx;
        mouse.dy += d.pdy;
        canvas.classList.add('dragging');
      }
    }
  });

  window.addEventListener('mouseup', function (e) {
    var d = mouse.down;
    if (!d || d.button !== e.button) return;
    mouse.down = null;
    mouse.dragging = false;
    canvas.classList.remove('dragging');
    if (d.consumed || !gateOpen()) return;
    if (e.button === 0 && !d.drag) {
      mouse.leftClicks++;
      mouse.leftX = d.ux;
      mouse.leftY = d.uy;
    } else if (e.button === 2 && d.moved <= DRAG_SLOP) {
      mouse.rightClicks++;
      mouse.rightX = d.ux;
      mouse.rightY = d.uy;
    }
  });

  canvas.addEventListener('contextmenu', function (e) { e.preventDefault(); });
  canvas.addEventListener('mouseenter', function () { mouse.over = true; });
  canvas.addEventListener('mouseleave', function () { mouse.over = false; });
  canvas.addEventListener('wheel', function (e) {
    e.preventDefault();
    if (!gateOpen()) return;
    var notches = e.deltaY;
    if (e.deltaMode === 0) notches /= 100;
    else if (e.deltaMode === 1) notches /= 3;
    mouse.wheel += clamp(notches, -5, 5);
  }, { passive: false });
  canvas.addEventListener('touchstart', function () {
    hint('Touch controls are not part of this demo yet; use a keyboard and mouse.');
  }, { passive: true });

  // ------------------------------------------------------------------ pointer lock
  function toggleCapture() {
    if (!ready) return;
    if (page.locked) {
      document.exitPointerLock();
      return;
    }
    if (page.panel) closePanel();
    if (page.panel) return;   // waiting for a discard decision
    focusView();
    try {
      var request = canvas.requestPointerLock();
      if (request && request.catch)
        request.catch(function (err) {
          hint('The browser did not allow mouse capture (' + (err && err.name) + '). Click the view, then press M again.', 'bad');
        });
    } catch (err) {
      hint('The browser did not allow mouse capture. Click the view, then press M again.', 'bad');
    }
  }

  document.addEventListener('pointerlockchange', function () {
    page.locked = document.pointerLockElement === canvas;
    var button = $('btn-capture');
    button.classList.toggle('active', page.locked);
    button.innerHTML = page.locked ? 'Release mouse <kbd>Esc</kbd>' : 'Capture mouse <kbd>M</kbd>';
    hint(page.locked
      ? 'Mouse captured: move to look, click to select, right-click to open. Esc gives the pointer back.'
      : 'Mouse released. Drag on the view to look around.');
    updateHints();
  });
  document.addEventListener('pointerlockerror', function () {
    hint('The browser refused mouse capture. Click the view, then press M again.', 'bad');
  });

  // ------------------------------------------------------------------ keyboard
  document.addEventListener('keydown', function (e) {
    var key = e.key;
    if (key === 'Escape') {
      if (!$('rec-discard').hidden) {
        e.preventDefault();
        discardChoice(false);
      } else if (page.panel) {
        e.preventDefault();
        closePanel();
      }
      return;
    }
    if (page.panel === 'record' && key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      save();
      return;
    }
    if (isTextField(e.target)) return;   // typing never triggers shortcuts or movement
    if (e.ctrlKey || e.altKey || e.metaKey) return;
    var lower = key.length === 1 ? key.toLowerCase() : key;
    if (lower === 'h') {
      e.preventDefault();
      togglePanel('help');
      return;
    }
    if (lower === 'l') {
      e.preventDefault();
      togglePanel('list');
      return;
    }
    if (e.target !== canvas) return;
    if (lower === 'm') {
      e.preventDefault();
      toggleCapture();
    } else if (key === 'Enter') {
      e.preventDefault();
      inspectSelected('enter');
    } else if (key.indexOf('Arrow') === 0 || key === ' ') {
      e.preventDefault();      // keep the page from scrolling
    }
  });

  // ------------------------------------------------------------------ panels
  function openPanel(name) {
    if (page.panel === name) return;
    if (page.panel === 'record' && isDirty()) {
      confirmDiscard(function () { openPanel(name); });
      return;
    }
    if (page.locked) document.exitPointerLock();
    PANELS.forEach(function (p) { $('panel-' + p).hidden = p !== name; });
    $('rec-discard').hidden = true;
    $('data-reset-confirm').hidden = true;
    page.panel = name;
    if (name === 'list') renderList();
    if (name === 'data') renderData();
    var first = name === 'record' ? $('rec-description') : $('panel-' + name).querySelector('button');
    if (first) first.focus({ preventScroll: true });
    pushUiState();
  }

  function closePanel(force) {
    if (!page.panel) return;
    if (!force && page.panel === 'record' && isDirty()) {
      confirmDiscard(function () { closePanel(true); });
      return;
    }
    $('panel-' + page.panel).hidden = true;
    $('rec-discard').hidden = true;
    if (page.panel === 'record') {
      page.base = null;
      page.conflict = null;
    }
    page.panel = '';
    focusView();
    pushUiState();
  }

  function togglePanel(name) {
    if (page.panel === name) closePanel();
    else openPanel(name);
  }

  stage.addEventListener('click', function (e) {
    if (e.target.closest('[data-close]')) closePanel();
  });

  function isDirty() {
    return page.panel === 'record' && !!page.base && $('rec-description').value !== page.base.description;
  }

  function confirmDiscard(then) {
    page.pendingDiscard = then;
    $('rec-discard').hidden = false;
    $('rec-discard-no').focus({ preventScroll: true });
  }

  function discardChoice(discard) {
    $('rec-discard').hidden = true;
    var then = page.pendingDiscard;
    page.pendingDiscard = null;
    if (discard) {
      if (page.base) $('rec-description').value = page.base.description;
      updateCount();
      if (then) then();
    } else {
      $('rec-description').focus({ preventScroll: true });
    }
  }
  $('rec-discard-yes').addEventListener('click', function () { discardChoice(true); });
  $('rec-discard-no').addEventListener('click', function () { discardChoice(false); });

  // ------------------------------------------------------------------ records
  function inspectSelected(how) {
    if (!ready) return;
    if (!page.selected) {
      hint('Select a rack first: click it in the view, or pick one in the Equipment list (L).');
      if (how === 'button') openPanel('list');
      return;
    }
    openRecord(page.selected, how);
  }

  function openRecord(recordId, how) {
    send('JsOpenRecord', JSON.stringify({ recordId: recordId, how: how || 'page', requestId: nextRequestId() }));
  }

  function selectRecord(recordId, face, how) {
    send('JsSelectRecord', JSON.stringify({ recordId: recordId, face: !!face, how: how || 'list' }));
  }

  function showRecord(m) {
    var r = m.record;
    page.base = r;
    page.conflict = null;
    $('record-title').textContent = r.name;
    $('rec-name').textContent = r.name;
    $('rec-id').textContent = r.recordId;
    $('rec-kind').textContent = r.kind;
    $('rec-location').textContent = r.location;
    $('rec-anchor').textContent = (r.anchorIds || []).join(', ');
    $('rec-description').value = r.description;
    $('rec-description').readOnly = !!m.readOnly;
    $('rec-save').disabled = !!m.readOnly;
    showRevision(r);
    updateCount();
    if (m.readOnly) setStatus('rec-status', m.storeStatus, 'warn');
    else if (r.source === 'local edit') setStatus('rec-status', 'Showing the text saved in this browser profile.', '');
    else setStatus('rec-status', 'Showing the original demo text (not edited in this browser profile yet).', '');
    if (page.panel !== 'record') openPanel('record');
    else $('rec-description').focus({ preventScroll: true });
  }

  function showRevision(r) {
    $('rec-revision').textContent = r.revision === 0
      ? 'original demo text (version 0)'
      : 'version ' + r.revision + ', saved ' + r.updatedAt.replace('T', ' ').replace('Z', ' UTC');
  }

  function updateCount() {
    var n = $('rec-description').value.length;
    $('rec-count').textContent = n + ' / 4000' + (isDirty() ? ' - unsaved changes' : '');
  }
  $('rec-description').addEventListener('input', updateCount);

  function save() {
    if (!page.base || page.saving || $('rec-save').disabled) return;
    page.saving = true;
    setTimeout(function () { page.saving = false; }, 3000);
    send('JsSaveRecord', JSON.stringify({
      recordId: page.base.recordId,
      description: $('rec-description').value,
      baseRevision: page.base.revision,
      requestId: nextRequestId()
    }));
  }
  $('rec-save').addEventListener('click', save);

  $('rec-copy').addEventListener('click', function () {
    var id = $('rec-id').textContent;
    var done = function () { setStatus('rec-status', 'Record ID copied: ' + id, ''); };
    try {
      navigator.clipboard.writeText(id).then(done, function () { setStatus('rec-status', 'Copy was blocked; select the ID text instead.', 'warn'); });
    } catch (e) {
      setStatus('rec-status', 'Copy is not available here; select the ID text instead.', 'warn');
    }
  });

  function onSaveResult(m) {
    page.saving = false;
    page.lastSave = { status: m.status, message: m.message, recordId: m.record && m.record.recordId, revision: m.record && m.record.revision };
    var r = m.record;
    if (!page.base || !r || r.recordId !== page.base.recordId) return;
    if (m.status === 'Saved') {
      page.base = r;
      showRevision(r);
      setStatus('rec-status', 'Saved in this browser profile at ' + timeNow() + ' (version ' + r.revision + ').', 'good');
      hint(r.name + ' saved (local demo data).', 'good');
    } else if (m.status === 'NoChange') {
      setStatus('rec-status', 'No changes to save.', '');
    } else if (m.status === 'Conflict') {
      page.conflict = r;
      setStatus('rec-status', m.message, 'bad');
    } else {
      setStatus('rec-status', m.message || ('Not saved: ' + m.status), 'bad');
    }
    updateCount();
  }

  function onSite(m) {
    page.site = m;
    page.records = m.records || [];
    $('site-name').textContent = m.siteName;
    if (page.panel === 'list') renderList();
    if (page.panel === 'data') renderData();
  }

  function renderList() {
    var list = $('list-items');
    list.textContent = '';
    page.records.forEach(function (r) {
      var item = el('li');
      if (r.recordId === page.selected) item.className = 'selected';
      var grow = el('span', 'grow');
      grow.appendChild(el('span', 'name', r.name));
      if (r.source === 'local edit') grow.appendChild(el('span', 'edited', '  edited (version ' + r.revision + ')'));
      grow.appendChild(el('span', 'loc', r.location));
      var show = el('button', 'small', 'Show');
      show.type = 'button';
      show.addEventListener('click', function () {
        closePanel();
        selectRecord(r.recordId, true, 'list');
      });
      var open = el('button', 'small', 'Open record');
      open.type = 'button';
      open.addEventListener('click', function () { openRecord(r.recordId, 'list'); });
      item.appendChild(grow);
      item.appendChild(show);
      item.appendChild(open);
      list.appendChild(item);
    });
  }

  function renderData() {
    var s = page.site || {};
    $('data-notice').textContent = s.notice || 'LOCAL DEMO DATA.';
    $('data-where').textContent = s.storageDescription || '';
    $('data-key').textContent = s.storageKey || '';
    $('data-state').textContent = (s.storeStatus || '') + (s.readOnly ? ' (read-only)' : '');
    $('data-build').textContent = s.build || '';
    $('data-session').textContent = session;
  }

  $('data-export').addEventListener('click', function () { command('export'); });
  $('data-reset').addEventListener('click', function () {
    $('data-reset-confirm').hidden = false;
    $('data-reset-no').focus({ preventScroll: true });
  });
  $('data-reset-no').addEventListener('click', function () { $('data-reset-confirm').hidden = true; });
  $('data-reset-yes').addEventListener('click', function () {
    $('data-reset-confirm').hidden = true;
    command('clearData');
    setStatus('data-status', 'Saved demo edits removed from this browser profile.', 'good');
    renderData();
  });

  function onExport(m) {
    page.lastExport = { fileName: m.fileName, json: m.json };
    try {
      var blob = new Blob([m.json], { type: 'application/json' });
      var link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = m.fileName;
      document.body.appendChild(link);
      link.click();
      setTimeout(function () {
        URL.revokeObjectURL(link.href);
        link.remove();
      }, 1000);
    } catch (e) {
      console.warn('[VRHE demo] download failed: ' + e);
    }
    postReport(m.fileName, m.json);
    var pre = $('data-json');
    pre.textContent = m.json;
    pre.hidden = false;
    setStatus('data-status', 'Downloaded ' + m.fileName + (reporting ? ' (a copy was also saved to the local results folder).' : '.'), 'good');
  }

  // ------------------------------------------------------------------ Unity messages
  function onUnityMessage(text) {
    var m;
    try {
      m = JSON.parse(text);
    } catch (e) {
      console.warn('[VRHE demo] unreadable message from Unity: ' + String(text).slice(0, 200));
      return;
    }
    page.messages++;
    if (m.requestId) replies[m.requestId] = m;
    switch (m.type) {
      case 'status':
        if (m.phase === 'hint') hint(m.text);
        else if (!ready) setLoading(m.text, 0.3 + 0.7 * (m.progress || 0));
        break;
      case 'error':
        if (!ready) fatal(m.text);
        else hint(m.text, 'bad');
        page.lastError = m.text;
        break;
      case 'site':
        onSite(m);
        break;
      case 'ready':
        ready = true;
        page.view = m.view;
        $('loading').hidden = true;
        hint('Ready. Click the view, then use W A S D or the arrow keys to move. Press H for help.');
        updateViewButton();
        pushUiState(true);
        break;
      case 'selection':
        page.selected = m.recordId;
        page.selectedName = m.name;
        $('btn-inspect').disabled = !m.recordId;
        if (!m.recordId) $('tag').hidden = true;
        if (m.recordId) hint(m.name + ' selected. Right-click it, press Enter or use "Open selected record".');
        if (page.panel === 'list') renderList();
        break;
      case 'hover':
        page.hovered = m.recordId;
        canvas.classList.toggle('hovering', !!m.recordId);
        break;
      case 'openRecord':
        if (isDirty())   // never replace unsaved text without asking
          confirmDiscard(function () { showRecord(m); });
        else
          showRecord(m);
        break;
      case 'saveResult':
        onSaveResult(m);
        if (m.status === 'Saved') page.records.forEach(function (r) {
          if (r.recordId === m.record.recordId) {
            r.revision = m.record.revision;
            r.source = m.record.source;
          }
        });
        break;
      case 'hud':
        page.hud = m;
        if (m.view !== page.view) {
          page.view = m.view;
          updateViewButton();
        }
        updateHud();
        break;
      case 'export':
        onExport(m);
        break;
      case 'report':
        postReport(m.fileName, m.json);
        break;
      default:
        break;   // state, projection and pacing are replies for the automated checks
    }
  }

  function updateViewButton() {
    $('btn-view').innerHTML = (page.view === 'first' ? 'Third person' : 'First person') + ' <kbd>V</kbd>';
  }

  function onTag(x, y, visible) {
    var tag = $('tag');
    if (!visible || !page.selected || page.panel) {
      tag.hidden = true;
      return;
    }
    var r = canvas.getBoundingClientRect();
    var s = stage.getBoundingClientRect();
    tag.style.left = (r.left - s.left + x * r.width / canvas.width) + 'px';
    tag.style.top = (r.top - s.top + (canvas.height - y) * r.height / canvas.height) + 'px';
    $('tag-name').textContent = page.selectedName;
    tag.hidden = false;
  }

  // ------------------------------------------------------------------ toolbar
  $('toolbar').addEventListener('click', function (e) {
    var button = e.target.closest('button[data-action]');
    if (!button) return;
    var action = button.dataset.action;
    if (action === 'help' || action === 'list' || action === 'data') togglePanel(action);
    else if (action === 'inspect') inspectSelected('button');
    else if (action === 'view') {
      command('toggleView');
      if (!page.panel) focusView();
    } else if (action === 'reset') {
      command('resetView');
      if (!page.panel) focusView();
    } else if (action === 'capture') toggleCapture();
    else if (action === 'size') {
      page.large = !page.large;
      layout();
      if (!page.panel) focusView();
    }
  });

  $('look-speed').value = String(page.lookSpeed);
  $('look-speed-value').textContent = page.lookSpeed.toFixed(2) + 'x';
  $('look-speed').addEventListener('input', function () {
    page.lookSpeed = clamp(Number($('look-speed').value) || 1, 0.25, 3);
    $('look-speed-value').textContent = page.lookSpeed.toFixed(2) + 'x';
    savePrefs();
    pushUiState(true);
  });

  // ------------------------------------------------------------------ lifecycle
  function setLoading(text, fraction) {
    $('loading-text').textContent = text;
    $('loading-bar').style.width = Math.round(clamp(fraction, 0, 1) * 100) + '%';
  }

  function fatal(message) {
    page.lastError = String(message);
    console.error('[VRHE demo] ' + message);
    var box = $('error');
    box.textContent = 'The demo stopped: ' + message + '\n\nClose this window and start the demo again with the launcher. If it keeps failing, collect the results file (see START-HERE).';
    box.hidden = false;
    $('loading').hidden = true;
  }

  function start() {
    layout();
    window.addEventListener('resize', layout);
    setLoading('Loading the Unity runtime...', 0);
    if (typeof createUnityInstance !== 'function') {
      fatal('The Unity loader did not start.');
      return;
    }
    var config = Object.assign({}, window.VRHEDemoUnityConfig, {
      showBanner: function (message, type) {
        console[type === 'error' ? 'error' : 'warn']('[unity-banner] ' + message);
        if (type === 'error') fatal(message);
      }
    });
    createUnityInstance(canvas, config, function (progress) {
      setLoading('Loading the Unity runtime... ' + Math.round(progress * 100) + '%', progress * 0.3);
    }).then(function (instance) {
      unity = instance;
      window.unityInstance = instance;
      console.log('[VRHE demo] Unity instance created; session ' + session);
      pushUiState(true);
    }).catch(function (message) {
      fatal('createUnityInstance failed: ' + message);
    });
  }

  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'hidden' && ready) command('report');
  });
  window.addEventListener('pagehide', function () {
    if (ready) command('report');
  });
  window.addEventListener('beforeunload', function (e) {
    if (isDirty()) {
      e.preventDefault();
      e.returnValue = '';
    }
  });

  // ------------------------------------------------------------------ automated checks
  // Read-only helpers for Tools/verify_interactive_demo.py. They report state; user-visible
  // behaviour is driven through real keyboard and mouse events.

  // Rendered, not just flagged: an element counts as shown only if it has a layout box.
  function shown(id) {
    var node = $(id);
    return !!node && node.getClientRects().length > 0 && getComputedStyle(node).visibility !== 'hidden';
  }

  // Which element, if any, would receive a click at the centre and near the corners of the 3D
  // view instead of the canvas (overlays that ignore the pointer do not count).
  function viewCovered() {
    var r = canvas.getBoundingClientRect();
    var points = [[0.5, 0.5], [0.1, 0.1], [0.9, 0.1], [0.1, 0.9], [0.9, 0.9]];
    for (var i = 0; i < points.length; i++) {
      var hit = document.elementFromPoint(r.left + r.width * points[i][0], r.top + r.height * points[i][1]);
      if (hit !== canvas) return hit ? (hit.id || hit.tagName) : 'nothing';
    }
    return '';
  }
  var test = {
    snapshot: function () {
      return {
        ready: ready, session: session, panel: page.panel, typing: page.typing, focused: page.focused,
        windowFocused: page.windowFocused, locked: page.locked, gate: gateOpen(), selected: page.selected,
        selectedName: page.selectedName, hovered: page.hovered, view: page.view, hud: page.hud,
        canvas: { width: canvas.width, height: canvas.height, cssWidth: canvas.clientWidth, cssHeight: canvas.clientHeight },
        record: page.base, dirty: isDirty(), editorText: $('rec-description').value,
        recordStatus: $('rec-status').textContent, discardVisible: shown('rec-discard'),
        lastSave: page.lastSave, lastExport: page.lastExport && page.lastExport.fileName,
        statusline: $('statusline').textContent, error: page.lastError, messages: page.messages,
        tagVisible: shown('tag'), crosshairVisible: shown('crosshair'),
        focusHintVisible: shown('focus-hint'), viewCovered: viewCovered(), activeElement: document.activeElement && (document.activeElement.id || document.activeElement.tagName),
        storageKey: page.site && page.site.storageKey, lookSpeed: page.lookSpeed
      };
    },
    unity: function (verb, arg) {
      var id = nextRequestId();
      send('JsTest', verb + ':' + (arg ? arg + ':' : '') + id);
      var reply = replies[id] || null;
      delete replies[id];
      return reply;
    },
    state: function () {
      var id = nextRequestId();
      send('JsTest', 'state:' + id);
      var reply = replies[id] || null;
      delete replies[id];
      return reply;
    },
    project: function (recordId) {
      var id = nextRequestId();
      send('JsTest', 'project:' + recordId + ':' + id);
      var m = replies[id];
      delete replies[id];
      if (!m) return null;
      var r = canvas.getBoundingClientRect();
      return {
        visible: m.visible, unityX: m.x, unityY: m.y,
        clientX: r.left + m.x * r.width / canvas.width,
        clientY: r.top + (canvas.height - m.y) * r.height / canvas.height
      };
    },
    pacingBegin: function (label) { send('JsTest', 'pacingBegin:' + label); },
    pacingEnd: function () {
      var id = nextRequestId();
      send('JsTest', 'pacingEnd:' + id);
      var m = replies[id];
      delete replies[id];
      return m ? m.window : null;
    },
    storedRaw: function () {
      try {
        return page.site ? window.localStorage.getItem(page.site.storageKey) : null;
      } catch (e) {
        return 'ERROR ' + e;
      }
    },
    lastExportJson: function () { return page.lastExport ? page.lastExport.json : null; }
  };

  window.VRHEDemoPage = {
    start: start,
    fatal: fatal,
    onUnityMessage: onUnityMessage,
    onTag: onTag,
    takeMouseFrame: takeMouseFrame,
    test: test
  };
})();
