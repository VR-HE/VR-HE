// VR-HE interactive browser demo: page interface and Unity bridge (PROTOTYPE).
//
// Division of work
//   Page (this file): panels, help, the rack panel (rack note and its equipment list), the
//   equipment editor (name, RU range, descriptions), the description-names panel, the equipment
//   list, export download, mouse handling (click versus drag, right-click, wheel, pointer lock),
//   the input gate and local results reporting to the demo server on 127.0.0.1.
//   Unity (Assets/InteractiveDemo): 3D view, walking, camera, picking, highlights and the
//   provisional record store in this browser profile's localStorage. The store checks every
//   data rule (RU bounds, overlaps, description removal, name replacement); the page's live
//   hints and disabled buttons only make those rules visible.
//
// Bridge contract
//   Unity -> page: window.VRHEDemoPage.onUnityMessage(json) with a "type" field (see
//   DemoMessages.cs), onTag(x, y, visible) for the floating label, and takeMouseFrame(), which
//   Unity polls once per frame. Unity coordinates are canvas pixels with the origin at the
//   bottom-left; page coordinates are CSS pixels from the top-left.
//   Page -> Unity: unityInstance.SendMessage('VRHEDemo', method, text); see DemoApp.cs.
//   Equipment and name changes go through JsAuthoring (author() below), one command per change.
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
  var PANELS = ['record', 'equipment', 'names', 'list', 'help', 'data'];

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
    base: null,          // rack as opened or last saved: {recordId, revision, description, equipment, ...}
    conflict: null,
    saving: false,
    pendingConfirm: null,
    eqBase: null,        // equipment item as stored (EquipmentView)
    eqDraft: null,       // the equipment editor's working copy
    eqRack: null,        // that item's rack with its equipment summaries (for RU checks)
    catalog: null,       // description names: {active, labels: [...]}
    namesForm: null,     // open Rename/Remove form in the names panel: {labelId, kind}
    namesReturn: null,   // equipment item to return to when the names panel closes
    readOnly: false,
    lastAuthoring: null,
    errors: 0,
    lastGate: '',
    hud: null,
    lastSave: null,
    lastExport: null,
    lastError: '',
    messages: 0,
    lookSpeed: clamp(Number(loadPrefs().lookSpeed) || 1, 0.25, 3),
    invertMouseY: loadPrefs().invertMouseY === true
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
      window.localStorage.setItem(PREFS_KEY, JSON.stringify({ lookSpeed: page.lookSpeed, invertMouseY: page.invertMouseY }));
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
    if (node.tagName === 'TEXTAREA' || node.tagName === 'SELECT') return true;   // a list takes letter keys too
    return node.tagName === 'INPUT' && /^(text|search|email|number|password|url|tel)$/i.test(node.type || 'text');
  }

  // A panel's sticky footer (Save row, messages, questions) covers the bottom of its scrolling
  // area. Matching scroll-padding keeps controls that are focused or scrolled to above the footer,
  // including the browser's own scrolling when Tab moves focus.
  function fitFooter(foot) {
    var panel = foot && foot.closest('.panel');
    if (panel) panel.style.scrollPaddingBottom = (foot.offsetHeight + 6) + 'px';
  }
  if (window.ResizeObserver) {
    var footWatch = new ResizeObserver(function (entries) {
      entries.forEach(function (entry) { fitFooter(entry.target); });
    });
    Array.prototype.forEach.call(document.querySelectorAll('.panel-foot'), function (foot) { footWatch.observe(foot); });
  }

  // Scroll a control (or a card holding one) into view inside its panel, clear of the footer.
  function reveal(node) {
    if (!node || !node.scrollIntoView) return;
    var panel = node.closest && node.closest('.panel');
    fitFooter(panel && panel.querySelector('.panel-foot'));
    node.scrollIntoView({ block: 'nearest', inline: 'nearest' });
  }

  // Focus a field the page chose for the user and make sure it can be seen.
  function focusField(node) {
    if (!node) return;
    node.focus({ preventScroll: true });
    reveal(node);
  }

  // The text field or list most recently used in each panel, so "Keep editing" can go back to it.
  var lastField = {};
  document.addEventListener('focusin', function (e) {
    var panel = e.target && e.target.closest ? e.target.closest('.panel') : null;
    if (panel && isTextField(e.target)) lastField[panel.id] = e.target;
  });

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
    // Apply the preference once at the shared look-delta boundary: drag and pointer lock,
    // first-person pitch and third-person orbit all consume this frame. Absolute pointer/
    // picking coordinates, wheel zoom and keyboard height/reset inputs keep their meanings.
    var frame = [mouse.dx, page.invertMouseY ? -mouse.dy : mouse.dy, mouse.wheel, mouse.leftClicks, mouse.leftX, mouse.leftY,
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
      closeAll();
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
    if (page.panel) closeAll();
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
      if (confirmVisible()) {
        e.preventDefault();
        answer(false);               // = keep editing
      } else if (page.panel === 'names' && page.namesForm) {
        e.preventDefault();
        closeNamesForm();            // Esc closes the open Rename/Remove form first
      } else if (page.panel) {
        e.preventDefault();
        closePanel();
      }
      return;
    }
    if (key === 'Enter' && (e.ctrlKey || e.metaKey) && (page.panel === 'record' || page.panel === 'equipment')) {
      e.preventDefault();
      if (confirmVisible()) return;
      if (page.panel === 'record') save();
      else saveEquipment();
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
  // The rack and equipment panels ask before unsaved changes are dropped. The question appears
  // inside the panel that holds the changes; Esc or the second button keeps editing.
  var CONFIRMS = {
    record: { box: 'rec-discard', yes: 'rec-discard-yes', no: 'rec-discard-no', text: null },
    equipment: { box: 'eq-confirm', yes: 'eq-confirm-yes', no: 'eq-confirm-no', text: 'eq-confirm-text' }
  };

  function openPanel(name) {
    if (page.panel === name) return;
    if (isDirty()) {
      confirmDiscard(function () { openPanel(name); });
      return;
    }
    if (page.locked) document.exitPointerLock();
    var previous = page.panel;
    PANELS.forEach(function (p) { $('panel-' + p).hidden = p !== name; });
    if (name !== 'help') $('panel-' + name).scrollTop = 0;
    hideConfirms();
    $('data-reset-confirm').hidden = true;
    leavePanel(previous);
    page.panel = name;
    if (name === 'list') renderList();
    if (name === 'data') renderData();
    var first = name === 'record' ? $('rec-description')
      : name === 'equipment' ? firstDescriptionField()
      : name === 'names' ? $('names-new')
      : $('panel-' + name).querySelector('button');
    if (first) first.focus({ preventScroll: true });
    pushUiState();
  }

  // Forget an editor's state when its panel is left (after any unsaved-changes question).
  function leavePanel(previous) {
    if (previous === 'record') {
      page.base = null;
      page.conflict = null;
      resetAddForm();
    } else if (previous === 'equipment') {
      page.eqBase = page.eqDraft = page.eqRack = null;
    } else if (previous === 'names') {
      page.namesForm = null;
      page.namesReturn = null;
    }
  }

  function closePanel(force) {
    if (!page.panel) return;
    if (!force && isDirty()) {
      confirmDiscard(function () { closePanel(true); });
      return;
    }
    var previous = page.panel;
    var back = previous === 'names' ? page.namesReturn : null;
    $('panel-' + previous).hidden = true;
    hideConfirms();
    leavePanel(previous);
    page.panel = '';
    if (back) {          // names were managed from an equipment item: go back to it, as saved now
      openEquipment(back, 'names');
      if (page.panel) return;
    }
    focusView();
    pushUiState();
  }

  // Close whatever is open without returning to an earlier panel (clicks on the view, capture).
  function closeAll() {
    page.namesReturn = null;
    closePanel();
  }

  function togglePanel(name) {
    if (page.panel === name) closePanel();
    else openPanel(name);
  }

  stage.addEventListener('click', function (e) {
    if (e.target.closest('[data-close]')) closePanel();
  });

  function noteDirty() {
    return page.panel === 'record' && !!page.base && $('rec-description').value !== page.base.description;
  }

  function recordDirty() {
    return noteDirty() || (page.panel === 'record' && !!page.base && $('eq-new-name').value.trim() !== '');
  }

  function equipmentDirty() {
    return page.panel === 'equipment' && !!page.eqBase && draftDiffers(page.eqDraft, page.eqBase);
  }

  function isDirty() { return recordDirty() || equipmentDirty(); }

  function confirmDiscard(then) {
    ask(page.panel, 'You have unsaved changes.', 'Discard changes', function () {
      discardEdits();
      if (then) then();
    });
  }

  // A question inside the given panel; onYes runs on the first button.
  function ask(panel, text, yesLabel, onYes) {
    var c = CONFIRMS[panel];
    if (!c) {
      onYes();
      return;
    }
    page.pendingConfirm = onYes;
    if (c.text) $(c.text).textContent = text;
    $(c.yes).textContent = yesLabel;
    $(c.box).hidden = false;
    $(c.no).focus({ preventScroll: true });
    reveal($(c.box));
  }

  function confirmVisible() {
    var c = CONFIRMS[page.panel];
    return !!c && !$(c.box).hidden;
  }

  function answer(yes) {
    var c = CONFIRMS[page.panel];
    var then = page.pendingConfirm;
    page.pendingConfirm = null;
    if (c) $(c.box).hidden = true;
    if (yes) {
      if (then) then();
      return;
    }
    var last = lastField['panel-' + page.panel];
    var focus = last && last.isConnected && !last.disabled ? last
      : page.panel === 'record' ? $('rec-description') : page.panel === 'equipment' ? firstDescriptionField() : null;
    focusField(focus);
  }

  function hideConfirms() {
    Object.keys(CONFIRMS).forEach(function (k) { $(CONFIRMS[k].box).hidden = true; });
    page.pendingConfirm = null;
  }

  function discardEdits() {
    if (page.panel === 'record' && page.base) {
      $('rec-description').value = page.base.description;
      resetAddForm();
      updateCount();
    } else if (page.panel === 'equipment' && page.eqBase) {
      page.eqDraft = draftFrom(page.eqBase);
      renderEquipment();
    }
  }

  ['rec-discard-yes', 'eq-confirm-yes'].forEach(function (id) {
    $(id).addEventListener('click', function () { answer(true); });
  });
  ['rec-discard-no', 'eq-confirm-no'].forEach(function (id) {
    $(id).addEventListener('click', function () { answer(false); });
  });

  // ------------------------------------------------------------------ shared helpers for records
  function rules() {
    var a = (page.site && page.site.authoring) || {};
    return {
      ruNumbering: a.ruNumbering || 'bottom-up',
      ruOverlap: a.ruOverlap || 'warn',
      labelCollision: a.labelCollision || 'keep-both',
      maxDescriptionsPerItem: a.maxDescriptionsPerItem || 20,
      maxEquipmentNameLength: a.maxEquipmentNameLength || 80,
      maxLabelNameLength: a.maxLabelNameLength || 60
    };
  }

  function numberingText() {
    return rules().ruNumbering === 'top-down' ? 'RU 1 is the top position' : 'RU 1 is the bottom position';
  }

  // Same wording as DemoRecordStore.RangeText.
  function ruText(start, end) {
    return start === end ? 'RU ' + start : 'RU ' + start + '-' + end + ' (' + (end - start + 1) + 'U)';
  }

  function utcText(stamp) {
    return stamp ? stamp.replace('T', ' ').replace('Z', ' UTC') : '';
  }

  function plural(n, one, many) { return n + ' ' + (n === 1 ? one : many); }

  function actionButton(text, act, onClick, title, disabled, cls) {
    var b = el('button', 'small' + (cls ? ' ' + cls : ''), text);
    b.type = 'button';
    b.dataset.act = act;
    if (title) b.title = title;
    b.disabled = !!disabled;
    b.addEventListener('click', onClick);
    return b;
  }

  function option(value, text) {
    var o = document.createElement('option');
    o.value = value;
    o.textContent = text;
    return o;
  }

  function renderWarnings(id, warnings) {
    var list = $(id);
    list.textContent = '';
    (warnings || []).forEach(function (w) { list.appendChild(el('li', '', w)); });
  }

  function noReply(statusId) {
    setStatus(statusId, 'The 3D engine did not answer, so nothing was confirmed. Reload the page and check the item.', 'bad');
  }

  // Sends one authoring command to Unity. SendMessage runs synchronously, so the reply (or none,
  // if Unity failed) is available when it returns. Every rule is checked again in the store.
  function author(op, fields) {
    var id = nextRequestId();
    var request = Object.assign({ op: op, requestId: id }, fields || {});
    if (!send('JsAuthoring', JSON.stringify(request))) return null;
    var reply = replies[id] || null;
    delete replies[id];
    if (!reply) return null;
    page.lastAuthoring = { op: op, status: reply.status, message: reply.message, warnings: reply.warnings || [],
      labelId: reply.labelId, equipmentId: reply.equipmentId, affected: reply.affected };
    if (reply.catalog) page.catalog = reply.catalog;
    if (typeof reply.readOnly === 'boolean') page.readOnly = reply.readOnly;
    return reply;
  }

  function parseRange(startText, endText, sameIfBlank) {
    startText = String(startText).trim();
    endText = String(endText).trim();
    if (sameIfBlank && endText === '') endText = startText;
    var start = Number(startText);
    var end = Number(endText);
    return {
      start: start, end: end, blank: startText === '',
      ok: startText !== '' && endText !== '' && Number.isInteger(start) && Number.isInteger(end)
    };
  }

  // Live advice while typing rack units. It mirrors the store's rules (DemoRecordStore.CheckRange
  // and the overlap policy); the store checks again when saving.
  function rangeCheck(range, rack, exceptId) {
    var units = (rack && rack.rackUnits) || 42;
    var rackName = (rack && rack.name) || 'This rack';
    if (range.blank) return { tone: '', text: 'Enter the rack units it fills, 1 to ' + units + '. ' + numberingText() + '.' };
    if (!range.ok) return { tone: 'bad', text: 'Rack units are whole numbers from 1 to ' + units + '.' };
    if (range.start < 1 || range.end < 1 || range.start > units || range.end > units)
      return { tone: 'bad', text: rackName + ' has ' + units + ' rack units in this demo, so use 1 to ' + units + '.' };
    if (range.start > range.end)
      return { tone: 'bad', text: 'From RU ' + range.start + ' is above to RU ' + range.end + '. For a 2U item at RU 20 and 21, enter 20 to 21.' };
    var others = ((rack && rack.equipment) || []).filter(function (o) {
      return o.equipmentId !== exceptId && o.ruStart <= range.end && range.start <= o.ruEnd;
    });
    if (others.length) {
      var block = rules().ruOverlap === 'block';
      return {
        tone: block ? 'bad' : 'warn',
        text: 'Shares rack units with ' + others.map(function (o) { return o.name + ' (' + ruText(o.ruStart, o.ruEnd) + ')'; }).join(', ') +
          '. Two items can share units only when one is mounted at the front and one at the rear, which this demo does not record. ' +
          (block ? 'Saving is blocked until the ranges no longer overlap.' : 'You can still save; check the numbers.')
      };
    }
    return { tone: 'good', text: ruText(range.start, range.end) + ' is free in ' + rackName + '.' };
  }

  function showCheck(id, check) {
    var node = $(id);
    node.textContent = check.text;
    node.className = 'small ru-check' + (check.tone ? ' ' + check.tone : '');
  }

  // ------------------------------------------------------------------ racks
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
    page.readOnly = !!m.readOnly;
    $('record-title').textContent = r.name;
    $('rec-name').textContent = r.name;
    $('rec-id').textContent = r.recordId;
    $('rec-kind').textContent = r.kind;
    $('rec-location').textContent = r.location;
    $('rec-anchor').textContent = (r.anchorIds || []).join(', ');
    $('rec-units').textContent = r.rackUnits + ' RU (a demo assumption; ' + numberingText() + ')';
    $('rec-description').value = r.description;
    $('rec-description').readOnly = !!m.readOnly;
    $('rec-save').disabled = !!m.readOnly;
    showRevision(r);
    resetAddForm();
    renderRackEquipment(r);
    ['eq-new-name', 'eq-new-start', 'eq-new-end'].forEach(function (id) { $(id).readOnly = !!m.readOnly; });
    $('eq-add-btn').disabled = !!m.readOnly;
    updateCount();
    if (m.readOnly) setStatus('rec-status', m.storeStatus, 'warn');
    else if (r.source === 'local edit') setStatus('rec-status', 'Showing the rack note saved in this browser profile.', '');
    else setStatus('rec-status', 'Showing the original demo note (not edited in this browser profile yet).', '');
    if (page.panel !== 'record') openPanel('record');
    else focusField($('rec-description'));
  }

  function showRevision(r) {
    $('rec-revision').textContent = r.revision === 0
      ? 'original demo text (version 0)'
      : 'version ' + r.revision + ', saved ' + utcText(r.updatedAt);
  }

  function descriptionSummary(e) {
    return plural(e.descriptions, 'description', 'descriptions') + ', ' + e.named + ' named';
  }

  function renderRackEquipment(r) {
    var list = $('rec-equipment');
    list.textContent = '';
    var items = r.equipment || [];
    $('rec-eq-title').textContent = 'Equipment in this rack (' + items.length + ')';
    $('rec-eq-help').textContent = items.length
      ? 'Top of the rack first; ' + numberingText() + '. Open an item to edit its name, rack units and descriptions.'
      : 'None recorded yet. Add the first item below; ' + numberingText() + '.';
    items.forEach(function (e) {
      var li = el('li');
      li.dataset.equipment = e.equipmentId;
      var main = el('span', 'grow');
      main.appendChild(el('span', 'ru', ruText(e.ruStart, e.ruEnd)));
      main.appendChild(el('span', 'eq-name', e.name));
      main.appendChild(el('span', 'small meta', descriptionSummary(e)));
      if (e.overlaps) main.appendChild(el('span', 'overlap', e.overlaps));
      li.appendChild(main);
      li.appendChild(actionButton('Open', 'open-eq', function () { openEquipment(e.equipmentId, 'rack'); }, 'Open ' + e.name));
      list.appendChild(li);
    });
    ['eq-new-start', 'eq-new-end'].forEach(function (id) { $(id).max = String(r.rackUnits || 42); });
  }

  function updateCount() {
    var n = $('rec-description').value.length;
    $('rec-count').textContent = n + ' / 4000' + (noteDirty() ? ' - unsaved changes' : '');
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
      var equipment = page.base.equipment;
      page.base = r;
      if (!r.equipment) r.equipment = equipment;
      showRevision(r);
      renderRackEquipment(r);
      setStatus('rec-status', 'Rack note saved in this browser profile at ' + timeNow() + ' (version ' + r.revision + ').', 'good');
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

  // ------------------------------------------------------------------ adding equipment to a rack
  function resetAddForm() {
    $('eq-new-name').value = '';
    $('eq-new-start').value = '';
    $('eq-new-end').value = '';
    setStatus('eq-add-status', '', '');
    updateAddCheck();
  }

  function updateAddCheck() {
    var range = parseRange($('eq-new-start').value, $('eq-new-end').value, true);
    showCheck('eq-new-check', rangeCheck(range, page.base, ''));
    $('eq-new-size').textContent = range.ok && range.end >= range.start && range.start >= 1 ? (range.end - range.start + 1) + 'U' : '';
  }
  ['eq-new-start', 'eq-new-end'].forEach(function (id) { $(id).addEventListener('input', updateAddCheck); });
  $('eq-new-name').addEventListener('input', updateCount);

  function addEquipment() {
    if (!page.base || page.readOnly) return;
    var name = $('eq-new-name').value;
    var range = parseRange($('eq-new-start').value, $('eq-new-end').value, true);
    if (!name.trim()) {
      setStatus('eq-add-status', 'Type a name for the equipment first.', 'bad');
      focusField($('eq-new-name'));
      return;
    }
    if (!range.ok) {
      setStatus('eq-add-status', 'Enter the rack units it fills as whole numbers, for example 20 to 21.', 'bad');
      focusField($('eq-new-start'));
      return;
    }
    var reply = author('createEquipment', { recordId: page.base.recordId, name: name, ruStart: range.start, ruEnd: range.end });
    if (!reply) return noReply('eq-add-status');
    if (reply.rack && reply.rack.recordId === page.base.recordId) {
      page.base.equipment = reply.rack.equipment;
      renderRackEquipment(page.base);
    }
    if (reply.status !== 'Saved') {
      setStatus('eq-add-status', reply.message || ('Not added: ' + reply.status), 'bad');
      updateAddCheck();
      return;
    }
    var text = reply.message + (reply.warnings.length ? ' ' + reply.warnings.join(' ') : '');
    $('eq-new-name').value = '';
    $('eq-new-start').value = '';
    $('eq-new-end').value = '';
    updateAddCheck();
    updateCount();
    if (noteDirty()) {   // keep the unsaved rack note on screen; the new item is listed above
      setStatus('eq-add-status', text + ' Save or discard the rack note, then open the item from the list.', 'good');
      return;
    }
    showEquipment(reply, text, reply.warnings.length ? 'warn' : 'good');
  }
  $('eq-add-btn').addEventListener('click', addEquipment);
  ['eq-new-name', 'eq-new-start', 'eq-new-end'].forEach(function (id) {
    $(id).addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        addEquipment();
      }
    });
  });

  // ------------------------------------------------------------------ equipment editor
  // page.eqBase is the item as stored (EquipmentView); page.eqDraft is the editor's working copy:
  // {name, ruStart, ruEnd (as typed), descriptions: [{descriptionId ('' = new), labelId, text, key}]}.
  // Save sends the whole draft; the store keeps description IDs, checks every rule and writes once.
  var draftKeys = 0;

  function draftFrom(e) {
    return {
      name: e.name,
      ruStart: String(e.ruStart),
      ruEnd: String(e.ruEnd),
      descriptions: e.descriptions.map(function (d) {
        return { descriptionId: d.descriptionId, labelId: d.labelId, text: d.text, key: 'k' + (++draftKeys) };
      })
    };
  }

  function draftDiffers(draft, base) {
    if (!draft || !base) return false;
    if (draft.name !== base.name || draft.ruStart !== String(base.ruStart) || draft.ruEnd !== String(base.ruEnd)) return true;
    if (draft.descriptions.length !== base.descriptions.length) return true;
    return draft.descriptions.some(function (d, i) {
      var b = base.descriptions[i];
      return d.descriptionId !== b.descriptionId || d.labelId !== b.labelId || d.text !== b.text;
    });
  }

  function storedDescription(id) {
    var found = null;
    if (page.eqBase && id) page.eqBase.descriptions.forEach(function (d) { if (d.descriptionId === id) found = d; });
    return found;
  }

  function activeNames() {
    return ((page.catalog && page.catalog.labels) || []).filter(function (l) { return !l.retired; });
  }

  function findName(labelId) {
    var found = null;
    ((page.catalog && page.catalog.labels) || []).forEach(function (l) { if (l.labelId === labelId) found = l; });
    return found;
  }

  function firstDescriptionField() {
    return document.querySelector('#eq-descriptions textarea') || $('eq-name');
  }

  function openEquipment(equipmentId, how) {
    var go = function () {
      var reply = author('openEquipment', { equipmentId: equipmentId });
      if (!reply) {
        hint('The 3D engine did not answer; the equipment item was not opened.', 'bad');
        return;
      }
      if (reply.status !== 'Opened') {
        hint(reply.message || 'That equipment record could not be opened.', 'bad');
        return;
      }
      showEquipment(reply, reply.readOnly ? reply.storeStatus : '', reply.readOnly ? 'warn' : '');
    };
    if (isDirty()) confirmDiscard(go);
    else go();
  }

  function showEquipment(m, statusText, tone) {
    var switching = !page.eqBase || !m.equipment || page.eqBase.equipmentId !== m.equipment.equipmentId;
    page.eqBase = m.equipment;
    page.eqDraft = draftFrom(m.equipment);
    page.eqRack = m.rack && m.rack.recordId ? m.rack : null;
    renderEquipment();
    setStatus('eq-status', statusText || '', tone || '');
    renderWarnings('eq-warnings', []);
    if (page.panel !== 'equipment') openPanel('equipment');
    else {
      if (switching) $('panel-equipment').scrollTop = 0;
      focusField(firstDescriptionField());
    }
  }

  function renderEquipment() {
    var e = page.eqBase;
    var d = page.eqDraft;
    if (!e || !d) return;
    $('equipment-title').textContent = e.name;
    $('eq-rack-name').textContent = (page.eqRack && page.eqRack.name) || e.rackName;
    $('eq-id').textContent = e.equipmentId;
    $('eq-revision').textContent = 'version ' + e.revision + ', saved ' + utcText(e.updatedAt);
    $('eq-name').value = d.name;
    $('eq-name').maxLength = rules().maxEquipmentNameLength;
    $('eq-start').value = d.ruStart;
    $('eq-end').value = d.ruEnd;
    ['eq-start', 'eq-end'].forEach(function (id) { $(id).max = String(e.rackUnits || 42); });
    ['eq-name', 'eq-start', 'eq-end'].forEach(function (id) { $(id).readOnly = !!page.readOnly; });
    $('eq-save').disabled = !!page.readOnly;
    renderDescriptions();
    updateEquipmentCheck();
  }

  function updateEquipmentCheck() {
    var d = page.eqDraft;
    if (!d) return;
    var range = parseRange(d.ruStart, d.ruEnd, false);
    showCheck('eq-ru-check', rangeCheck(range, page.eqRack, page.eqBase.equipmentId));
    $('eq-size').textContent = range.ok && range.end >= range.start && range.start >= 1 ? (range.end - range.start + 1) + 'U' : '';
  }

  function markDirty() {
    $('eq-dirty').textContent = equipmentDirty() ? 'Unsaved changes' : '';
    var max = rules().maxDescriptionsPerItem;
    $('eq-add-desc').disabled = !!page.readOnly || (page.eqDraft && page.eqDraft.descriptions.length >= max);
    $('eq-add-desc').title = page.eqDraft && page.eqDraft.descriptions.length >= max
      ? 'This prototype allows at most ' + max + ' descriptions per item' : 'Add another description to this item only';
  }

  function fillNameOptions(select, desc) {
    select.textContent = '';
    select.appendChild(option('', '(no name)'));
    var active = activeNames();
    var known = active.some(function (l) { return l.labelId === desc.labelId; });
    if (desc.labelId && !known) {   // a reference kept as stored (retired or unknown name)
      var label = findName(desc.labelId);
      select.appendChild(option(desc.labelId, label
        ? label.name + ' (replaced' + (label.replacedByName ? ' by ' + label.replacedByName : '') + '; choose again)'
        : '(a name not in this list)'));
    }
    active.forEach(function (l) { select.appendChild(option(l.labelId, l.name)); });
    var line = option('__line', '\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500');
    line.disabled = true;
    select.appendChild(line);
    select.appendChild(option('__new', 'New name\u2026'));
    select.appendChild(option('__manage', 'Manage names\u2026'));
    select.value = desc.labelId || '';
  }

  function describeChange(desc) {
    if (!desc.descriptionId) return 'New, not saved yet.';
    var stored = storedDescription(desc.descriptionId);
    if (!stored) return '';
    if (stored.labelId !== desc.labelId || stored.text !== desc.text) return 'Changed, not saved yet.';
    return '';
  }

  function canRemove(desc) {
    return !desc.text.trim() && page.eqDraft.descriptions.length > 1 && !page.readOnly;
  }

  function removeTitle(desc) {
    if (page.eqDraft.descriptions.length < 2) return 'An item keeps at least one description';
    if (desc.text.trim()) return 'Only an empty description can be removed; text is never deleted here';
    return 'Remove this empty description';
  }

  function renderDescriptions(focusKey, focusWhat) {
    var list = $('eq-descriptions');
    list.textContent = '';
    var draft = page.eqDraft;
    draft.descriptions.forEach(function (desc, i) {
      var li = el('li', 'desc');
      li.dataset.key = desc.key;
      if (desc.descriptionId) li.dataset.description = desc.descriptionId;
      var head = el('div', 'desc-head');
      head.appendChild(el('span', 'desc-num', String(i + 1)));
      var select = el('select', 'desc-label');
      select.setAttribute('aria-label', 'Name of description ' + (i + 1));
      fillNameOptions(select, desc);
      select.disabled = !!page.readOnly;
      head.appendChild(select);
      head.appendChild(el('span', 'spacer'));
      head.appendChild(actionButton('\u2191', 'up', function () { moveDescription(desc.key, -1); }, 'Move up',
        i === 0 || page.readOnly));
      head.appendChild(actionButton('\u2193', 'down', function () { moveDescription(desc.key, 1); }, 'Move down',
        i === draft.descriptions.length - 1 || page.readOnly));
      var remove = actionButton('Remove', 'remove', function () { removeDescription(desc.key); }, removeTitle(desc), !canRemove(desc));
      head.appendChild(remove);
      li.appendChild(head);

      var form = el('div', 'desc-new');
      form.hidden = true;
      var input = el('input');
      input.type = 'text';
      input.maxLength = rules().maxLabelNameLength;
      input.placeholder = 'New name, for example: Firmware version';
      input.autocomplete = 'off';
      input.spellcheck = false;
      input.setAttribute('aria-label', 'New description name');
      form.appendChild(input);
      form.appendChild(actionButton('Add name', 'new-add', function () { addNameFromCard(desc, input); }));
      form.appendChild(actionButton('Cancel', 'new-cancel', function () {
        form.hidden = true;
        select.focus({ preventScroll: true });
      }));
      input.addEventListener('keydown', function (ev) {
        if (ev.key === 'Enter' && !ev.ctrlKey && !ev.metaKey) {
          ev.preventDefault();
          addNameFromCard(desc, input);
        }
      });
      li.appendChild(form);

      var text = el('textarea');
      text.rows = 3;
      text.maxLength = 4000;
      text.spellcheck = true;
      text.value = desc.text;
      text.readOnly = !!page.readOnly;
      text.setAttribute('aria-label', 'Text of description ' + (i + 1));
      li.appendChild(text);
      var meta = el('span', 'small desc-meta', describeChange(desc));
      li.appendChild(meta);

      select.addEventListener('change', function () {
        var value = select.value;
        if (value === '__new') {
          select.value = desc.labelId || '';
          form.hidden = false;
          input.focus({ preventScroll: true });
          return;
        }
        if (value === '__manage') {
          select.value = desc.labelId || '';
          manageNames();
          return;
        }
        if (value === '__line') {
          select.value = desc.labelId || '';
          return;
        }
        desc.labelId = value;
        meta.textContent = describeChange(desc);
        markDirty();
      });
      text.addEventListener('input', function () {
        desc.text = text.value;
        meta.textContent = describeChange(desc);
        remove.disabled = !canRemove(desc);
        remove.title = removeTitle(desc);
        markDirty();
      });
      list.appendChild(li);
    });
    markDirty();
    if (focusKey) {
      var card = list.querySelector('li[data-key="' + focusKey + '"]');
      var target = card && (focusWhat === 'select' ? card.querySelector('select')
        : focusWhat === 'up' || focusWhat === 'down' ? card.querySelector('button[data-act=' + focusWhat + ']')
        : card.querySelector('textarea'));
      if (target && target.disabled) target = card.querySelector('select');
      if (target) target.focus({ preventScroll: true });
      reveal(card);
    }
  }

  // Where focus is among the description cards, so a re-render (after Save) can put it back.
  function descriptionFocus() {
    var a = document.activeElement;
    var li = a && a.closest ? a.closest('#eq-descriptions > li') : null;
    if (!li) return null;
    var text = a.tagName === 'TEXTAREA';
    return {
      index: Array.prototype.indexOf.call(li.parentNode.children, li),
      selector: text ? 'textarea' : a.tagName === 'SELECT' ? 'select.desc-label'
        : a.dataset && a.dataset.act ? 'button[data-act=' + a.dataset.act + ']' : 'textarea',
      start: text ? a.selectionStart : null,
      end: text ? a.selectionEnd : null
    };
  }

  function restoreDescriptionFocus(at) {
    if (!at) return;
    var li = $('eq-descriptions').children[at.index];
    if (!li) return;
    var target = li.querySelector(at.selector);
    if (!target || target.disabled) target = li.querySelector('textarea');
    if (!target || target.disabled) target = li.querySelector('select');
    if (!target) return;
    target.focus({ preventScroll: true });
    if (at.start !== null && target.tagName === 'TEXTAREA')
      target.setSelectionRange(Math.min(at.start, target.value.length), Math.min(at.end, target.value.length));
  }

  function draftIndex(key) {
    var index = -1;
    page.eqDraft.descriptions.forEach(function (d, i) { if (d.key === key) index = i; });
    return index;
  }

  function moveDescription(key, delta) {
    var list = page.eqDraft.descriptions;
    var i = draftIndex(key);
    var j = i + delta;
    if (i < 0 || j < 0 || j >= list.length) return;
    var item = list.splice(i, 1)[0];
    list.splice(j, 0, item);
    renderDescriptions(key, delta < 0 ? 'up' : 'down');
  }

  function removeDescription(key) {
    var list = page.eqDraft.descriptions;
    var i = draftIndex(key);
    if (i < 0 || !canRemove(list[i])) return;   // the store refuses too
    list.splice(i, 1);
    renderDescriptions(list[Math.min(i, list.length - 1)].key, 'text');
    setStatus('eq-status', 'Empty description removed from the editor. Press Save to keep the change.', '');
  }

  function addDescription() {
    var list = page.eqDraft && page.eqDraft.descriptions;
    if (!list || page.readOnly) return;
    if (list.length >= rules().maxDescriptionsPerItem) {
      setStatus('eq-status', 'This prototype allows at most ' + rules().maxDescriptionsPerItem + ' descriptions per item.', 'bad');
      return;
    }
    var desc = { descriptionId: '', labelId: '', text: '', key: 'k' + (++draftKeys) };
    list.push(desc);
    renderDescriptions(desc.key, 'text');
    setStatus('eq-status', 'Description ' + list.length + ' added to this item only (not saved yet). Choose a name or leave it unnamed.', '');
  }
  $('eq-add-desc').addEventListener('click', addDescription);

  function addNameFromCard(desc, input) {
    if (!input.value.trim()) {
      setStatus('eq-status', 'Type the new name first.', 'bad');
      focusField(input);
      return;
    }
    var reply = author('createLabel', { name: input.value });
    if (!reply) return noReply('eq-status');
    if (reply.status === 'Saved' || reply.status === 'NoChange') {
      desc.labelId = reply.labelId;
      renderDescriptions(desc.key, 'select');
      var label = findName(reply.labelId);
      setStatus('eq-status', (reply.status === 'Saved'
        ? 'Added "' + (label ? label.name : '') + '" to the description names. '
        : reply.message + ' ') + 'It is chosen for this description only; press Save to keep it on this item.', 'good');
    } else {
      setStatus('eq-status', reply.message || ('Not added: ' + reply.status), 'bad');
    }
  }

  $('eq-name').addEventListener('input', function () {
    if (!page.eqDraft) return;
    page.eqDraft.name = $('eq-name').value;
    markDirty();
  });
  ['eq-start', 'eq-end'].forEach(function (id) {
    $(id).addEventListener('input', function () {
      if (!page.eqDraft) return;
      page.eqDraft.ruStart = $('eq-start').value;
      page.eqDraft.ruEnd = $('eq-end').value;
      updateEquipmentCheck();
      markDirty();
    });
  });

  // Returns true when the item is saved (or had nothing to save).
  function saveEquipment() {
    var e = page.eqBase;
    var d = page.eqDraft;
    if (!e || !d || page.readOnly) return false;
    var range = parseRange(d.ruStart, d.ruEnd, false);
    if (!d.name.trim()) {
      setStatus('eq-status', 'The equipment needs a name. Nothing was saved.', 'bad');
      focusField($('eq-name'));
      return false;
    }
    if (!range.ok) {
      setStatus('eq-status', 'Rack units are whole numbers, for example 20 to 21. Nothing was saved.', 'bad');
      focusField($('eq-start'));
      return false;
    }
    var reply = author('saveEquipment', {
      draft: {
        equipmentId: e.equipmentId, baseRevision: e.revision, name: d.name, ruStart: range.start, ruEnd: range.end,
        descriptions: d.descriptions.map(function (x) { return { descriptionId: x.descriptionId, labelId: x.labelId, text: x.text }; })
      }
    });
    if (!reply) {
      noReply('eq-status');
      return false;
    }
    if (reply.rack && reply.rack.recordId) page.eqRack = reply.rack;
    if (reply.status === 'Saved') {
      var at = descriptionFocus();   // typing can continue where it was after Ctrl+Enter
      page.eqBase = reply.equipment;
      page.eqDraft = draftFrom(reply.equipment);
      renderEquipment();
      restoreDescriptionFocus(at);
      setStatus('eq-status', reply.message + ' (' + timeNow() + ')', reply.warnings.length ? 'warn' : 'good');
      renderWarnings('eq-warnings', reply.warnings);
      hint(reply.equipment.name + ' saved (local demo data).', 'good');
      return true;
    }
    if (reply.status === 'NoChange') {
      setStatus('eq-status', 'No changes to save.', '');
      renderWarnings('eq-warnings', []);
      return true;
    }
    // Refused: keep everything typed; refresh the name lists (a name may have been replaced meanwhile).
    var keep = descriptionFocus();
    renderDescriptions();
    restoreDescriptionFocus(keep);
    updateEquipmentCheck();
    setStatus('eq-status', reply.message || ('Not saved: ' + reply.status), 'bad');
    renderWarnings('eq-warnings', reply.warnings);
    return false;
  }
  $('eq-save').addEventListener('click', saveEquipment);

  $('eq-back').addEventListener('click', function () {
    if (page.eqBase) openRecord(page.eqBase.rackRecordId, 'equipment');
  });

  function manageNames() {
    var e = page.eqBase;
    var go = function () { openNames(e ? e.equipmentId : null); };
    if (equipmentDirty())
      ask('equipment', 'Save your changes to this item before managing names?', 'Save and manage names', function () {
        if (saveEquipment()) go();
      });
    else go();
  }
  $('eq-manage').addEventListener('click', manageNames);

  // ------------------------------------------------------------------ description names
  // One shared list (D039). Rename fixes a spelling everywhere; Remove... always needs a
  // replacement and moves every description that used the old name to it (D041). The store
  // enforces both; the disabled button below is a convenience.
  function openNames(returnTo) {
    var reply = author('catalog', {});
    if (!reply) {
      hint('The 3D engine did not answer; the description names could not be shown.', 'bad');
      return;
    }
    page.namesForm = null;
    setStatus('names-status', reply.readOnly ? reply.storeStatus : '', reply.readOnly ? 'warn' : '');
    renderWarnings('names-warnings', []);
    if (page.panel !== 'names') openPanel('names');
    if (page.panel !== 'names') return;   // an unsaved-changes question is showing
    page.namesReturn = returnTo || null;
    $('names-back').hidden = !page.namesReturn;
    renderNames();
  }

  function usesText(l) {
    return l.uses ? 'used by ' + plural(l.uses, 'description', 'descriptions') + ' on ' + plural(l.items, 'item', 'items') : 'not used yet';
  }

  function collisionNote() {
    return rules().labelCollision === 'block'
      ? 'If an item already has a description with the replacement name, nothing changes and you are told which items to sort out first.'
      : 'If an item already has a description with the replacement name, both descriptions are kept, each with its own text.';
  }

  function renderNames() {
    var labels = (page.catalog && page.catalog.labels) || [];
    var list = $('names-list');
    list.textContent = '';
    labels.filter(function (l) { return !l.retired; }).forEach(function (l) {
      var li = el('li');
      li.dataset.label = l.labelId;
      var row = el('div', 'name-row');
      var main = el('span', 'grow');
      main.appendChild(el('span', 'name', l.name));
      main.appendChild(el('span', 'small uses', usesText(l)));
      if (l.previousNames) main.appendChild(el('span', 'small prev', 'earlier spelling: ' + l.previousNames));
      row.appendChild(main);
      row.appendChild(actionButton('Rename', 'rename', function () { openNameForm(l.labelId, 'rename'); },
        'Fix the spelling everywhere this name is used', page.readOnly));
      row.appendChild(actionButton('Remove\u2026', 'remove', function () { openNameForm(l.labelId, 'replace'); },
        'Remove this name by choosing the name that replaces it', page.readOnly));
      li.appendChild(row);
      if (page.namesForm && page.namesForm.labelId === l.labelId)
        li.appendChild(page.namesForm.kind === 'rename' ? renameForm(l) : replaceForm(l, labels));
      list.appendChild(li);
    });
    var retired = labels.filter(function (l) { return l.retired; });
    $('names-retired-count').textContent = String(retired.length);
    var old = $('names-retired');
    old.textContent = '';
    retired.forEach(function (l) {
      var li = el('li');
      li.dataset.label = l.labelId;
      li.appendChild(el('span', 'name', l.name));
      li.appendChild(el('span', 'small', ' replaced by ' + (l.replacedByName || 'another name') + ', ' + utcText(l.retiredAt) + '; ' +
        plural(l.reassigned, 'description', 'descriptions') + ' moved, text kept.'));
      old.appendChild(li);
    });
    $('names-add').disabled = !!page.readOnly;
    $('names-new').readOnly = !!page.readOnly;
    $('names-new').maxLength = rules().maxLabelNameLength;
  }

  function renameForm(l) {
    var form = el('div', 'name-form');
    form.dataset.form = 'rename';
    var input = el('input');
    input.type = 'text';
    input.id = 'names-rename-input';
    input.value = l.name;
    input.maxLength = rules().maxLabelNameLength;
    input.autocomplete = 'off';
    input.spellcheck = false;
    var label = el('label', '', 'Correct spelling of \u201c' + l.name + '\u201d');
    label.htmlFor = input.id;
    form.appendChild(label);
    form.appendChild(input);
    form.appendChild(el('p', 'small', (l.uses === 1 ? 'Changes the name on the one description that uses it. Its text does not change.'
      : l.uses ? 'Changes the name on all ' + l.uses + ' descriptions that use it, on ' + plural(l.items, 'item', 'items') +
        '. Their text does not change.' : 'No description uses it yet.') +
      ' To merge it into another existing name, use Remove\u2026 instead.'));
    var row = el('div', 'row');
    row.appendChild(actionButton('Rename everywhere', 'rename-go', function () { renameName(l, input.value); }, '', page.readOnly, 'primary'));
    row.appendChild(actionButton('Cancel', 'cancel', closeNamesForm));
    form.appendChild(row);
    input.addEventListener('keydown', function (ev) {
      if (ev.key === 'Enter' && !ev.ctrlKey && !ev.metaKey) {
        ev.preventDefault();
        renameName(l, input.value);
      }
    });
    return form;
  }

  function replaceForm(l, labels) {
    var form = el('div', 'name-form');
    form.dataset.form = 'replace';
    form.appendChild(el('p', '', 'Remove \u201c' + l.name + '\u201d by choosing the name that replaces it. ' + (l.uses === 1
      ? 'The one description that uses it gets the replacement name and keeps its text.'
      : l.uses ? 'Its ' + l.uses + ' descriptions on ' + plural(l.items, 'item', 'items') + ' get the replacement name and keep their text.'
      : 'No description uses it now.')));
    var existing = el('label', 'choice');
    var r1 = el('input');
    r1.type = 'radio';
    r1.name = 'names-rep-kind';
    r1.id = 'names-rep-kind-existing';
    r1.checked = true;
    existing.appendChild(r1);
    existing.appendChild(document.createTextNode('An existing name'));
    form.appendChild(existing);
    var select = el('select');
    select.id = 'names-rep-existing';
    select.setAttribute('aria-label', 'Existing replacement name');
    select.appendChild(option('', 'Choose a name\u2026'));
    labels.filter(function (x) { return !x.retired && x.labelId !== l.labelId; }).forEach(function (x) {
      select.appendChild(option(x.labelId, x.name));
    });
    form.appendChild(select);
    var fresh = el('label', 'choice');
    var r2 = el('input');
    r2.type = 'radio';
    r2.name = 'names-rep-kind';
    r2.id = 'names-rep-kind-new';
    fresh.appendChild(r2);
    fresh.appendChild(document.createTextNode('A new name'));
    form.appendChild(fresh);
    var input = el('input');
    input.type = 'text';
    input.id = 'names-rep-new';
    input.maxLength = rules().maxLabelNameLength;
    input.placeholder = 'New name';
    input.autocomplete = 'off';
    input.spellcheck = false;
    input.setAttribute('aria-label', 'New replacement name');
    form.appendChild(input);
    form.appendChild(el('p', 'small', collisionNote() + ' A name can\u2019t be removed without a replacement.'));
    var row = el('div', 'row');
    var go = actionButton('Replace and remove \u201c' + l.name + '\u201d', 'replace-go', function () {
      replaceName(l, r1.checked ? select.value : '', r2.checked ? input.value : '');
    }, 'Choose the replacement first', true, 'primary');
    row.appendChild(go);
    row.appendChild(actionButton('Cancel', 'cancel', closeNamesForm));
    form.appendChild(row);
    var refresh = function () {
      var chosen = r1.checked ? select.value : input.value.trim();
      go.disabled = !!page.readOnly || !chosen;
      go.title = chosen ? '' : 'Choose the replacement first';
    };
    select.addEventListener('change', function () { r1.checked = true; refresh(); });
    input.addEventListener('input', function () { r2.checked = true; refresh(); });
    r1.addEventListener('change', refresh);
    r2.addEventListener('change', refresh);
    input.addEventListener('keydown', function (ev) {
      if (ev.key === 'Enter' && !ev.ctrlKey && !ev.metaKey) {
        ev.preventDefault();
        if (!go.disabled) go.click();
      }
    });
    return form;
  }

  function openNameForm(labelId, kind) {
    page.namesForm = { labelId: labelId, kind: kind };
    renderNames();
    var target = kind === 'rename' ? $('names-rename-input') : $('names-rep-existing');
    if (target) {
      target.focus({ preventScroll: true });
      if (kind === 'rename') target.select();
      reveal(target.closest('.name-form') || target);
    }
  }

  function closeNamesForm() {
    var form = page.namesForm;
    page.namesForm = null;
    renderNames();
    var opener = form && document.querySelector('#names-list li[data-label="' + form.labelId + '"] button[data-act='
      + (form.kind === 'rename' ? 'rename' : 'remove') + ']');
    focusField(opener && !opener.disabled ? opener : $('names-new'));
  }

  function addName() {
    if (!$('names-new').value.trim()) {
      setStatus('names-status', 'Type the new name first.', 'bad');
      $('names-new').focus({ preventScroll: true });
      return;
    }
    var reply = author('createLabel', { name: $('names-new').value });
    if (!reply) return noReply('names-status');
    if (reply.status === 'Saved') $('names-new').value = '';
    renderWarnings('names-warnings', []);
    renderNames();
    setStatus('names-status', reply.message, reply.status === 'Saved' ? 'good' : reply.status === 'NoChange' ? '' : 'bad');
  }
  $('names-add').addEventListener('click', addName);
  $('names-new').addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.ctrlKey && !e.metaKey) {
      e.preventDefault();
      addName();
    }
  });

  function renameName(l, value) {
    var reply = author('renameLabel', { labelId: l.labelId, baseRevision: l.revision, name: value });
    if (!reply) return noReply('names-status');
    if (reply.status === 'Saved' || reply.status === 'NoChange') page.namesForm = null;
    renderWarnings('names-warnings', reply.warnings);
    renderNames();
    setStatus('names-status', reply.message, reply.status === 'Saved' ? 'good' : reply.status === 'NoChange' ? '' : 'bad');
    if (reply.status === 'Saved') hint('Name corrected everywhere (local demo data).', 'good');
  }

  function replaceName(l, replacementLabelId, replacementName) {
    var reply = author('replaceLabel', {
      labelId: l.labelId, baseRevision: l.revision,
      replacementLabelId: replacementLabelId || '', replacementName: replacementName || ''
    });
    if (!reply) return noReply('names-status');
    if (reply.status === 'Saved') page.namesForm = null;   // otherwise keep the form for another try
    renderWarnings('names-warnings', reply.warnings);
    renderNames();
    setStatus('names-status', reply.message, reply.status === 'Saved' ? (reply.warnings.length ? 'warn' : 'good') : 'bad');
    if (reply.status === 'Saved') hint('Name replaced; every description kept its text (local demo data).', 'good');
  }

  $('names-back').addEventListener('click', function () { closePanel(); });

  // ------------------------------------------------------------------ site, list and saved data
  function onSite(m) {
    page.site = m;
    page.records = m.records || [];
    if (typeof m.readOnly === 'boolean' && !page.panel) page.readOnly = m.readOnly;
    $('site-name').textContent = m.siteName;
    $('eq-new-name').maxLength = rules().maxEquipmentNameLength;
    if (page.selected) $('tag-hint').textContent = tagHint(page.selected);
    if (page.panel === 'list') renderList();
    if (page.panel === 'data') renderData();
  }

  function rackSummary(recordId) {
    var found = null;
    page.records.forEach(function (r) { if (r.recordId === recordId) found = r; });
    return found;
  }

  function tagHint(recordId) {
    var r = rackSummary(recordId);
    var n = r && r.equipment ? r.equipment.length : 0;
    return 'Right-click or Enter: open rack' + (n ? ' (' + plural(n, 'equipment item', 'equipment items') + ')' : '');
  }

  function renderList() {
    var list = $('list-items');
    list.textContent = '';
    page.records.forEach(function (r) {
      var item = el('li', 'rack' + (r.recordId === page.selected ? ' selected' : ''));
      item.dataset.record = r.recordId;
      var row = el('div', 'rack-row');
      var grow = el('span', 'grow');
      grow.appendChild(el('span', 'name', r.name));
      if (r.source === 'local edit') grow.appendChild(el('span', 'edited', '  note edited (version ' + r.revision + ')'));
      var equipment = r.equipment || [];
      grow.appendChild(el('span', 'loc', r.location + ' \u00b7 ' + (equipment.length ? plural(equipment.length, 'equipment item', 'equipment items') : 'no equipment recorded')));
      row.appendChild(grow);
      row.appendChild(actionButton('Show', 'show', function () {
        closeAll();
        selectRecord(r.recordId, true, 'list');
      }, 'Select ' + r.name + ' and turn the view toward it'));
      row.appendChild(actionButton('Open rack', 'open', function () { openRecord(r.recordId, 'list'); }, 'Open ' + r.name + "'s note and equipment"));
      item.appendChild(row);
      if (equipment.length) {
        var sub = el('ul', 'eq-sub');
        equipment.forEach(function (e) {
          var li = el('li');
          li.dataset.equipment = e.equipmentId;
          li.appendChild(el('span', 'ru', ruText(e.ruStart, e.ruEnd)));
          var name = el('span', 'eq-name grow', e.name);
          if (e.overlaps) {
            name.appendChild(el('span', 'overlap-mark', ' (shares units)'));
            name.title = e.overlaps;
          }
          li.appendChild(name);
          li.appendChild(actionButton('Open', 'open-eq', function () { openEquipment(e.equipmentId, 'list'); }, 'Open ' + e.name));
          sub.appendChild(li);
        });
        item.appendChild(sub);
      }
      list.appendChild(item);
    });
  }

  function migrationText(s) {
    var m = s.migration || {};
    if (!m.fromKey) return 'No data from the earlier demo version in this browser profile.';
    if (m.state === 'carried over')
      return 'Carried over ' + plural(m.carriedEntries, 'rack note', 'rack notes') + ' from the earlier demo version (' + m.fromKey +
        '). That copy is kept unchanged as a backup' + (s.persisted ? '.' : '; the new format is written at your first save.');
    if (m.state === 'reset')
      return 'Started over (reset). The earlier demo version\u2019s copy (' + m.fromKey + ') is kept unchanged and included in exports.';
    return 'Earlier demo data under ' + m.fromKey + ' could not be used (' + m.state + '); it is kept unchanged and included in exports.';
  }

  function renderData() {
    var s = page.site || {};
    $('data-notice').textContent = s.notice || 'LOCAL DEMO DATA.';
    $('data-where').textContent = s.storageDescription || '';
    $('data-key').textContent = s.storageKey || '';
    $('data-contents').textContent = plural(s.equipmentCount || 0, 'equipment record', 'equipment records') + ', ' +
      plural(s.activeNames || 0, 'description name', 'description names') + (s.persisted ? '' : ' (nothing saved in this profile yet)');
    $('data-migration').textContent = migrationText(s);
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
    var errors = page.errors;
    command('clearData');
    if (page.errors !== errors) setStatus('data-status', page.lastError, 'bad');
    else setStatus('data-status', 'Saved demo data removed from this browser profile; the original demo content is back.', 'good');
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
        page.errors++;
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
        else $('tag-hint').textContent = tagHint(m.recordId);
        if (m.recordId && m.how !== 'equipment')
          hint(m.name + ' selected. Right-click it, press Enter or use "Open selected record".');
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
      case 'authoring':
        break;   // read synchronously by author(), which sent the command
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
    else if (action === 'names') {
      if (page.panel === 'names') closePanel();
      else openNames(null);
    }
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

  $('invert-mouse-y').checked = page.invertMouseY;
  $('invert-mouse-y').addEventListener('change', function () {
    page.invertMouseY = $('invert-mouse-y').checked;
    mouse.dy = 0;   // discard motion queued before changing the preference
    savePrefs();
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
        equipment: page.eqBase, rack: page.eqRack, eqDirty: equipmentDirty(), eqStatus: $('eq-status').textContent,
        eqWarnings: Array.prototype.map.call($('eq-warnings').children, function (n) { return n.textContent; }),
        eqDirtyText: $('eq-dirty').textContent, eqRuCheck: $('eq-ru-check').textContent, addCheck: $('eq-new-check').textContent,
        addStatus: $('eq-add-status').textContent, confirmVisible: confirmVisible(),
        draft: page.eqDraft && {
          name: page.eqDraft.name, ruStart: page.eqDraft.ruStart, ruEnd: page.eqDraft.ruEnd,
          descriptions: page.eqDraft.descriptions.map(function (d) { return { descriptionId: d.descriptionId, labelId: d.labelId, text: d.text }; })
        },
        catalog: page.catalog, namesForm: page.namesForm, namesReturn: page.namesReturn,
        namesStatus: $('names-status').textContent,
        namesWarnings: Array.prototype.map.call($('names-warnings').children, function (n) { return n.textContent; }),
        lastAuthoring: page.lastAuthoring, records: page.records, readOnly: page.readOnly,
        tagHint: $('tag-hint').textContent,
        lastSave: page.lastSave, lastExport: page.lastExport && page.lastExport.fileName,
        statusline: $('statusline').textContent, error: page.lastError, messages: page.messages,
        tagVisible: shown('tag'), crosshairVisible: shown('crosshair'),
        focusHintVisible: shown('focus-hint'), viewCovered: viewCovered(), activeElement: document.activeElement && (document.activeElement.id || document.activeElement.tagName),
        storageKey: page.site && page.site.storageKey, lookSpeed: page.lookSpeed, invertMouseY: page.invertMouseY
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
    storedKey: function (key) {
      try {
        return window.localStorage.getItem(key);
      } catch (e) {
        return 'ERROR ' + e;
      }
    },
    // A reply Unity sent for a request the check made itself with unityInstance.SendMessage
    // (for example a command the interface would never send). Returns it once.
    takeReply: function (requestId) {
      var m = replies[requestId] || null;
      delete replies[requestId];
      return m;
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
