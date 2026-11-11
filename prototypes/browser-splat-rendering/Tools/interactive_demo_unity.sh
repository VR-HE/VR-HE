#!/usr/bin/env bash
# VR-HE interactive browser demo: Unity batch commands for this prototype project only.
#
#   Tools/interactive_demo_unity.sh setup   create/refresh the demo scene and materials
#   Tools/interactive_demo_unity.sh test    run the demo's EditMode tests
#   Tools/interactive_demo_unity.sh build   build the WebGL demo into Builds/InteractiveDemo
#
# Every call passes this project's explicit path to Unity, so no other project (in particular
# not The Veil) and no running Editor is ever addressed. Unity must not already have this
# project open. Logs go to Logs/ (ignored); test results to TestResults/raw/ (ignored).
set -euo pipefail

PROJECT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNITY="${VRHE_UNITY:-$HOME/Unity/Hub/Editor/6000.3.15f1/Editor/Unity}"
STAMP="$(date +%Y%m%d-%H%M%S)"
mkdir -p "$PROJECT/Logs" "$PROJECT/TestResults/raw"

if [[ ! -f "$PROJECT/Assets/InteractiveDemo/Data/demo-site.json" || ! -d "$PROJECT/Assets/BrowserSplatTest" ]]; then
  echo "refusing: $PROJECT is not the VR-HE browser-splat-rendering prototype" >&2
  exit 2
fi
if [[ -f "$PROJECT/Temp/UnityLockfile" ]] && pgrep -f -- "-projectPath[= ]$PROJECT" >/dev/null 2>&1; then
  echo "refusing: a Unity Editor already has $PROJECT open; close it first" >&2
  exit 2
fi

# URP re-saves Assets/Settings/PC_RPAsset.asset whenever Unity exits, recording its one-time
# version migration (k_AssetPreviousVersion 12 -> 13). That shared benchmark asset is otherwise
# unchanged, so put back exactly that one-line change and leave any other edit alone.
restore_urp_bookkeeping() {
  local asset="Assets/Settings/PC_RPAsset.asset" diff
  diff="$(git -C "$PROJECT" diff --unified=0 -- "$asset" 2>/dev/null | command grep '^[+-] ' || true)"
  if [[ "$diff" == $'-  k_AssetPreviousVersion: 12\n+  k_AssetPreviousVersion: 13' ]]; then
    git -C "$PROJECT" checkout -- "$asset"
    echo "restored $asset (URP migration bookkeeping only)"
  elif [[ -n "$diff" ]]; then
    echo "note: $asset has other changes; left as is" >&2
  fi
}
trap restore_urp_bookkeeping EXIT

label() {
  local commit dirty=""
  commit="$(git -C "$PROJECT" rev-parse --short=12 HEAD 2>/dev/null || echo unknown)"
  if [[ -n "$(git -C "$PROJECT" status --porcelain -- . 2>/dev/null)" ]]; then dirty="-dirty"; fi
  echo "interactive-demo-${commit}${dirty}-$(date -u +%Y%m%dT%H%M%SZ)"
}

case "${1:-}" in
  setup)
    LOG="$PROJECT/Logs/interactive-demo-setup-$STAMP.log"
    "$UNITY" -batchmode -quit -nographics -projectPath "$PROJECT" -buildTarget WebGL \
      -executeMethod VRHE.InteractiveDemo.EditorTools.DemoProjectSetup.SetupBatch -logFile "$LOG"
    ;;
  test)
    LOG="$PROJECT/Logs/interactive-demo-tests-$STAMP.log"
    RESULTS="$PROJECT/TestResults/raw/interactive-demo-editmode-$STAMP.xml"
    set +e
    "$UNITY" -batchmode -nographics -projectPath "$PROJECT" -buildTarget WebGL -runTests -testPlatform EditMode \
      -assemblyNames VRHE.InteractiveDemo.Tests -testResults "$RESULTS" -logFile "$LOG"
    CODE=$?
    set -e
    echo "test results: $RESULTS (exit $CODE)"
    if [[ -f "$RESULTS" ]]; then
      python3 -I - "$RESULTS" <<'EOF'
import sys, xml.etree.ElementTree as ET
root = ET.parse(sys.argv[1]).getroot()
print("total={} passed={} failed={} skipped={}".format(root.get("total"), root.get("passed"), root.get("failed"), root.get("skipped")))
for case in root.iter("test-case"):
    if case.get("result") != "Passed":
        msg = case.find("./failure/message")
        print("  {}: {} {}".format(case.get("result"), case.get("fullname"), (msg.text or "").strip() if msg is not None else ""))
EOF
    fi
    exit $CODE
    ;;
  build)
    LOG="$PROJECT/Logs/interactive-demo-build-$STAMP.log"
    OUT="$PROJECT/Builds/InteractiveDemo"
    EXTRA=()
    if [[ "${2:-}" == "--recreate-scene" ]]; then EXTRA=(-vrheRecreateScene); fi
    "$UNITY" -batchmode -quit -projectPath "$PROJECT" -buildTarget WebGL \
      -executeMethod VRHE.InteractiveDemo.EditorTools.DemoProjectSetup.BuildBatch \
      -vrheBuildOutput "$OUT" -vrheBuildLabel "$(label)" "${EXTRA[@]}" -logFile "$LOG"
    echo "build output: $OUT"
    ;;
  *)
    echo "usage: $0 setup|test|build [--recreate-scene]" >&2
    exit 2
    ;;
esac
echo "log: $LOG"
